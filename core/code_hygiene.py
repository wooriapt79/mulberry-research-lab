# -*- coding: utf-8 -*-
"""
Code hygiene checks for STEP 4 (Kbin auto-review).

Checks a Python source file for:
    - UTF-8 encoding declaration
    - Korean text inside comments
    - Indentation consistency (tabs vs spaces)
"""

from __future__ import annotations

import re
import tokenize
from pathlib import Path
from typing import Any, Dict

KOREAN_TEXT_RE = re.compile(r"[가-힣]")
ENCODING_DECLARATION_RE = re.compile(r"coding[:=]\s*([-\w.]+)")


def check_utf8_declaration(source: str) -> bool:
    """Return True if one of the first two lines declares a UTF-8 encoding."""
    for line in source.splitlines()[:2]:
        match = ENCODING_DECLARATION_RE.search(line)
        if match and match.group(1).lower().replace("-", "") == "utf8":
            return True
    return False


def find_korean_comments(source: str) -> list[dict]:
    """Return [{"line": n, "text": "..."}] for every `#` comment token containing Korean text.

    Uses tokenize so Korean text inside string literals (e.g. agent prompt
    data) is not mistaken for a comment.
    """
    findings = []
    try:
        tokens = tokenize.generate_tokens(iter(source.splitlines(keepends=True)).__next__)
        for tok in tokens:
            if tok.type == tokenize.COMMENT and KOREAN_TEXT_RE.search(tok.string):
                findings.append({"line": tok.start[0], "text": tok.string.strip()})
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return findings


def check_indentation(source: str) -> dict:
    """
    Return {"consistent": bool, "uses_tabs": bool, "uses_spaces": bool}.

    Inconsistent means the file mixes tabs and spaces for indentation.
    """
    uses_tabs = False
    uses_spaces = False

    try:
        tokens = tokenize.generate_tokens(iter(source.splitlines(keepends=True)).__next__)
        for tok in tokens:
            if tok.type == tokenize.INDENT:
                if "\t" in tok.string:
                    uses_tabs = True
                if " " in tok.string:
                    uses_spaces = True
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass

    return {
        "consistent": not (uses_tabs and uses_spaces),
        "uses_tabs": uses_tabs,
        "uses_spaces": uses_spaces,
    }


def run_hygiene_check(file_path: str) -> Dict[str, Any]:
    """Run all hygiene checks on a Python file and return a combined report."""
    path = Path(file_path)
    source = path.read_text(encoding="utf-8")

    korean_comments = find_korean_comments(source)
    indentation = check_indentation(source)
    has_utf8 = check_utf8_declaration(source)

    passed = has_utf8 and not korean_comments and indentation["consistent"]

    return {
        "file": str(path),
        "passed": passed,
        "utf8_declaration": has_utf8,
        "korean_comments": korean_comments,
        "indentation": indentation,
    }
