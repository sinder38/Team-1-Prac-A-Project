# HTTP Server Interface Design

**Date:** 2026-06-18
**Status:** Approved

## Overview

Add a Flask HTTP server as a parallel entry point to the existing CLI (`run_pipeline.py`). The server exposes the same pipeline stages as individual REST endpoints, allowing callers to trigger stages independently, pass data between them via disk-persisted artifacts, and fetch historical outputs by run ID. Nothing in `agents/` or `run_pipeline.py` is changed.

---

## Architecture

```
backend/
├── run_pipeline.py          # CLI entry point — unchanged
├── run_server.py            # new: HTTP entry point
├── pipeline.toml            # unchanged
├── agents/                  # unchanged
└── server/
    ├── __init__.py          # creates Flask app, registers blueprints
    ├── stages.py            # blueprint: POST /stages/{name}
    ├── artifacts.py         # blueprint: GET /artifacts/{name}
    └── utils.py             # shared: request parsing, artifact path resolution
```

The CLI and HTTP interfaces are independent entry points that share the same `agents/` internals. Neither knows about the other.

---

## State Model

The server is **stateless**. All inter-stage state is persisted via JSON artifacts on disk. Each pipeline run is identified by a caller-supplied `run_id` (UUID or any opaque string). Artifacts are written and read using `run_id` as part of the filename, allowing multiple independent runs for the same prediction date.

Artifact filenames follow the pattern:
```
data/outputs/{agent_type}/{agent_type}_{week_stem}_{run_id}_{horizon_days}d.json  # almanac, technical, macro
data/outputs/evidence/evidence_{week_stem}_{run_id}.json                          # no horizon
data/outputs/llm/llm_{model}_{week_stem}_{run_id}_{horizon_days}d.json
```

---

## Run ID

- Supplied by the caller in every trigger request body as `"run_id"`.
- Must be present — 400 if missing.
- No server-side generation; callers are responsible for creating and tracking their own IDs.
- The same `run_id` must be used across all stage triggers that belong to one logical run, so the LLM stage can locate the 4 agent outputs.

---

## Horizon

- An integer representing the prediction time horizon in days: `7`, `30`, `90`, etc.
- Applicable to: **almanac**, **technical**, **macro**, and **llm** stages.
- Not applicable to: **evidence** (snapshot of current data, not forecast-scoped).
- For stages that accept it, `horizon_days` is required and must be a positive integer — 400 if missing or invalid.
- Stored in the artifact JSON under a `"horizon_days"` key and included in the artifact filename for almanac, technical, macro, and llm — allowing multiple horizon predictions within the same run to coexist on disk.

---

## Endpoints

### Stage Triggers

All trigger endpoints are synchronous — the response is returned when the stage completes. LLM calls may take 30+ seconds; callers are expected to handle this.

All return `Content-Type: application/json`.

---

#### `POST /stages/almanac`

Runs the almanac agent and writes the artifact to disk.

**Request body:**
```json
{
  "prediction_date": "2026-06-18",
  "run_id": "abc123",
  "horizon_days": 7
}
```

**Response `200`:** `AlmanacOutput` as JSON.

**Errors:**
- `400` — missing or invalid `prediction_date`, `run_id`, or `horizon`
- `500` — agent raised an exception (message included)

---

#### `POST /stages/technical`

Runs the technical agent and writes the artifact to disk.

**Request body:**
```json
{
  "prediction_date": "2026-06-18",
  "run_id": "abc123",
  "horizon_days": 7
}
```

**Response `200`:** `TechnicalOutput` as JSON.

**Errors:** same as almanac.

---

#### `POST /stages/macro`

Runs the macro agent and writes the artifact to disk.

**Request body:**
```json
{
  "prediction_date": "2026-06-18",
  "run_id": "abc123",
  "horizon_days": 7
}
```

**Response `200`:** `MacroOutput` as JSON.

**Errors:** same as almanac.

---

#### `POST /stages/evidence`

Runs the evidence agent and writes the artifact to disk. Does not accept `horizon`.

**Request body:**
```json
{
  "prediction_date": "2026-06-18",
  "run_id": "abc123"
}
```

**Response `200`:** `EvidenceOutput` as JSON.

**Errors:**
- `400` — missing or invalid `prediction_date` or `run_id`
- `500` — agent raised an exception

---

#### `POST /stages/llm`

Runs one LLM model. Requires all 4 agent artifacts for the given `run_id` to exist on disk — no silent skipping.

**Request body:**
```json
{
  "prediction_date": "2026-06-18",
  "run_id": "abc123",
  "model": "nemotron",
  "horizon_days": 7
}
```

- `model` must be a key in `LLM_REGISTRY`. Known values: `example`, `nemotron`, `gptoss`, `gemma`, `laguna`.
- `horizon` is required and included in the output artifact filename.

**Response `200`:** `LLMOutput` as JSON.

**Errors:**
- `400` — missing fields, unknown model
- `404` — one or more of the 4 required agent artifacts not found on disk (response body names which ones are missing)
- `500` — LLM call or parse raised an exception

---

### Artifact Fetch

All fetch endpoints accept query params and return the saved JSON artifact. Return `404` with a descriptive message if the artifact does not exist.

---

#### `GET /artifacts/almanac?run_id=abc123&horizon_days=7`
#### `GET /artifacts/technical?run_id=abc123&horizon_days=7`
#### `GET /artifacts/macro?run_id=abc123&horizon_days=7`
#### `GET /artifacts/evidence?run_id=abc123`

Returns the saved JSON for that stage and run. `horizon` is required for almanac, technical, and macro; not applicable for evidence.

**Errors:**
- `400` — missing `run_id`
- `404` — artifact not found

---

#### `GET /artifacts/llm?run_id=abc123&model=nemotron&horizon_days=7`

Returns the saved LLM output JSON for a specific run, model, and horizon.

**Errors:**
- `400` — missing `run_id`, `model`, or `horizon`
- `404` — artifact not found

---

#### `GET /artifacts/runs?prediction_date=2026-06-18`

Lists all `run_id`s that have any artifact on disk for the given prediction date week. Allows callers to discover existing runs before fetching.

**Response `200`:**
```json
{
  "prediction_date": "2026-06-18",
  "week": "W25",
  "run_ids": ["abc123", "def456"]
}
```

**Errors:**
- `400` — missing or invalid `prediction_date`

---

## Error Response Shape

All errors follow a consistent envelope:
```json
{
  "error": "Missing required field: run_id"
}
```

---

## File Layout: `server/utils.py`

Shared helpers used by both blueprints:

- `parse_date(value: str) -> date` — parses ISO date string, raises `ValueError` on bad input
- `require_fields(body: dict, *fields: str)` — raises `400` if any field is missing
- `artifact_path(agent_type, week_stem, run_id, **kwargs) -> Path` — resolves the artifact file path using the naming convention above
- `load_artifact(path: Path) -> dict` — reads and parses JSON, raises `FileNotFoundError` if missing

---

## `run_server.py`

Minimal entry point:
```python
from server import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

Invoke with: `uv run python run_server.py`

---

## Dependencies

Add `flask` to `pyproject.toml` dependencies. No other new dependencies.

---

## What Is Not Changing

- `agents/` — no modifications
- `run_pipeline.py` — no modifications
- `pipeline.toml` — not used by the HTTP server (config comes from request body)
- Artifact file format — JSON files written by the server use the same `asdict()` serialization as the CLI
