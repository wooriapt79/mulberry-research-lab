#!/usr/bin/env python3
"""
malu_processor.py — Malu Agent Brain (Gemini-powered)
GitHub Actions 트리거: 이슈 코멘트에 @Malu-Agent 언급 시 자동 실행
환경변수: GEMINI_API_KEY (secrets.MALU_BOT_ACCESS_TOKEN), MALU_TOKEN (secrets.MALU_TOKEN)
"""


import json
import os
import urllib.request
import urllib.error




def get_gemini_response(api_key: str, prompt: str) -> str:
    """Gemini API 호출 — 응답 텍스트 반환."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as exc:
        return f"Malu 두뇌 일시 오류: {exc}"




def post_github_comment(token: str, repo: str, issue_number: int, body: str) -> bool:
    """GitHub 이슈에 댓글 등록."""
