"""Shared file writers. Keep this boundary when swapping disk for sqlite."""

from __future__ import annotations

from pathlib import Path


def write_markdown(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
    return path
