"""
CLOSER AI — Vercel Serverless Application Entrypoint.
Provides a FastAPI application when FastAPI is available, or ASGI fallback.
Serves the full-bleed video landing page, static assets, and telephony routes.
"""

import base64
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

try:
    from fastapi import FastAPI, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

    app = FastAPI(
        title="CLOSER AI",
        description="Intelligence Designed To Evolve — Autonomous Conversational Voice Engine",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    @app.get("/landing", response_class=HTMLResponse)
    @app.get("/landing.html", response_class=HTMLResponse)
    @app.get("/index.html", response_class=HTMLResponse)
    async def serve_landing():
        index_file = ROOT_DIR / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(encoding="utf-8"), status_code=200)
        return HTMLResponse(content="<h1>CLOSER AI: Intelligence Designed To Evolve</h1>", status_code=200)

    @app.get("/console", response_class=HTMLResponse)
    @app.get("/dashboard", response_class=HTMLResponse)
    @app.get("/admin", response_class=HTMLResponse)
    async def serve_console():
        try:
            from src.closer.web.dashboard import HTML_TEMPLATE
            return HTMLResponse(content=HTML_TEMPLATE, status_code=200)
        except Exception:
            return HTMLResponse(content="<h1>CLOSER AI Executive Console</h1>", status_code=200)

    @app.get("/styles.css")
    async def serve_css():
        css_file = ROOT_DIR / "styles.css"
        if css_file.exists():
            return Response(content=css_file.read_bytes(), media_type="text/css; charset=utf-8")
        return Response(status_code=404)

    @app.get("/main.js")
    async def serve_js():
        js_file = ROOT_DIR / "main.js"
        if js_file.exists():
            return Response(content=js_file.read_bytes(), media_type="application/javascript; charset=utf-8")
        return Response(status_code=404)

    @app.get("/assets/{filename}")
    async def serve_asset(filename: str):
        file_path = ROOT_DIR / "assets" / filename
        if file_path.exists() and file_path.is_file():
            media_type = "image/webp" if filename.endswith(".webp") else "application/octet-stream"
            return FileResponse(file_path, media_type=media_type)
        return Response(status_code=404)

    @app.get("/fonts/{filename}")
    async def serve_font(filename: str):
        file_path = ROOT_DIR / "fonts" / filename
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path, media_type="font/woff2")
        return Response(status_code=404)

    @app.get("/api/leads")
    async def get_leads():
        try:
            from src.closer.web.dashboard import MOCK_LEADS
            return JSONResponse(content=MOCK_LEADS)
        except Exception:
            return JSONResponse(content=[])

except ImportError:
    # Minimal ASGI fallback if FastAPI is not installed locally
    async def app(scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "/")
            if path in ("/", "/landing", "/index.html"):
                index_path = ROOT_DIR / "index.html"
                content = index_path.read_bytes() if index_path.exists() else b"CLOSER AI"
                content_type = b"text/html; charset=utf-8"
            elif path.endswith(".css"):
                file_path = ROOT_DIR / path.lstrip("/")
                content = file_path.read_bytes() if file_path.exists() else b""
                content_type = b"text/css; charset=utf-8"
            elif path.endswith(".js"):
                file_path = ROOT_DIR / path.lstrip("/")
                content = file_path.read_bytes() if file_path.exists() else b""
                content_type = b"application/javascript; charset=utf-8"
            else:
                content = b"Not Found"
                content_type = b"text/plain"

            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", content_type],
                    [b"content-length", str(len(content)).encode()],
                ],
            })
            await send({
                "type": "http.response.body",
                "body": content,
            })
