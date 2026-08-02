"""Comparison table builder for Multi-LLM pipeline output."""
from pipeline.config import LLMModelEntry


# Single source of truth for the comparison-table rows: (display name, row key).
COMPARISON_DIMENSIONS = [
    ("Weekly Regime",          "regime"),
    ("Confidence Score",       "confidence"),
    ("SPX % estimate",         "spx"),
    ("NDX % estimate",         "ndx"),
    ("IWM % estimate",         "iwm"),
    ("Top supporting reason",  "evidence"),
    ("Top contradiction",      "contradiction"),
    ("Invalidation condition", "invalidation"),
]


def _cell(text) -> str:
    """Make a string safe inside a single Markdown table cell."""
    return (str(text) if text else "\u2014").replace("|", "/").replace("\n", " ").replace("\r", " ").strip() or "\u2014"


def _row(output) -> dict:
    """Extract the comparison-table fields from an LLMOutput."""
    def rng(r):
        return f"{r.low}% to {r.high}%"
    return {
        "regime": output.weekly_regime.value,
        "confidence": output.confidence.value,
        "spx": rng(output.spx_range),
        "ndx": rng(output.ndx_range),
        "iwm": rng(output.iwm_range),
        "evidence": "; ".join(output.supporting_evidence) if output.supporting_evidence else "\u2014",
        "contradiction": "; ".join(output.contradictions) if output.contradictions else "\u2014",
        "invalidation": output.invalidation or "\u2014",
        "plain_english": output.plain_english or "\u2014",
    }


def build_comparison_md(rows_by_slug: dict, models: list[LLMModelEntry], tag: str, run_date) -> str:
    """Build the Multi-LLM comparison table."""
    labels = [m.label for m in models]

    head = [
        f"# Multi-LLM Comparison Table \u2014 {tag} (run {run_date.isoformat()})",
        "",
        "Prompt was identical across all models (fair-comparison rule).",
        "",
        "| Dimension | " + " | ".join(labels) + " |",
        "| :--- " + "| :--- " * len(labels) + "|",
    ]

    body = [
        f"| **{display}** | "
        + " | ".join(_cell(rows_by_slug.get(m.slug, {}).get(key, "\u2014")) for m in models)
        + " |"
        for display, key in COMPARISON_DIMENSIONS
    ]

    tail = ["", "## Plain-English summaries", ""]
    tail += [
        f"- **{m.label}:** {rows_by_slug.get(m.slug, {}).get('plain_english', '\u2014')}"
        for m in models
    ]
    tail += ["", "_Disclaimer: model output, not financial advice._", ""]

    return "\n".join(head + body + tail)
