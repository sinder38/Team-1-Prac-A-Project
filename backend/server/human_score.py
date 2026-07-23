"""Human score persist: JSON source of truth, MD rendered for display/archive."""

from __future__ import annotations

import json
import re
from pathlib import Path

from agents.paths import DATA_DIR
from server.files import write_markdown

_DIMS = (
    ("macro", "Macro / News Weight", "Macro"),
    ("technical", "Technical Structure", "Technical"),
    ("almanac", "Almanac Seasonal Weight", "Almanac"),
    ("aiAgreement", "AI Model Agreement Quality", "AI Agreement"),
    ("wildCard", "Wild Card / Human Observation", "Wild Card"),
)
_EVIDENCE = (
    ("almanac", "R3 Almanac Agent Output"),
    ("macro", "R4 Macro Agent Output"),
    ("technical", "R5 Technical Agent Output"),
    ("llm", "R6 LLM Comparison Output"),
)
_PLACEHOLDER = "________"


def _signed(score) -> str:
    try:
        n = int(score)
    except (TypeError, ValueError):
        n = 0
    return f"+{n}" if n > 0 else str(n)


def _total(scores: dict) -> int:
    return sum(int(scores.get(k) or 0) for k, _, _ in _DIMS)


def render_human_score_markdown(report: dict) -> str:
    """W28-style markdown from a report JSON payload."""
    form = report.get("form") or {}
    scores = form.get("scores") or {}
    reasoning = form.get("reasoning") or {}
    evidence = form.get("evidence") or {}
    ai_said = report.get("aiSaid") or {}
    week = str(report.get("week") or "—")
    m = re.search(r"W(\d{1,2})", week, re.I)
    title = f"Week {int(m.group(1))}" if m else week
    total = report.get("total")
    if total is None:
        total = _total(scores)
    consensus = (report.get("consensus") or "—").strip()

    table = [
        "| Dimension                         | AI Said                                   | Team Score | Team Reasoning |",
        "| --------------------------------- | ----------------------------------------- | :--------: | -------------- |",
    ]
    for key, label, _ in _DIMS:
        said = str(ai_said.get(key) or "—").replace("|", "/")
        reason = str(reasoning.get(key) or _PLACEHOLDER).replace("|", "/")
        table.append(f"| **{label}** | {said} | **{_signed(scores.get(key))}** | {reason} |")

    judgements = []
    for i, (key, label, _) in enumerate(_DIMS, 1):
        judgements.append(
            f"### {i}. {label} — Score: {_signed(scores.get(key))}\n\n"
            f"{reasoning.get(key) or _PLACEHOLDER}\n"
        )

    breakdown = " + ".join(f"{short} {_signed(scores.get(key))}" for key, _, short in _DIMS)
    evidence_lines = [f"* {label}" for key, label in _EVIDENCE if evidence.get(key)]

    parts = [
        f"# Human Score Analyst Output — {title}",
        "",
        "## AI Consensus",
        "",
        f"**{consensus}**",
        "",
        "---",
        "",
        "## Human Score Table",
        "",
        *table,
        "",
        "---",
        "",
        "## Human Score Total",
        "",
        f"**{_signed(total)}**",
        "",
        f"({breakdown})",
        "",
        "---",
        "",
        "## Five-Dimension Judgement",
        "",
        *judgements,
        "---",
        "",
        "## Human Call",
        "",
        f"**{form.get('humanCall') or 'Neutral'}**",
        "",
        "---",
        "",
        "## Confidence",
        "",
        f"**{form.get('confidence') or 'Medium'}**",
        "",
        "---",
        "",
        "## Override Paragraph",
        "",
        form.get("overrideParagraph") or _PLACEHOLDER,
        "",
        "---",
        "",
        "## Wild Card Insight",
        "",
        form.get("wildCardInsight") or _PLACEHOLDER,
        "",
        "---",
        "",
        "## Invalidation Condition",
        "",
        form.get("invalidation") or _PLACEHOLDER,
        "",
        "---",
        "",
        "## Evidence Used",
        "",
        *evidence_lines,
    ]
    return "\n".join(parts)


def save_human_score(stem: str, report: dict, *, data_root: Path | None = None) -> Path:
    """Write human_score_{stem}.json + rendered .md. Overwrites if present."""
    stem = stem.upper()
    if not re.fullmatch(r"W\d{2}", stem):
        raise ValueError(f"Invalid week stem: {stem!r}")
    if not isinstance(report, dict) or not isinstance(report.get("form"), dict):
        raise ValueError("Human score report requires a form object")

    root = data_root or DATA_DIR
    payload = dict(report)
    payload.setdefault("week", stem)
    scores = (payload.get("form") or {}).get("scores") or {}
    if payload.get("total") is None:
        payload["total"] = _total(scores)

    human_dir = root / "human"
    human_dir.mkdir(parents=True, exist_ok=True)
    (human_dir / f"human_score_{stem}.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return write_markdown(
        human_dir / f"human_score_{stem}.md",
        render_human_score_markdown(payload),
    )


def load_human_score_json(stem: str, *, data_root: Path | None = None) -> dict | None:
    """Raw report dict from human_score_{stem}.json, or None."""
    path = (data_root or DATA_DIR) / "human" / f"human_score_{stem}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("form"), dict):
        return None
    return data
