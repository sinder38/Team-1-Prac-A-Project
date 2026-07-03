"""Pipeline stage functions — one per agent type."""

from datetime import date
from pathlib import Path
from typing import Callable

from agents.pipeline.context import PipelineContext
from agents.llm.base_llm import BaseLLMAgent

REPO_ROOT = Path(__file__).resolve().parents[3]

def _make_openrouter(model_name: str, model_id: str):
    from agents.llm.multi_model_runner import OpenRouterAgent
    return OpenRouterAgent(model_name=model_name, model_id=model_id)


# Registry maps model_key/slug → zero-arg callable returning a BaseLLMAgent instance.
# Slugs must match multi_model_runner.MODELS[*]["slug"].
LLM_REGISTRY: dict[str, Callable[[], BaseLLMAgent]] = {
    "example":  lambda: __import__("agents.llm.example_agent", fromlist=["ExampleAgent"]).ExampleAgent(),
    "nemotron": lambda: _make_openrouter("NVIDIA Nemotron 3 Super", "nvidia/nemotron-3-super-120b-a12b:free"),
    "gptoss":   lambda: _make_openrouter("OpenAI gpt-oss-120b",     "openai/gpt-oss-120b:free"),
    "gemma":    lambda: _make_openrouter("Google Gemma 4 31B",       "google/gemma-4-31b-it:free"),
    "laguna":   lambda: _make_openrouter("Poolside Laguna M.1",      "poolside/laguna-m.1:free"),
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
        if agent.agent_type == "evidence":
            filename = f"actuals_{week_stem(prediction_date)}.md"
        else:
            filename = f"{agent.agent_type}_agent_{week_stem(prediction_date)}.md"
        FileSaver(md_path).save(md, filename)


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
    market_data_provider=None,
    yield_data_provider=None,
    chart_provider=None,
) -> None:
    from agents.evidence.evidence_agent import EvidenceAgent

    agent = EvidenceAgent(
        data_root=data_root,
        market_data_provider=market_data_provider,
        yield_data_provider=yield_data_provider,
        chart_provider=chart_provider,
    )
    output = agent.run(ctx.prediction_date)
    ctx.evidence = output
    _save_artifacts(agent, output, ctx.prediction_date, config)


def run_llm(ctx: PipelineContext, config: dict, model_key: str) -> tuple[str, dict]:
    """Run one LLM model. Returns (slug, row_dict) for the comparison table."""
    from agents.llm.multi_model_runner import _row
    from agents.io import FileSaver, week_stem

    if model_key not in LLM_REGISTRY:
        raise ValueError(
            f"Unknown LLM model_key {model_key!r}. Known models: {list(LLM_REGISTRY)}"
        )
    agent = LLM_REGISTRY[model_key]()

    prompt = agent.build_prompt(ctx.prediction_date, ctx)
    raw = agent.query(prompt)
    output = agent.parse_response(raw, ctx.prediction_date)
    ctx.llm_outputs.append(output)

    art = config.get("artifacts", {})

    if art.get("save_md", True):
        FileSaver(REPO_ROOT / "data" / "llm").save(
            agent.render_md(output, ctx.prediction_date),
            f"synthesis_{model_key}_{week_stem(ctx.prediction_date)}.txt",
        )

    return model_key, _row(output)