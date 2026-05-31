#!/usr/bin/env python3
# Mulberry · Koda Coding Team · 2026-05-31
# 고객 요청: 레스토랑 예약 웹사이트 만들어줘
# 배포 타겟: railway

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Mulberry App", description="jangseungbaegi")

@app.get("/", response_class=HTMLResponse)
def home():
    """메인 페이지 — Mulberry DNA 기반"""
    return """
    <html>
    <head><title>Mulberry</title></head>
    <body style="font-family:sans-serif;text-align:center;padding:50px;background:#0d0d14;color:#e8e6f0">
        <h1>🌿 Mulberry</h1>
        <p>jangseungbaegi 정신 — AI serves humans</p>
        <p style="color:#7F77DD">요청: 레스토랑 예약 웹사이트 만들어줘</p>
    </body>
    </html>
    """

@app.get("/health")
def health():
    return {"status": "ok", "brand": "Mulberry", "spirit": "jangseungbaegi"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
