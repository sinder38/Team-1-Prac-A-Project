"""Pipeline stage functions — one per agent type."""

from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from agents.almanac.almanac_agent import AlmanacAgent
from agents.delta import DeltaAgent
from agents.evidence.evidence_agent import EvidenceAgent
from core.io import FileSaver, week_stem
from llm.openrouter import build_agent
from llm.openrouter import _row
from agents.macro.macro_agent import MacroAgent
from agents.paths import DATA_DIR, REPO_ROOT
from pipeline.config import LLMModelEntry, StageConfig
from pipeline.context import PipelineContext
from core.schemas import EvidenceOutput
from agents.technical.technical_agent import TechnicalAgent

US_EASTERN = ZoneInfo("America/New_York")
MARKET_CLOSE_BUFFER = time(16, 15)


def _save_artifacts(
    agent, output, prediction_date: date, config: StageConfig
) -> None:
    week_stem_date = week_stem(prediction_date)

    # TODO: move saving as json into database
    if config.artifacts.save_json:
        FileSaver.for_agent(agent.agent_type).save(
            agent.render_json(output, prediction_date),
            f"{week_stem(prediction_date)}.json",
        )

    if config.artifacts.save_md:
        md = agent.render_md(output, prediction_date)

        md_path = DATA_DIR / agent.agent_type
        if agent.agent_type == "evidence":
            filename = f"actuals_{week_stem_date}.md"
        else:
            filename = f"{agent.agent_type}_agent_{week_stem_date}.md"
        FileSaver(md_path).save(md, filename)


def run_almanac(ctx: PipelineContext, config: StageConfig) -> None:

    agent = AlmanacAgent()
    output = agent.run(ctx.prediction_date, horizon_days=ctx.horizon_days)
    ctx.almanac = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_technical(ctx: PipelineContext, config: StageConfig) -> None:

    agent = TechnicalAgent()
    output = agent.run(ctx.prediction_date, horizon_days=ctx.horizon_days)
    ctx.technical = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_macro(ctx: PipelineContext, config: StageConfig) -> None:
    agent = MacroAgent()
    output = agent.run(ctx.prediction_date, horizon_days=ctx.horizon_days)
    ctx.macro = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_evidence(
    ctx: PipelineContext,
    config: StageConfig,
    data_root: Path | None = None,
    market_data_provider=None,
    yield_data_provider=None,
    chart_provider=None,
) -> None:
    agent = EvidenceAgent(
        data_root=data_root,
        market_data_provider=market_data_provider,
        yield_data_provider=yield_data_provider,
        chart_provider=chart_provider,
    )

    snapshot = agent.fetch_snapshot(ctx.prediction_date)
    output = EvidenceOutput(
        prediction_date=ctx.prediction_date,
        week=week_stem(ctx.prediction_date),
        content=agent.render_report(snapshot),
    )
    agent.generate_evidence_charts(snapshot)

    ctx.evidence = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_delta(
    ctx: PipelineContext,
    config: StageConfig,
    repo_root: Path | None = None,
    actuals_markdown: str | None = None,
    now: datetime | None = None,
) -> None:
    root = repo_root or REPO_ROOT
    actuals_week = config.delta.actuals_week
    if actuals_week == "auto":
        actuals_week = week_stem(ctx.prediction_date)
    _require_completed_week(ctx.prediction_date, actuals_week, now)

    prediction_week = config.delta.prediction_week
    if prediction_week == "previous":
        actuals_number = int(actuals_week[1:])
        prediction_week = (
            "W53" if actuals_number == 1 else f"W{actuals_number - 1:02d}"
        )

    agent = DeltaAgent(repo_root=root)
    output = agent.run(
        prediction_week=prediction_week,
        actuals_week=actuals_week,
        actuals_markdown=actuals_markdown,
    )
    ctx.delta = output
    week = prediction_week.removeprefix("v")
    if config.artifacts.save_md:
        agent.write_markdown(
            output,
            root / "data" / "qa" / f"delta_{week}.md",
        )
    # Delta history and future weight suggestions need a structured artifact.
    agent.write_json(
        output,
        root / "data" / "outputs" / "delta" / f"delta_{week}.json",
    )


def _require_completed_week(
    reference_date: date,
    actuals_week: str,
    now: datetime | None = None,
) -> None:
    """Reject current-week scoring until the Friday close is available."""
    week_number = int(actuals_week.removeprefix("vW").removeprefix("W"))
    iso_year = reference_date.isocalendar().year
    week_end = date.fromisocalendar(iso_year, week_number, 5)
    current = now or datetime.now(US_EASTERN)
    if current.tzinfo is None:
        current = current.replace(tzinfo=US_EASTERN)
    else:
        current = current.astimezone(US_EASTERN)

    is_after_close = (
        current.date() > week_end
        or (
            current.date() == week_end
            and current.time().replace(tzinfo=None) >= MARKET_CLOSE_BUFFER
        )
    )
    if not is_after_close:
        raise ValueError(
            f"{actuals_week} actuals are not complete until Friday after "
            "the US market close."
        )


def run_llm(
    ctx: PipelineContext, config: StageConfig, entry: LLMModelEntry
) -> tuple[str, dict]:
    """Run one LLM model. Returns (slug, row_dict) for the comparison table."""

    agent = build_agent(entry, default_max_retries=config.llm.max_retries)

    prompt = agent.build_prompt(ctx.prediction_date, ctx)
    raw = agent.query(prompt)
    output = agent.parse_response(raw, ctx.prediction_date)
    ctx.llm_outputs.append(output)

    if config.artifacts.save_md:
        FileSaver(DATA_DIR / "llm").save(
            agent.render_md(output, ctx.prediction_date),
            f"synthesis_{entry.slug}_{week_stem(ctx.prediction_date)}.txt",
        )

    return entry.slug, _row(output)
