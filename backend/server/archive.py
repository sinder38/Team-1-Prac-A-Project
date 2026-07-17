"""Load human-readable past-week archives from data/{almanac,macro,...}."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from server.utils import OUTPUTS_ROOT, REPO_ROOT, artifact_path, parse_date

DATA_ROOT = REPO_ROOT / "data"

_STEM_RE = re.compile(r"(W\d{2})")
_RUN_DATE_RE = re.compile(r"run\s+(\d{4}-\d{2}-\d{2})", re.I)
_CONFIDENCE_SCORE = {"Low": 40, "Low-Medium": 55, "Medium": 65, "High": 85}

_AGENT_FILES = {
    "almanac": ["almanac/almanac_agent_{stem}.md"],
    "macro": ["macro/macro_agent_{stem}.md"],
    "technical": [
        "technical/technical_agent_{stem}.md",
        "technical/technnical_agent_{stem}.md",  # legacy typo in repo
    ],
    "evidence": [
        "evidence/actuals_{stem}.md",
        "evidence/evidence_agent_{stem}.md",
    ],
}

_DIM_KEYS = {
    "weekly regime": "consensus",
    "confidence score": "confidenceLabel",
    "spx % estimate": "spx",
    "ndx % estimate": "ndx",
    "iwm % estimate": "iwm",
    "top supporting reason": "evidence",
    "top contradiction": "contradiction",
    "invalidation condition": "invalidation",
}

_HUMAN_DIM_KEYS = {
    "macro / news weight": "macro",
    "technical structure": "technical",
    "almanac seasonal weight": "almanac",
    "ai model agreement quality": "aiAgreement",
    "wild card / human observation": "wildCard",
}

_SCORE_RE = re.compile(r"([+-]?\d+)")


def _label_for_stem(stem: str, pred: date) -> str:
    """Prefer the archive stem's week number over the prediction date's ISO week.

    Some comparison headers use a run date that falls in a neighboring ISO week
    (e.g. W23 archived as run 2026-06-08, which is ISO W24).
    """
    year = pred.isocalendar()[0]
    return f"{year}-{stem}"


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _resolve_agent_path(agent: str, stem: str) -> Path | None:
    for pattern in _AGENT_FILES.get(agent, []):
        path = DATA_ROOT / pattern.format(stem=stem)
        if path.exists():
            return path
    return None


def _prediction_date_for_stem(stem: str) -> date:
    comparison = DATA_ROOT / "llm" / f"llm_comparison_{stem}.md"
    text = _read_text(comparison)
    if text:
        m = _RUN_DATE_RE.search(text)
        if m:
            try:
                return parse_date(m.group(1))
            except ValueError:
                pass
    week_num = int(stem[1:])
    year = 2026  # project year for these archives
    return date.fromisocalendar(year, week_num, 1)


def discover_archive_stems() -> dict[str, date]:
    """Map stem (W25) -> prediction_date for weeks with any archive markdown."""
    if not DATA_ROOT.exists():
        return {}

    stems: set[str] = set()
    search_dirs = [
        DATA_ROOT / "almanac",
        DATA_ROOT / "macro",
        DATA_ROOT / "technical",
        DATA_ROOT / "evidence",
        DATA_ROOT / "llm",
        DATA_ROOT / "human",
    ]
    for folder in search_dirs:
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            if not path.is_file():
                continue
            m = _STEM_RE.search(path.name)
            if m:
                stems.add(m.group(1))

    return {stem: _prediction_date_for_stem(stem) for stem in stems}


def _extract_metrics(agent: str, text: str) -> list[dict]:
    metrics: list[dict] = []

    def add(label: str, pattern: str) -> None:
        m = re.search(pattern, text, re.I | re.M)
        if m:
            metrics.append({"label": label, "value": m.group(1).strip().strip('"')})

    if agent == "almanac":
        add("Thesis", r'ALMANAC THESIS:\s*"?(.+?)"?\s*$')
        add("Seasonal Bias", r"ALMANAC SEASONAL BIAS:\s*(.+?)\.?$")
        add("Monthly Bias", r"PATTERN CONFIDENCE:\s*(\w+)")
    elif agent == "macro":
        add("Primary Driver", r"PRIMARY DRIVER THIS WEEK:\s*(.+)$")
        add("Fed Rate", r"Current Fed rate:\s*(.+)$")
        add("10Y Yield", r"10-year yield:\s*([\d.]+%?)")
        add("Macro Bias", r"MACRO BIAS:\s*(.+)$")
    elif agent == "technical":
        add("Last Close", r"LAST CLOSE:\s*(.+)$")
        add("Technical Bias", r"TECHNICAL BIAS:\s*(.+?)\.?$")
        add("EMA Condition", r"EMA condition:\s*(.+)$")
        add("Key Levels", r"Resistance 1:\s*(.+)$")

    return metrics[:4]


def _agent_card(agent_key: str, label: str, stem: str) -> dict | None:
    path = _resolve_agent_path(agent_key, stem)
    if not path:
        return None
    text = _read_text(path)
    if not text:
        return None
    return {
        "agent": label,
        "metrics": _extract_metrics(agent_key, text),
        "rawData": text,
    }


def _split_table_row(line: str) -> list[str]:
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    return parts


def _parse_llm_comparison(stem: str) -> dict | None:
    path = DATA_ROOT / "llm" / f"llm_comparison_{stem}.md"
    text = _read_text(path)
    if not text:
        return None

    lines = text.splitlines()
    header: list[str] | None = None
    rows: dict[str, list[str]] = {}

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*:?-{3,}", stripped):
            continue
        cells = _split_table_row(stripped)
        if len(cells) < 2:
            continue
        if header is None and cells[0].lower() in ("dimension", ""):
            header = cells[1:]
            continue
        if header is None:
            continue
        key = re.sub(r"[*_]", "", cells[0]).strip().lower()
        rows[key] = cells[1 : 1 + len(header)]

    if not header:
        return None

    # Plain-English bullet list under ## Plain-English summaries
    plain: dict[str, str] = {}
    in_plain = False
    for line in lines:
        if re.match(r"^##\s+Plain-English", line, re.I):
            in_plain = True
            continue
        if in_plain and line.startswith("##"):
            break
        if in_plain:
            m = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.+)$", line.strip())
            if m:
                plain[m.group(1).strip()] = m.group(2).strip()

    models = []
    for i, name in enumerate(header):
        model = {
            "name": name,
            "consensus": "—",
            "confidence": 50,
            "confidenceLabel": "—",
            "spx": "—",
            "ndx": "—",
            "iwm": "—",
            "evidence": "—",
            "contradiction": "—",
            "invalidation": "—",
            "plainEnglish": plain.get(name, "—"),
        }
        for dim_label, field in _DIM_KEYS.items():
            values = rows.get(dim_label)
            if not values or i >= len(values):
                continue
            value = values[i].strip() or "—"
            if field == "confidenceLabel":
                model["confidenceLabel"] = value
                model["confidence"] = _CONFIDENCE_SCORE.get(value, 50)
            else:
                model[field] = value
        models.append(model)

    counts: dict[str, int] = {}
    for m in models:
        regime = m["consensus"]
        counts[regime] = counts.get(regime, 0) + 1
    final = max(counts, key=lambda key: counts.get(key, 0)) if counts else "Uncertain"
    agreeing = counts.get(final, 0)
    disagreement = (
        round(((len(models) - agreeing) / len(models)) * 100) if models else 0
    )

    return {
        "finalConsensus": final,
        "disagreementRatio": disagreement,
        "models": models,
    }


def _section_body(text: str, title: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(title)}\s*\n+(.*?)(?=\n##\s+|\Z)",
        re.I | re.S | re.M,
    )
    m = pattern.search(text)
    if not m:
        return ""
    body = m.group(1).strip()
    # Drop trailing horizontal rules
    body = re.sub(r"\n---\s*$", "", body).strip()
    # Unwrap a single bold wrapper like **Neutral-Bullish**
    bold = re.fullmatch(r"\*\*(.+?)\*\*", body)
    if bold:
        return bold.group(1).strip()
    return body


def _parse_score_cell(cell: str) -> int:
    cleaned = re.sub(r"[*_]", "", cell).strip()
    m = _SCORE_RE.search(cleaned)
    return int(m.group(1)) if m else 0


def load_human_score(stem: str) -> dict | None:
    """Parse data/human/human_score_{stem}.md into the frontend report shape."""
    stem = stem.upper()
    if not re.fullmatch(r"W\d{2}", stem):
        raise ValueError(f"Invalid week stem: {stem!r}")

    path = DATA_ROOT / "human" / f"human_score_{stem}.md"
    text = _read_text(path)
    if not text:
        return None

    pred = discover_archive_stems().get(stem) or _prediction_date_for_stem(stem)
    week = _label_for_stem(stem, pred)

    scores = {k: 0 for k in _HUMAN_DIM_KEYS.values()}
    reasoning = {k: "" for k in _HUMAN_DIM_KEYS.values()}
    ai_said = {k: "—" for k in _HUMAN_DIM_KEYS.values()}

    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.match(r"^\|\s*:?-+\s*\|", line.strip()):
            continue
        cells = _split_table_row(line)
        if len(cells) < 4:
            continue
        dim_label = re.sub(r"[*_]", "", cells[0]).strip().lower()
        if dim_label in ("dimension", ""):
            continue
        key = _HUMAN_DIM_KEYS.get(dim_label)
        if not key:
            continue
        ai_said[key] = re.sub(r"[*_]", "", cells[1]).strip() or "—"
        scores[key] = _parse_score_cell(cells[2])
        reasoning[key] = re.sub(r"[*_]", "", cells[3]).strip()

    consensus_body = _section_body(text, "AI Consensus")
    consensus = consensus_body.split("\n")[0].strip()
    consensus = re.sub(r"^\*\*|\*\*$", "", consensus).strip()
    # Keep the short regime label if present: "Neutral-Bullish (3 of 5 models) — ..."
    if "—" in consensus:
        consensus = consensus.split("—")[0].strip()
    if "(" in consensus:
        # Prefer "Neutral-Bullish" from "Neutral-Bullish (3 of 5 models)"
        head = consensus.split("(")[0].strip()
        if head:
            consensus = head

    human_call = _section_body(text, "Human Call") or "Neutral"
    confidence = _section_body(text, "Confidence") or "Medium"
    # Confidence is often just "Medium"
    confidence = confidence.split("\n")[0].strip()

    total_m = re.search(
        r"##\s+Human Score Total\s*\n+\*\*([+-]?\d+)\*\*",
        text,
        re.I,
    )
    total = int(total_m.group(1)) if total_m else sum(scores.values())

    evidence = {
        "almanac": "Almanac" in text,
        "macro": "Macro" in text,
        "technical": "Technical" in text,
        "llm": "LLM" in text or "R6" in text,
    }

    form = {
        "scores": scores,
        "reasoning": reasoning,
        "humanCall": human_call.split("\n")[0].strip(),
        "confidence": confidence,
        "overrideParagraph": _section_body(text, "Override Paragraph"),
        "wildCardInsight": _section_body(text, "Wild Card Insight"),
        "invalidation": _section_body(text, "Invalidation Condition"),
        "evidence": evidence,
    }

    return {
        "form": form,
        "week": week,
        "predictionDate": pred.isoformat(),
        "consensus": consensus or "—",
        "aiSaid": ai_said,
        "total": total,
        "rawMarkdown": text,
        "source": "archive",
    }


def load_archive_week(stem: str) -> dict | None:
    """Return frontend-shaped agent + LLM payloads for an archive week stem."""
    stem = stem.upper()
    if not re.fullmatch(r"W\d{2}", stem):
        raise ValueError(f"Invalid week stem: {stem!r}")

    archives = discover_archive_stems()
    if stem not in archives:
        return None

    pred = archives[stem]
    return {
        "week": _label_for_stem(stem, pred),
        "stem": stem,
        "prediction_date": pred.isoformat(),
        "source": "archive",
        "almanac": _agent_card("almanac", "Almanac Agent", stem),
        "macro": _agent_card("macro", "Macro Agent", stem),
        "technical": _agent_card("technical", "Technical Agent", stem),
        "evidence": _agent_card("evidence", "Evidence Agent", stem),
        "llmComparison": _parse_llm_comparison(stem),
        "humanScoreReport": load_human_score(stem),
    }


def list_archive_weeks() -> list[dict]:
    weeks = []
    for stem, pred in discover_archive_stems().items():
        weeks.append(
            {
                "week": _label_for_stem(stem, pred),
                "stem": stem,
                "prediction_date": pred.isoformat(),
                "run_id": None,
                "source": "archive",
            }
        )
    weeks.sort(key=lambda w: w["week"])
    return weeks


_STANDARD_RUN = re.compile(
    r"^[a-z]+_(W\d{2})_(.+?)(?:_\d+d|_[a-z]+_\d+d)?\.json$"
)
_LLM_RUN = re.compile(r"^llm_[a-z0-9]+_(W\d{2})_(.+?)_\d+d\.json$")


def list_all_weeks() -> list[dict]:
    """JSON run weeks from data/outputs, plus archive markdown weeks for gaps."""
    by_week: dict[str, dict] = {}

    if OUTPUTS_ROOT.exists():
        # stem -> run_id -> newest mtime seen for that run
        by_stem: dict[str, dict[str, float]] = {}
        for subdir in OUTPUTS_ROOT.iterdir():
            if not subdir.is_dir():
                continue
            for f in subdir.glob("*.json"):
                m = _STANDARD_RUN.match(f.name) or _LLM_RUN.match(f.name)
                if not m:
                    continue
                stem, run_id = m.group(1), m.group(2)
                try:
                    mtime = f.stat().st_mtime
                except OSError:
                    mtime = 0.0
                runs = by_stem.setdefault(stem, {})
                runs[run_id] = max(runs.get(run_id, 0.0), mtime)

        for stem, run_mtimes in by_stem.items():
            if not run_mtimes:
                continue
            # Newest mtime wins; equal mtime → lexicographic run_id (stable tie-break).
            run_id = max(run_mtimes.items(), key=lambda item: (item[1], item[0]))[0]
            pred = None
            for agent in ("almanac", "technical", "macro", "evidence"):
                if agent == "evidence":
                    path = artifact_path(agent, stem, run_id)
                else:
                    path = artifact_path(agent, stem, run_id, horizon_days=7)
                if not path.exists():
                    continue
                try:
                    raw = json.loads(path.read_text(encoding="utf-8")).get("prediction_date")
                    if raw:
                        pred = parse_date(str(raw)[:10])
                        break
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    continue
            if pred is None:
                pred = date.fromisocalendar(date.today().isocalendar()[0], int(stem[1:]), 1)
            label = f"{pred.isocalendar()[0]}-{stem}"
            by_week[label] = {
                "week": label,
                "stem": stem,
                "prediction_date": pred.isoformat(),
                "run_id": run_id,
                "source": "run",
            }

    for entry in list_archive_weeks():
        by_week.setdefault(entry["week"], entry)

    return [by_week[k] for k in sorted(by_week)]
