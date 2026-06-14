"""Pipeline stage functions — one per agent type."""

import importlib
from datetime import date
from pathlib import Path

from agents.pipeline.context import PipelineContext

REPO_ROOT = Path(__file__).resolve().parents[3]

LLM_REGISTRY: dict[str, str] = {
    "example": "agents.llm.example_agent.ExampleAgent",
}


def _save_artifacts(agent, output, prediction_date: date, config: dict) -> None:
    from agents.io import FileSaver, week_stem

    art = config.get("artifacts", {})
    if art.get("save_json", True):
        FileSaver.for_agent(agent.agent_type).save(
            agent.render_json(output, prediction_date),
            f"{week_stem(prediction_date)}.json",
        )
    if art.get("save_md", True):
        md = agent.render_md(output, prediction_date)
        md_path = REPO_ROOT / "data" / agent.agent_type
        FileSaver(md_path).save(md, f"{agent.agent_type}_agent_{week_stem(prediction_date)}.md")


def run_almanac(ctx: PipelineContext, config: dict) -> None:
    from agents.almanac.almanac_agent import AlmanacAgent

    agent = AlmanacAgent()
    output = agent.run(ctx.prediction_date)
    ctx.almanac = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_technical(ctx: PipelineContext, config: dict) -> None:
    from agents.technical.technical_agent import TechnicalAgent

    agent = TechnicalAgent()
    output = agent.run(ctx.prediction_date)
    ctx.technical = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_macro(ctx: PipelineContext, config: dict) -> None:
    from agents.macro.macro_agent import MacroAgent

    agent = MacroAgent()
    output = agent.run(ctx.prediction_date)
    ctx.macro = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_evidence(
    ctx: PipelineContext,
    config: dict,
    data_root: Path | None = None,
) -> None:
    from agents.evidence.evidence_agent import EvidenceAgent

    agent = EvidenceAgent(data_root=data_root)
    output = agent.run(ctx.prediction_date)
    ctx.evidence = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_llm(ctx: PipelineContext, config: dict, model_key: str) -> None:
    if model_key not in LLM_REGISTRY:
        raise ValueError(
            f"Unknown LLM model_key {model_key!r}. Known models: {list(LLM_REGISTRY)}"
        )
    class_path = LLM_REGISTRY[model_key]
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)
    agent = agent_class()

    prompt = agent.build_prompt(ctx.prediction_date, ctx)
    raw = agent.query(prompt)
    output = agent.parse_response(raw, ctx.prediction_date)
    ctx.llm_outputs.append(output)

    from agents.io import DATA_ROOT, FileSaver, week_stem

    art = config.get("artifacts", {})
    if art.get("save_json", True):
        saver = FileSaver(DATA_ROOT / "llm" / model_key)
        saver.save(
            agent.render_json(output, ctx.prediction_date),
            f"{week_stem(ctx.prediction_date)}_{model_key}.json",
        )
    if art.get("save_md", True):
        md_path = REPO_ROOT / "data" / "llm"
        FileSaver(md_path).save(
            agent.render_md(output, ctx.prediction_date),
            f"llm_agent_{week_stem(ctx.prediction_date)}_{model_key}.md",
        )
