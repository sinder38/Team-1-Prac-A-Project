# Proposition: Decouple LLMs from Agents

## Current Problem

`backend/agents/llm/` and `backend/agents/pipeline/` sit inside `agents/` alongside domain agents (Almanac, Technical, Macro, Evidence). But LLMs and the pipeline are fundamentally different — LLMs **consume** agent outputs, and the pipeline **orchestrates** them. They don't belong with the domain agents.

## Proposed Structure

```
backend/
├── core/                     # Shared modules (NEW)
│   ├── base.py               # BaseAgent ABC
│   ├── schemas.py            # All Pydantic models/enums
│   └── io.py                 # FileSaver, week_stem
│
├── llm/                      # LLM module (moved from agents/llm/)
│   ├── base.py               # BaseLLMAgent
│   ├── openrouter.py         # OpenRouterAgent
│   ├── comparison.py         # build_comparison_md, _row
│   └── example.py            # ExampleAgent template
│
├── pipeline/                 # Orchestrator (moved from agents/pipeline/)
│   ├── config.py             # PipelineConfig, LLMModelEntry
│   ├── context.py            # PipelineContext
│   └── stages.py             # run_almanac, run_llm, run_technical, etc.
│
├── agents/                   # Domain agents only — unchanged
│   ├── almanac/
│   ├── technical/
│   ├── macro/
│   └── evidence/
```

## What Moves

| From | To |
|------|-----|
| `agents/base.py` | `core/base.py` |
| `agents/schemas.py` | `core/schemas.py` |
| `agents/io.py` | `core/io.py` |
| `agents/llm/base_llm.py` | `llm/base.py` |
| `agents/llm/multi_model_runner.py` | `llm/openrouter.py` + `llm/comparison.py` |
| `agents/llm/example_agent.py` | `llm/example.py` |
| `agents/pipeline/config.py` | `pipeline/config.py` |
| `agents/pipeline/context.py` | `pipeline/context.py` |
| `agents/pipeline/stages.py` | `pipeline/stages.py` |

## Files Updated

- 6 test files — import paths corrected
- `run_pipeline.py` — import paths corrected
- `conftest.py` — import paths corrected
- All domain agent files (almanac, technical, macro, evidence) — import paths corrected
- Server files (`server/artifacts.py`, `server/stages.py`) — import paths corrected

## Verification

All 66 tests pass with the new structure. The old files in `agents/llm/` and `agents/pipeline/` still exist as fallback copies with updated imports — ready to delete once the team confirms.

## Next Steps After Approval

1. Delete old `agents/llm/` directory
2. Delete old `agents/pipeline/` directory  
3. Remove `agents/base.py`, `agents/schemas.py`, `agents/io.py` (moved to core/)
