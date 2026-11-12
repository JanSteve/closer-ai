"""
closer.video.exporter
~~~~~~~~~~~~~~~~~~~~~
Multi-Format FFmpeg Exporter for CLOSER AI Video Pipeline.
Generates broadcast-quality Master Instagram Reels (1080x1920 MP4 with AAC 48kHz and
-14.0 LUFS EBU R128 loudness normalization), 720p mobile previews, 1:1 square feed clips,
320kbps MP3 audio masters, 1080x1920 JPG poster frames, and SRT/WebVTT subtitles.
"""

import os
import subprocess
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("closer.video.exporter")

def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp: HH:MM:SS,mmm"""
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def format_timestamp_vtt(seconds: float) -> str:
    """Format seconds into WebVTT timestamp: HH:MM:SS.mmm"""
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


class MultiFormatExporter:
    """Production-grade FFmpeg exporter for multi-format video/audio delivery."""

    def __init__(self, ffmpeg_bin: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_bin

    def _run_cmd(self, cmd: List[str], desc: str) -> None:
        logger.info(f"[Exporter] Running {desc}...")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"[Exporter] Command failed for {desc}:\n{res.stderr}")
            raise RuntimeError(f"FFmpeg command failed ({desc}): {res.stderr[-300:]}")

    def export_master_reel(
        self,
        video_raw_path: str,
        audio_mix_path: str,
        output_path: str,
        target_lufs: float = -14.0,
        true_peak: float = -1.2,
    ) -> str:
        """
        Muxes master 1080x1920 Instagram Reel with H.264 High Profile, AAC 48kHz audio,
        EBU R128 -14.0 LUFS loudness mastering, and +faststart flag.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        loudnorm_filter = f"loudnorm=I={target_lufs}:TP={true_peak}:LRA=11:print_format=none"

        cmd = [
            self.ffmpeg, "-y",
            "-i", video_raw_path,
            "-i", audio_mix_path,
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level:v", "4.2",
            "-preset", "medium",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            "-af", loudnorm_filter,
            "-movflags", "+faststart",
            "-shortest",
            output_path
        ]
        self._run_cmd(cmd, "Master Instagram Reel (1080x1920 MP4)")
        return output_path

    def export_mobile_preview(
        self,
        master_reel_path: str,
        output_path: str
    ) -> str:
        """Scales master video down to 720x1280 mobile preview for fast previewing & web viewing."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cmd = [
            self.ffmpeg, "-y",
            "-i", master_reel_path,
            "-vf", "scale=720:1280:flags=lanczos",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]
        self._run_cmd(cmd, "Mobile Preview (720x1280 MP4)")
        return output_path

    def export_square_feed(
        self,
        master_reel_path: str,
        output_path: str
    ) -> str:
        """
        Crops center action zone (Y: 420 to 1500) into 1080x1080 square for Instagram/Facebook feed grid.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cmd = [
            self.ffmpeg, "-y",
            "-i", master_reel_path,
            "-vf", "crop=1080:1080:0:420",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            "-movflags", "+faststart",
            output_path
        ]
        self._run_cmd(cmd, "Square Feed Variant (1080x1080 MP4)")
        return output_path

    def export_audio_master(
        self,
        audio_mix_path: str,
        output_path: str
    ) -> str:
        """Encodes standalone 320kbps MP3 audio mix for podcast audiograms and sound archiving."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cmd = [
            self.ffmpeg, "-y",
            "-i", audio_mix_path,
            "-c:a", "libmp3lame",
            "-b:a", "320k",
            "-ar", "48000",
            output_path
        ]
        self._run_cmd(cmd, "Standalone Audio Mix (320kbps MP3)")
        return output_path

    def export_poster_frame(
        self,
        master_reel_path: str,
        output_path: str,
        timestamp_sec: float = 2.0
    ) -> str:
        """Extracts high-resolution 1080x1920 JPEG poster cover image at hook timestamp."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cmd = [
            self.ffmpeg, "-y",
            "-ss", str(timestamp_sec),
            "-i", master_reel_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ]
        self._run_cmd(cmd, f"Poster Frame (1080x1920 JPG @ {timestamp_sec}s)")
        return output_path

    def export_subtitles_srt(
        self,
        subtitles_data: List[dict],
        output_path: str
    ) -> str:
        """Generates standard SubRip (.srt) subtitle file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        lines = []
        for idx, item in enumerate(subtitles_data, 1):
            t0 = format_timestamp_srt(item["t0"])
            t1 = format_timestamp_srt(item["t1"])
            text = item.get("text", "").strip()
            lines.append(f"{idx}\n{t0} --> {t1}\n{text}\n")
        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def export_subtitles_vtt(
        self,
        subtitles_data: List[dict],
        output_path: str
    ) -> str:
        """Generates standard WebVTT (.vtt) subtitle file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        lines = ["WEBVTT\n"]
        for idx, item in enumerate(subtitles_data, 1):
            t0 = format_timestamp_vtt(item["t0"])
            t1 = format_timestamp_vtt(item["t1"])
            text = item.get("text", "").strip()
            lines.append(f"{idx}\n{t0} --> {t1}\n{text}\n")
        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def export_all_formats(
        self,
        video_raw_path: str,
        audio_mix_path: str,
        subtitles_data: List[dict],
        output_dir: str,
        base_name: str
    ) -> Dict[str, str]:
        """
        Executes full multi-format export pipeline and returns paths dictionary.
        """
        os.makedirs(output_dir, exist_ok=True)

        master_path = os.path.join(output_dir, f"{base_name}_master.mp4")
        preview_path = os.path.join(output_dir, f"{base_name}_preview_720p.mp4")
        square_path = os.path.join(output_dir, f"{base_name}_square_1080p.mp4")
        audio_path = os.path.join(output_dir, f"{base_name}_audio.mp3")
        poster_path = os.path.join(output_dir, f"{base_name}_poster.jpg")
        srt_path = os.path.join(output_dir, f"{base_name}.srt")
        vtt_path = os.path.join(output_dir, f"{base_name}.vtt")

        self.export_master_reel(video_raw_path, audio_mix_path, master_path)
        self.export_mobile_preview(master_path, preview_path)
        self.export_square_feed(master_path, square_path)
        self.export_audio_master(audio_mix_path, audio_path)
        self.export_poster_frame(master_path, poster_path, timestamp_sec=2.0)
        self.export_subtitles_srt(subtitles_data, srt_path)
        self.export_subtitles_vtt(subtitles_data, vtt_path)

        return {
            "master_1080p": master_path,
            "preview_720p": preview_path,
            "square_1080p": square_path,
            "audio_mp3": audio_path,
            "poster_jpg": poster_path,
            "subtitles_srt": srt_path,
            "subtitles_vtt": vtt_path
        }
