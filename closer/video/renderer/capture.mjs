// closer/video/renderer/capture.mjs
// Headless Playwright Multi-Worker Frame Capture to FFmpeg Pipe
// Renders 1080x1920 9:16 Canvas 2D Stage at 30 fps directly to H.264 video.

import fs from 'fs';
import path from 'path';
import http from 'http';
import { spawn, execFileSync } from 'child_process';
import { chromium } from 'playwright-core';

// ─────────────────────────────────────────────────────────────────────────────
// 1. CLI ARGUMENT PARSER
// ─────────────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const opt = (k, d) => {
  const i = args.indexOf(k);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : d;
};

const webDir = path.resolve(args[0] || path.join(path.dirname(new URL(import.meta.url).pathname), 'web'));
const outPath = path.resolve(opt('--out', path.join(webDir, '../out/video_raw.mp4')));
const FPS = parseInt(opt('--fps', '30'), 10);
const WK = parseInt(opt('--workers', '4'), 10);
const Q = opt('--q', 'sector=clinics');
const explicitDur = parseFloat(opt('--duration', '0'));

if (!fs.existsSync(path.join(webDir, 'index.html'))) {
  console.error(`[Error] No index.html found in web directory: ${webDir}`);
  process.exit(2);
}

fs.mkdirSync(path.dirname(outPath), { recursive: true });

// ─────────────────────────────────────────────────────────────────────────────
// 2. EMBEDDED LIGHTWEIGHT STATIC HTTP SERVER
// ─────────────────────────────────────────────────────────────────────────────
const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.mjs': 'application/javascript',
  '.json': 'application/json',
  '.css': 'text/css',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2'
};

function startServer(dir) {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const parsed = new URL(req.url, 'http://127.0.0.1');
      let p = path.join(dir, decodeURIComponent(parsed.pathname));
      if (fs.existsSync(p) && fs.statSync(p).isDirectory()) {
        p = path.join(p, 'index.html');
      }

      if (!fs.existsSync(p)) {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
        return;
      }

      const ext = path.extname(p).toLowerCase();
      const mime = MIME_TYPES[ext] || 'application/octet-stream';
      res.writeHead(200, {
        'Content-Type': mime,
        'Access-Control-Allow-Origin': '*'
      });
      fs.createReadStream(p).pipe(res);
    });

    srv.listen(0, '127.0.0.1', () => {
      resolve({ srv, port: srv.address().port });
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. MAIN MULTI-WORKER CAPTURE ORCHESTRATOR
// ─────────────────────────────────────────────────────────────────────────────
async function main() {
  const t0 = Date.now();
  console.log(`[Capture] Starting video render: ${webDir}`);
  console.log(`[Capture] Config: 1080x1920 @ ${FPS} fps, ${WK} workers, query: "${Q}"`);

  const { srv, port } = await startServer(webDir);
  const baseURL = `http://127.0.0.1:${port}/index.html?${Q}`;

  const tempDir = fs.mkdtempSync(path.join(path.dirname(outPath), '.capture_segs_'));
  const procs = new Set();

  const cleanup = () => {
    for (const p of procs) {
      try { p.kill('SIGKILL'); } catch {}
    }
    try { fs.rmSync(tempDir, { recursive: true, force: true }); } catch {}
    srv.close();
  };

  process.on('SIGINT', () => { cleanup(); process.exit(130); });
  process.on('SIGTERM', () => { cleanup(); process.exit(143); });

  try {
    // 1. Probe duration from page
    const probeBrowser = await chromium.launch({
      args: ['--enable-gpu', '--font-render-hinting=none', '--force-color-profile=srgb', '--no-sandbox']
    });
    const probePage = await probeBrowser.newPage({ viewport: { width: 1080, height: 1920 } });
    await probePage.goto(baseURL);
    await probePage.waitForFunction(() => window.READY === true, null, { timeout: 30000 });
    const probeDUR = await probePage.evaluate(() => window.DUR || 0);
    await probeBrowser.close();

    const DUR = explicitDur > 0 ? explicitDur : probeDUR;
    if (!(DUR > 0)) {
      throw new Error(`Invalid duration probed: ${DUR}s. Ensure window.DUR is set in index.html.`);
    }

    const TOTAL_FRAMES = Math.round(DUR * FPS);
    const perWorker = Math.ceil(TOTAL_FRAMES / WK);
    console.log(`[Capture] Target Duration: ${DUR.toFixed(2)}s (${TOTAL_FRAMES} frames total, ~${perWorker} frames/worker)`);

    // 2. Launch workers in parallel
    await Promise.all([...Array(WK)].map(async (_, w) => {
      const a = w * perWorker;
      const b = Math.min(TOTAL_FRAMES, a + perWorker);
      if (a >= b) return;

      const segOut = path.join(tempDir, `seg_${w}.mp4`);
      const browser = await chromium.launch({
        args: ['--enable-gpu', '--font-render-hinting=none', '--force-color-profile=srgb', '--no-sandbox']
      });
      const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
      await page.goto(baseURL);
      await page.waitForFunction(() => window.READY === true, null, { timeout: 30000 });

      // Spawn FFmpeg pipe for this segment
      const ff = spawn('ffmpeg', [
        '-y', '-loglevel', 'error',
        '-f', 'image2pipe',
        '-framerate', String(FPS),
        '-c:v', 'mjpeg',
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '16',
        '-pix_fmt', 'yuv420p',
        segOut
      ], { stdio: ['pipe', 'inherit', 'inherit'] });

      procs.add(ff);
      let closed = new Promise(r => ff.on('close', r));

      for (let f = a; f < b; f++) {
        const timeSec = f / FPS;
        await page.evaluate(t => window.render(t), timeSec);
        const buf = await page.screenshot({ type: 'jpeg', quality: 95 });

        if (!ff.stdin.write(buf)) {
          await new Promise(r => ff.stdin.once('drain', r));
        }

        if ((f - a) % 90 === 0 || f === b - 1) {
          const pct = (((f - a + 1) / (b - a)) * 100).toFixed(0);
          console.log(`  [Worker ${w}] Frame ${f - a + 1}/${b - a} (${pct}%) @ t=${timeSec.toFixed(2)}s`);
        }
      }

      ff.stdin.end();
      await closed;
      procs.delete(ff);
      await browser.close();
    }));

    // 3. Concat segments into final output
    const segFiles = [...Array(WK)]
      .map((_, w) => path.join(tempDir, `seg_${w}.mp4`))
      .filter(f => fs.existsSync(f));

    if (segFiles.length === 1) {
      fs.copyFileSync(segFiles[0], outPath);
    } else {
      const concatList = path.join(tempDir, 'concat.txt');
      fs.writeFileSync(concatList, segFiles.map(f => `file '${f}'`).join('\n'));
      execFileSync('ffmpeg', [
        '-y', '-loglevel', 'error',
        '-f', 'concat', '-safe', '0',
        '-i', concatList,
        '-c', 'copy',
        outPath
      ]);
    }

    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
    const effFps = (TOTAL_FRAMES / elapsed).toFixed(1);
    console.log(`[Capture] Complete! Saved to ${outPath}`);
    console.log(`[Capture] Rendered ${TOTAL_FRAMES} frames in ${elapsed}s (Effective speed: ${effFps} fps)`);

  } finally {
    cleanup();
  }
}

main().catch(err => {
  console.error('[Capture] Fatal Error:', err);
  process.exit(1);
});
