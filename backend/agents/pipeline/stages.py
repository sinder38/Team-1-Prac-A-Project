"""Pipeline stage functions — one per agent type."""

from datetime import date
from pathlib import Path

from agents.almanac.almanac_agent import AlmanacAgent
from agents.evidence.evidence_agent import EvidenceAgent
from agents.io import FileSaver, week_stem
from agents.llm.multi_model_runner import OpenRouterAgent, _row
from agents.macro.macro_agent import MacroAgent
from agents.pipeline.config import LLMModelEntry, PipelineConfig
from agents.pipeline.context import PipelineContext
from agents.technical.technical_agent import TechnicalAgent

REPO_ROOT = Path(__file__).resolve().parents[3]


def _save_artifacts(
    agent, output, prediction_date: date, config: PipelineConfig
) -> None:
    week_stem_date = week_stem(prediction_date)

    if config.artifacts.save_json:
        FileSaver.for_agent(agent.agent_type).save(
            agent.render_json(output, prediction_date),
            f"{week_stem(prediction_date)}.json",
        )

    if config.artifacts.save_md:
        md = agent.render_md(output, prediction_date)

        md_path = REPO_ROOT / "data" / agent.agent_type
        FileSaver(md_path).save(md, f"{agent.agent_type}_agent_{week_stem_date}.md")


def run_almanac(ctx: PipelineContext, config: PipelineConfig) -> None:

    agent = AlmanacAgent()
    output = agent.run(ctx.prediction_date)
    ctx.almanac = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_technical(ctx: PipelineContext, config: PipelineConfig) -> None:

    agent = TechnicalAgent()
    output = agent.run(ctx.prediction_date)
    ctx.technical = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_macro(ctx: PipelineContext, config: PipelineConfig) -> None:
    agent = MacroAgent()
    output = agent.run(ctx.prediction_date)
    ctx.macro = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_evidence(
    ctx: PipelineContext,
    config: PipelineConfig,
    data_root: Path | None = None,
) -> None:
    agent = EvidenceAgent(data_root=data_root)
    output = agent.run(ctx.prediction_date)
    ctx.evidence = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_llm(
    ctx: PipelineContext, config: PipelineConfig, entry: LLMModelEntry
) -> tuple[str, dict]:
    """Run one LLM model. Returns (slug, row_dict) for the comparison table."""

    agent = OpenRouterAgent(model_name=entry.label, model_id=entry.id)

    prompt = agent.build_prompt(ctx.prediction_date, ctx)
    raw = agent.query(prompt)
    output = agent.parse_response(raw, ctx.prediction_date)
    ctx.llm_outputs.append(output)

    if config.artifacts.save_md:
        FileSaver(REPO_ROOT / "data" / "llm").save(
            agent.render_md(output, ctx.prediction_date),
            f"synthesis_{entry.slug}_{week_stem(ctx.prediction_date)}.txt",
        )

    return entry.slug, _row(output)
