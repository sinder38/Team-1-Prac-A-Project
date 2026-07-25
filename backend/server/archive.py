"""Load human-readable past-week archives from data/{almanac,macro,...}."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from agents.paths import DATA_DIR
from server.db import render, repository as repo
from server.db.context import db_session
from server.utils import parse_date

DATA_ROOT = DATA_DIR

# The week stem must be directly before the file extension. This rejects names
# such as notes_W99_draft.md.
_STEM_RE = re.compile(r"_(W\d{2})\.")
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


def _agent_card(agent_key: str, label: str, payload: dict | None) -> dict | None:
    """Build a frontend agent card from a stored payload.

    ``rawData`` is regenerated from the structured payload (lossy for
    technical, which the schema cannot fully reproduce — see server.db.render).
    """
    if not payload:
        return None
    raw = render.render_markdown(agent_key, payload)
    return {
        "agent": label,
        "metrics": _extract_metrics(agent_key, raw),
        "rawData": raw,
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


def _consensus_result(models: list[dict]) -> tuple[str, int]:
    """Return the most common regime and the disagreement percentage."""
    counts: dict[str, int] = {}
    for model in models:
        regime = model["consensus"]
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
        models.append(model)

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
    """Return the stored human-score report for a week from the DB."""
    with db_session() as session:
        row = repo.get_archive_human_score(session, _require_stem(stem))
        return row.payload if row else None


def _human_score(stem: str, pred: date | None = None) -> dict | None:
    """Same as load_human_score. Callers that already know the prediction date
    (load_archive_week) pass it in to avoid re-scanning the data tree."""
    path = DATA_ROOT / "human" / f"human_score_{stem}.md"
    text = _read_text(path)
    if not text:
        return None

    if pred is None:
        pred = discover_archive_stems().get(stem) or _prediction_date_for_stem(stem)
    week = _label_for_stem(stem, pred)

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
    with db_session() as session:
        run = repo.get_archive_run(session, stem)
        if run is None:
            return None
        pred = run.prediction_date
        cards = {
            agent: repo.get_archive_agent_payload(session, stem, agent)
            for agent in ("almanac", "macro", "technical", "evidence")
        }
        comparison = repo.get_archive_llm_comparison(session, stem)
        human_row = repo.get_archive_human_score(session, stem)
        human = human_row.payload if human_row else None

    return {
        "week": _label_for_stem(stem, pred),
        "stem": stem,
        "prediction_date": pred.isoformat(),
        "source": "archive",
        "almanac": _agent_card("almanac", "Almanac Agent", cards["almanac"]),
        "macro": _agent_card("macro", "Macro Agent", cards["macro"]),
        "technical": _agent_card("technical", "Technical Agent", cards["technical"]),
        "evidence": _agent_card("evidence", "Evidence Agent", cards["evidence"]),
        "llmComparison": comparison,
        "humanScoreReport": human,
    }


def _week_sort_value(entry: dict) -> str:
    """Return the label used to order week entries."""
    return str(entry["week"])


def _run_entry(run) -> dict:
    return {
        "week": _label_for_stem(run.week_stem, run.prediction_date),
        "stem": run.week_stem,
        "prediction_date": run.prediction_date.isoformat(),
        "run_id": run.run_id,
        "source": run.source,
    }


def list_archive_weeks() -> list[dict]:
    with db_session() as session:
        runs = repo.list_runs(session, source="archive")
        weeks = [_run_entry(run) for run in runs]
    weeks.sort(key=_week_sort_value)
    return weeks


def list_all_weeks() -> list[dict]:
    """Runtime run weeks, plus archive markdown weeks for any gaps."""
    with db_session() as session:
        runs = repo.list_runs(session)

    by_week: dict[str, dict] = {}
    # Runtime runs first; keep the newest per week.
    runtime = sorted(
        (r for r in runs if r.source == "run" and r.week_stem),
        key=lambda r: r.created_at,
    )
    for run in runtime:
        by_week[_label_for_stem(run.week_stem, run.prediction_date)] = _run_entry(run)

    for run in runs:
        if run.source != "archive":
            continue
        by_week.setdefault(
            _label_for_stem(run.week_stem, run.prediction_date), _run_entry(run)
        )

    return [by_week[week] for week in sorted(by_week)]
