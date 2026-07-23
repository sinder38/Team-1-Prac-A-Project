"""Load human-readable past-week archives from data/{almanac,macro,...}."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from agents.paths import DATA_DIR
from server.human_score import (
    load_human_score_json,
    render_human_score_markdown,
    save_human_score as _save_human_score_files,
)
from server.utils import OUTPUTS_ROOT, artifact_path, parse_date

DATA_ROOT = DATA_DIR

# The week stem must be directly before the file extension. This rejects names
# such as notes_W99_draft.md.
_STEM_RE = re.compile(r"_(W\d{2})\.")
_RUN_DATE_RE = re.compile(r"run\s+(\d{4}-\d{2}-\d{2})", re.I)
_CONFIDENCE_SCORE = {"Low": 40, "Low-Medium": 55, "Medium": 65, "High": 85}

# Patterns for standard and LLM artifacts stored under data/outputs.
_STANDARD_RUN = re.compile(r"^[a-z]+_(W\d{2})_(.+?)(?:_\d+d|_[a-z]+_\d+d)?\.json$")
_LLM_RUN = re.compile(r"^llm_[a-z0-9]+_(W\d{2})_(.+?)_\d+d\.json$")

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

# Per-agent (label, regex) pairs pulled from the agent markdown headers.
_AGENT_METRICS = {
    "almanac": [
        ("Thesis", r'ALMANAC THESIS:\s*"?(.+?)"?\s*$'),
        ("Seasonal Bias", r"ALMANAC SEASONAL BIAS:\s*(.+?)\.?$"),
        ("Monthly Bias", r"PATTERN CONFIDENCE:\s*(\w+)"),
    ],
    "macro": [
        ("Primary Driver", r"PRIMARY DRIVER THIS WEEK:\s*(.+)$"),
        ("Fed Rate", r"Current Fed rate:\s*(.+)$"),
        ("10Y Yield", r"10-year yield:\s*([\d.]+%?)"),
        ("Macro Bias", r"MACRO BIAS:\s*(.+)$"),
    ],
    "technical": [
        ("Last Close", r"LAST CLOSE:\s*(.+)$"),
        ("Technical Bias", r"TECHNICAL BIAS:\s*(.+?)\.?$"),
        ("EMA Condition", r"EMA condition:\s*(.+)$"),
        ("Key Levels", r"Resistance 1:\s*(.+)$"),
    ],
}


def _require_stem(stem: str) -> str:
    stem = stem.upper()
    if not re.fullmatch(r"W\d{2}", stem):
        raise ValueError(f"Invalid week stem: {stem!r}")
    return stem


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
    # No run date in the markdown → assume the archive belongs to the current year.
    week_num = int(stem[1:])
    return date.fromisocalendar(date.today().year, week_num, 1)


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

    discovered: dict[str, date] = {}
    for stem in stems:
        discovered[stem] = _prediction_date_for_stem(stem)
    return discovered


def _extract_metrics(agent: str, text: str) -> list[dict]:
    metrics: list[dict] = []
    for label, pattern in _AGENT_METRICS.get(agent, []):
        m = re.search(pattern, text, re.I | re.M)
        if m:
            metrics.append({"label": label, "value": m.group(1).strip().strip('"')})
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
    cells: list[str] = []
    for part in line.strip().strip("|").split("|"):
        cells.append(part.strip())
    return cells


def _comparison_table(
    lines: list[str],
) -> tuple[list[str], dict[str, list[str]]]:
    """Read the model names and dimension rows from a Markdown table."""
    header: list[str] = []
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
        if not header and cells[0].lower() in ("dimension", ""):
            header = cells[1:]
            continue
        if not header:
            continue

        key = re.sub(r"[*_]", "", cells[0]).strip().lower()
        rows[key] = cells[1 : 1 + len(header)]

    return header, rows


def _plain_english_summaries(lines: list[str]) -> dict[str, str]:
    """Read the bullet list under the Plain-English summaries heading."""
    summaries: dict[str, str] = {}
    in_section = False

    for line in lines:
        if re.match(r"^##\s+Plain-English", line, re.I):
            in_section = True
            continue
        if in_section and line.startswith("##"):
            break
        if not in_section:
            continue

        match = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.+)$", line.strip())
        if match:
            model_name = match.group(1).strip()
            summaries[model_name] = match.group(2).strip()

    return summaries


def _comparison_model(
    name: str,
    index: int,
    rows: dict[str, list[str]],
    summaries: dict[str, str],
) -> dict:
    """Build the frontend data for one model column."""
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
        "plainEnglish": summaries.get(name, "—"),
    }

    for dimension, field in _DIM_KEYS.items():
        values = rows.get(dimension)
        if not values or index >= len(values):
            continue

        value = values[index].strip() or "—"
        if field == "confidenceLabel":
            model["confidenceLabel"] = value
            model["confidence"] = _CONFIDENCE_SCORE.get(value, 50)
        else:
            model[field] = value

    return model


_EMPTY_CELLS = frozenset({"", "—", "-", "–", "n/a", "na"})


def _is_empty_cell(value: object) -> bool:
    return str(value or "").strip().lower() in _EMPTY_CELLS


def _model_has_output(model: dict) -> bool:
    """True when a comparison column has real content (skip unused/failed models)."""
    for key in (
        "consensus",
        "spx",
        "ndx",
        "iwm",
        "evidence",
        "contradiction",
        "invalidation",
        "plainEnglish",
    ):
        if not _is_empty_cell(model.get(key)):
            return True
    return False


def _consensus_result(models: list[dict]) -> tuple[str, int]:
    """Return the most common regime and the disagreement percentage."""
    counts: dict[str, int] = {}
    for model in models:
        regime = model["consensus"]
        if _is_empty_cell(regime):
            continue
        counts[regime] = counts.get(regime, 0) + 1

    final_consensus = "Uncertain"
    agreeing_models = 0
    for regime, count in counts.items():
        if count > agreeing_models:
            final_consensus = regime
            agreeing_models = count

    if not models:
        return final_consensus, 0

    disagreeing_models = len(models) - agreeing_models
    disagreement_ratio = round(disagreeing_models / len(models) * 100)
    return final_consensus, disagreement_ratio


def _parse_llm_comparison(stem: str) -> dict | None:
    path = DATA_ROOT / "llm" / f"llm_comparison_{stem}.md"
    text = _read_text(path)
    if not text:
        return None

    lines = text.splitlines()
    header, rows = _comparison_table(lines)
    if not header:
        return None

    summaries = _plain_english_summaries(lines)
    models: list[dict] = []
    for index, name in enumerate(header):
        model = _comparison_model(name, index, rows, summaries)
        if _model_has_output(model):
            models.append(model)

    if not models:
        return None

    final_consensus, disagreement_ratio = _consensus_result(models)

    return {
        "finalConsensus": final_consensus,
        "disagreementRatio": disagreement_ratio,
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


def _clean_consensus_label(body: str) -> str:
    """Reduce an 'AI Consensus' section to its short regime label.

    'Neutral-Bullish (3 of 5 models) — cautious...' -> 'Neutral-Bullish'
    """
    label = re.sub(r"^\*\*|\*\*$", "", body.split("\n")[0].strip()).strip()
    label = label.split("—")[0].strip()  # drop trailing description
    head = label.split("(")[0].strip()  # drop "(3 of 5 models)"
    return head or label


def load_human_score(stem: str) -> dict | None:
    """Parse data/human/human_score_{stem} into the frontend report shape."""
    return _human_score(_require_stem(stem))


def save_human_score(stem: str, report: dict) -> Path:
    """Persist report JSON + MD under DATA_ROOT/human/."""
    return _save_human_score_files(_require_stem(stem), report, data_root=DATA_ROOT)


def _human_score(stem: str, pred: date | None = None) -> dict | None:
    """Same as load_human_score. Callers that already know the prediction date
    (load_archive_week) pass it in to avoid re-scanning the data tree."""
    data = load_human_score_json(stem, data_root=DATA_ROOT)
    path = DATA_ROOT / "human" / f"human_score_{stem}.md"
    text = None if data is not None else _read_text(path)
    if data is None and not text:
        return None

    if pred is None:
        pred = discover_archive_stems().get(stem) or _prediction_date_for_stem(stem)
    week = _label_for_stem(stem, pred)

    if data is not None:
        md = _read_text(path) or render_human_score_markdown({**data, "week": week})
        return {
            "form": data["form"],
            "week": data.get("week") or week,
            "predictionDate": pred.isoformat(),
            "consensus": data.get("consensus") or "—",
            "aiSaid": data.get("aiSaid") or {},
            "total": data.get("total", 0),
            "rawMarkdown": md,
            "source": "archive",
        }

    assert text is not None  # missing file already returned above

    scores: dict[str, int] = {}
    reasoning: dict[str, str] = {}
    ai_said: dict[str, str] = {}
    for key in _HUMAN_DIM_KEYS.values():
        scores[key] = 0
        reasoning[key] = ""
        ai_said[key] = "—"

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

    consensus = _clean_consensus_label(_section_body(text, "AI Consensus"))

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

    # These flags only show whether a source is mentioned in the report. They
    # do not measure how strongly the team weighted that source.
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
    stem = _require_stem(stem)
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
        "humanScoreReport": _human_score(stem, pred),
    }


def list_archive_weeks() -> list[dict]:
    weeks: list[dict] = []
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
    weeks.sort(key=_week_sort_value)
    return weeks


def _week_sort_value(entry: dict) -> str:
    """Return the label used to order week entries."""
    return str(entry["week"])


def _latest_run_ids() -> dict[str, str]:
    """Find the newest run ID for each week in the output folders."""
    best_runs: dict[str, tuple[float, str]] = {}
    if not OUTPUTS_ROOT.exists():
        return {}

    for folder in OUTPUTS_ROOT.iterdir():
        if not folder.is_dir():
            continue

        for path in folder.glob("*.json"):
            match = _STANDARD_RUN.match(path.name)
            if not match:
                match = _LLM_RUN.match(path.name)
            if not match:
                continue

            stem = match.group(1)
            run_id = match.group(2)
            try:
                modified_time = path.stat().st_mtime
            except OSError:
                modified_time = 0.0

            candidate = (modified_time, run_id)
            current = best_runs.get(stem)
            if current is None or candidate > current:
                best_runs[stem] = candidate

    latest: dict[str, str] = {}
    for stem, (_, run_id) in best_runs.items():
        latest[stem] = run_id
    return latest


def _run_prediction_date(stem: str, run_id: str) -> date:
    """Read a prediction date from any available artifact in the run."""
    for agent in ("almanac", "technical", "macro", "evidence"):
        if agent == "evidence":
            path = artifact_path(agent, stem, run_id)
        else:
            path = artifact_path(
                agent,
                stem,
                run_id,
                horizon_days=7,
            )
        if not path.exists():
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            raw_date = data.get("prediction_date")
            if raw_date:
                return parse_date(str(raw_date)[:10])
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue

    year = date.today().isocalendar().year
    week_number = int(stem[1:])
    return date.fromisocalendar(year, week_number, 1)


def _run_week_entry(stem: str, run_id: str) -> dict:
    """Build one frontend week entry for a generated JSON run."""
    prediction_date = _run_prediction_date(stem, run_id)
    year = prediction_date.isocalendar().year
    label = f"{year}-{stem}"
    return {
        "week": label,
        "stem": stem,
        "prediction_date": prediction_date.isoformat(),
        "run_id": run_id,
        "source": "run",
    }


def list_all_weeks() -> list[dict]:
    """JSON run weeks from data/outputs, plus archive markdown weeks for gaps."""
    by_week: dict[str, dict] = {}

    for stem, run_id in _latest_run_ids().items():
        entry = _run_week_entry(stem, run_id)
        by_week[entry["week"]] = entry

    for entry in list_archive_weeks():
        by_week.setdefault(entry["week"], entry)

    weeks: list[dict] = []
    for week in sorted(by_week):
        weeks.append(by_week[week])
    return weeks
