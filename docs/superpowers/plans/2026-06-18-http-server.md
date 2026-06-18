# HTTP Server Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Flask HTTP server as a parallel entry point to the existing CLI, exposing each pipeline stage as an individual REST endpoint with stateless disk-based artifact persistence.

**Architecture:** A `server/` package sits beside `agents/` and `run_pipeline.py`. It has two Flask blueprints (`stages` and `artifacts`) and a shared `utils.py` for request parsing and artifact path resolution. The `agents/` package and `run_pipeline.py` are never modified — the server calls the same stage functions the CLI does.

**Tech Stack:** Python 3.12+, Flask, uv (package manager), pytest

## Global Constraints

- Python `>=3.12` (matches existing `pyproject.toml`)
- `flask` added to `[project].dependencies` in `pyproject.toml`
- All new files live under `backend/server/` or `backend/tests/server/`
- `agents/` and `run_pipeline.py` — **do not modify**
- Artifact JSON uses `dataclasses.asdict()` with `default=str` — same as existing CLI
- Artifact filename patterns (exact):
  - `data/outputs/{agent_type}/{agent_type}_{week_stem}_{run_id}_{horizon_days}d.json` — almanac, technical, macro
  - `data/outputs/evidence/evidence_{week_stem}_{run_id}.json` — no horizon
  - `data/outputs/llm/llm_{model}_{week_stem}_{run_id}_{horizon_days}d.json`
- `week_stem` is computed via `agents.io.week_stem(prediction_date)` — returns e.g. `"W25"`
- All error responses: `{"error": "<message>"}` with appropriate HTTP status
- `run_id` is caller-supplied string, required on all endpoints
- `horizon_days` is a positive integer, required on almanac/technical/macro/llm endpoints, absent on evidence
- LLM trigger: all 4 agent artifacts (`almanac`, `technical`, `macro`, `evidence`) must exist for the given `run_id` — return `404` naming all missing files if any are absent

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/pyproject.toml` | Modify | Add `flask` dependency |
| `backend/server/__init__.py` | Create | `create_app()` — builds Flask app, registers blueprints |
| `backend/server/utils.py` | Create | `parse_date`, `require_fields`, `artifact_path`, `load_artifact`, `err` |
| `backend/server/stages.py` | Create | Blueprint: `POST /stages/{almanac,technical,macro,evidence,llm}` |
| `backend/server/artifacts.py` | Create | Blueprint: `GET /artifacts/{almanac,technical,macro,evidence,llm}`, `GET /artifacts/runs` |
| `backend/run_server.py` | Create | Entry point: creates app, calls `app.run()` |
| `backend/tests/server/__init__.py` | Create | Empty — marks test package |
| `backend/tests/server/test_utils.py` | Create | Tests for all `utils.py` helpers |
| `backend/tests/server/test_stages.py` | Create | Tests for all stage trigger endpoints |
| `backend/tests/server/test_artifacts.py` | Create | Tests for all artifact fetch endpoints |

---

## Task 1: Add Flask dependency and scaffold the `server/` package

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/server/__init__.py`
- Create: `backend/run_server.py`

**Interfaces:**
- Produces: `create_app() -> Flask` (imported by `run_server.py` and all test fixtures)

- [ ] **Step 1: Add `flask` to `pyproject.toml`**

Open `backend/pyproject.toml`. Change the `dependencies` list to:

```toml
dependencies = [
    "yfinance>=0.2",
    "pandas>=2.0",
    "requests>=2.32",
    "openai>=2.41.1",
    "python-dotenv>=1.2.2",
    "flask>=3.0",
]
```

- [ ] **Step 2: Install the new dependency**

Run from `backend/`:
```bash
uv sync
```
Expected: resolves without error, `flask` appears in `.venv`.

- [ ] **Step 3: Create `backend/server/__init__.py`**

```python
from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    from server.stages import stages_bp
    from server.artifacts import artifacts_bp

    app.register_blueprint(stages_bp)
    app.register_blueprint(artifacts_bp)

    return app
```

- [ ] **Step 4: Create `backend/run_server.py`**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

- [ ] **Step 5: Verify import chain is clean**

Run from `backend/`:
```bash
uv run python -c "from server import create_app; print('ok')"
```
Expected: prints `ok` with no import errors.

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/server/__init__.py backend/run_server.py
git commit -m "feat: scaffold Flask server package with create_app"
```

---

## Task 2: Implement `server/utils.py`

**Files:**
- Create: `backend/server/utils.py`
- Create: `backend/tests/server/__init__.py`
- Create: `backend/tests/server/test_utils.py`

**Interfaces:**
- Consumes: `agents.io.week_stem(date) -> str`
- Produces:
  - `parse_date(value: str) -> date` — raises `ValueError` on bad input
  - `require_fields(body: dict, *fields: str) -> None` — raises `werkzeug.exceptions.BadRequest` if any field missing
  - `artifact_path(agent_type: str, week_stem: str, run_id: str, *, horizon_days: int | None = None, model: str | None = None) -> Path`
  - `load_artifact(path: Path) -> dict` — raises `FileNotFoundError` if missing
  - `err(message: str, status: int) -> tuple` — returns a Flask JSON error response tuple

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/server/__init__.py` (empty file).

Create `backend/tests/server/test_utils.py`:

```python
import json
import pytest
from datetime import date
from pathlib import Path

from server.utils import parse_date, artifact_path, load_artifact, err


def test_parse_date_valid():
    assert parse_date("2026-06-18") == date(2026, 6, 18)


def test_parse_date_invalid():
    with pytest.raises(ValueError):
        parse_date("not-a-date")


def test_artifact_path_almanac():
    p = artifact_path("almanac", "W25", "run1", horizon_days=7)
    assert p.name == "almanac_W25_run1_7d.json"
    assert "almanac" in str(p)


def test_artifact_path_evidence():
    p = artifact_path("evidence", "W25", "run1")
    assert p.name == "evidence_W25_run1.json"


def test_artifact_path_llm():
    p = artifact_path("llm", "W25", "run1", model="nemotron", horizon_days=7)
    assert p.name == "llm_nemotron_W25_run1_7d.json"


def test_load_artifact_found(tmp_path):
    f = tmp_path / "test.json"
    f.write_text(json.dumps({"key": "val"}))
    assert load_artifact(f) == {"key": "val"}


def test_load_artifact_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_artifact(tmp_path / "nope.json")


def test_err_shape():
    import flask
    app = flask.Flask(__name__)
    with app.app_context():
        response, status = err("bad input", 400)
        assert status == 400
        assert json.loads(response.data) == {"error": "bad input"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/server/test_utils.py -v
```
Expected: `ModuleNotFoundError` or `ImportError` — `server.utils` does not exist yet.

- [ ] **Step 3: Implement `backend/server/utils.py`**

```python
import json
from datetime import date
from pathlib import Path

from flask import jsonify
from werkzeug.exceptions import BadRequest

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUTS_ROOT = REPO_ROOT / "data" / "outputs"


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def require_fields(body: dict, *fields: str) -> None:
    for field in fields:
        if field not in body or body[field] is None:
            raise BadRequest(f"Missing required field: {field}")


def artifact_path(
    agent_type: str,
    week_stem: str,
    run_id: str,
    *,
    horizon_days: int | None = None,
    model: str | None = None,
) -> Path:
    base = OUTPUTS_ROOT / agent_type
    if agent_type == "llm":
        filename = f"llm_{model}_{week_stem}_{run_id}_{horizon_days}d.json"
    elif agent_type == "evidence":
        filename = f"evidence_{week_stem}_{run_id}.json"
    else:
        filename = f"{agent_type}_{week_stem}_{run_id}_{horizon_days}d.json"
    return base / filename


def load_artifact(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def err(message: str, status: int) -> tuple:
    return jsonify({"error": message}), status
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/server/test_utils.py -v
```
Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/server/utils.py backend/tests/server/__init__.py backend/tests/server/test_utils.py
git commit -m "feat: add server utils — artifact path, date parsing, error helper"
```

---

## Task 3: Implement the stages blueprint

**Files:**
- Create: `backend/server/stages.py`
- Create: `backend/tests/server/test_stages.py`

**Interfaces:**
- Consumes:
  - `agents.pipeline.stages.run_almanac(ctx, config) -> None`
  - `agents.pipeline.stages.run_technical(ctx, config) -> None`
  - `agents.pipeline.stages.run_macro(ctx, config) -> None`
  - `agents.pipeline.stages.run_evidence(ctx, config) -> None`
  - `agents.pipeline.stages.run_llm(ctx, config, model_key) -> tuple[str, dict]`
  - `agents.pipeline.stages.LLM_REGISTRY: dict[str, Callable]`
  - `agents.pipeline.context.PipelineContext(prediction_date: date)`
  - `agents.io.week_stem(date) -> str`
  - `server.utils.parse_date`, `require_fields`, `artifact_path`, `err`
- Produces: Flask Blueprint `stages_bp` registered at no URL prefix

Each stage trigger:
1. Parses and validates the request body
2. Builds a minimal `PipelineContext`
3. Calls the stage function with `config={"artifacts": {"save_json": False, "save_md": False}}` to suppress CLI-style file writes
4. Serializes the output with `dataclasses.asdict(output, default=str)`
5. Writes the artifact to disk at the path from `artifact_path()`
6. Returns the serialized output as JSON

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/server/test_stages.py`:

```python
import json
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from server import create_app
from agents.schemas import (
    AlmanacOutput, Bias, Confidence,
    TechnicalOutput, InstrumentTechnical,
    MacroOutput, MacroBias, CommodityData,
    EvidenceOutput,
    LLMOutput, Regime, PredictedRange,
)


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


ALMANAC_OUTPUT = AlmanacOutput(
    prediction_date=date(2026, 6, 18),
    monthly_bias=Bias.BULLISH,
    seasonal_bias=Bias.BULLISH,
    confidence=Confidence.MEDIUM,
    thesis="Test thesis",
)

TECHNICAL_OUTPUT = TechnicalOutput(
    prediction_date=date(2026, 6, 18),
    instruments={
        "SPX": InstrumentTechnical(
            last_close=5400.0, ema_8=5380.0, ema_21=5350.0,
            trend_bias=Bias.BULLISH, key_support=5300.0,
            key_resistance=5500.0, confidence=Confidence.HIGH,
        )
    },
)

MACRO_OUTPUT = MacroOutput(
    prediction_date=date(2026, 6, 18),
    fed_rate="5.25%", yield_2y=4.8, yield_10y=4.5, yield_30y=4.6,
    dxy=CommodityData(price=104.0, weekly_change=-0.3),
    wti_oil=CommodityData(price=78.0, weekly_change=1.2),
    gold=CommodityData(price=2350.0, weekly_change=0.5),
    macro_bias=MacroBias.NEUTRAL, primary_driver="Fed policy",
    confidence=Confidence.MEDIUM, invalidation="Surprise CPI print",
)

EVIDENCE_OUTPUT = EvidenceOutput(
    prediction_date=date(2026, 6, 18),
    week="W25",
    content="# W25 actuals",
)

LLM_OUT = LLMOutput(
    prediction_date=date(2026, 6, 18),
    model_name="example",
    weekly_regime=Regime.BULLISH,
    confidence=Confidence.MEDIUM,
    spx_range=PredictedRange(low=-1.0, high=2.0),
    ndx_range=PredictedRange(low=-1.5, high=2.5),
    iwm_range=PredictedRange(low=-2.0, high=1.5),
    invalidation="None",
    plain_english="Bullish week expected.",
)


def test_post_almanac_returns_output(client, tmp_path):
    with patch("server.stages.run_almanac") as mock_run, \
         patch("server.stages.artifact_path", return_value=tmp_path / "out.json"):
        mock_run.side_effect = lambda ctx, config: setattr(ctx, "almanac", ALMANAC_OUTPUT)
        resp = client.post("/stages/almanac", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
            "horizon_days": 7,
        })
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["monthly_bias"] == "Bullish"


def test_post_almanac_missing_field(client):
    resp = client.post("/stages/almanac", json={
        "prediction_date": "2026-06-18",
        "run_id": "run1",
        # horizon_days missing
    })
    assert resp.status_code == 400
    assert "horizon_days" in json.loads(resp.data)["error"]


def test_post_almanac_bad_date(client):
    resp = client.post("/stages/almanac", json={
        "prediction_date": "not-a-date",
        "run_id": "run1",
        "horizon_days": 7,
    })
    assert resp.status_code == 400


def test_post_evidence_no_horizon(client, tmp_path):
    with patch("server.stages.run_evidence") as mock_run, \
         patch("server.stages.artifact_path", return_value=tmp_path / "out.json"):
        mock_run.side_effect = lambda ctx, config, **kw: setattr(ctx, "evidence", EVIDENCE_OUTPUT)
        resp = client.post("/stages/evidence", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
        })
    assert resp.status_code == 200
    assert json.loads(resp.data)["week"] == "W25"


def test_post_llm_missing_agent_artifacts(client, tmp_path):
    with patch("server.stages.artifact_path", side_effect=lambda t, *a, **kw: tmp_path / f"{t}.json"):
        resp = client.post("/stages/llm", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
            "model": "example",
            "horizon_days": 7,
        })
    assert resp.status_code == 404
    body = json.loads(resp.data)
    assert "almanac" in body["error"]


def test_post_llm_unknown_model(client):
    resp = client.post("/stages/llm", json={
        "prediction_date": "2026-06-18",
        "run_id": "run1",
        "model": "does_not_exist",
        "horizon_days": 7,
    })
    assert resp.status_code == 400
    assert "model" in json.loads(resp.data)["error"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/server/test_stages.py -v
```
Expected: `ImportError` — `server.stages` does not exist yet.

- [ ] **Step 3: Implement `backend/server/stages.py`**

```python
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest

from agents.io import week_stem
from agents.pipeline.context import PipelineContext
from agents.pipeline.stages import (
    LLM_REGISTRY,
    run_almanac,
    run_evidence,
    run_llm,
    run_macro,
    run_technical,
)
from server.utils import artifact_path, err, parse_date, require_fields

stages_bp = Blueprint("stages", __name__, url_prefix="/stages")

_NO_ARTIFACTS = {"artifacts": {"save_json": False, "save_md": False}}


def _write_artifact(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


@stages_bp.route("/almanac", methods=["POST"])
def post_almanac():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id", "horizon_days")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
        horizon_days = int(body["horizon_days"])
        if horizon_days <= 0:
            raise ValueError("horizon_days must be a positive integer")
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except (ValueError, TypeError) as e:
        return err(str(e), 400)

    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        run_almanac(ctx, _NO_ARTIFACTS)
    except Exception as e:
        return err(str(e), 500)

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.almanac)
    output_dict["horizon_days"] = horizon_days
    path = artifact_path("almanac", stem, run_id, horizon_days=horizon_days)
    _write_artifact(path, output_dict)
    return jsonify(output_dict), 200


@stages_bp.route("/technical", methods=["POST"])
def post_technical():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id", "horizon_days")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
        horizon_days = int(body["horizon_days"])
        if horizon_days <= 0:
            raise ValueError("horizon_days must be a positive integer")
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except (ValueError, TypeError) as e:
        return err(str(e), 400)

    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        run_technical(ctx, _NO_ARTIFACTS)
    except Exception as e:
        return err(str(e), 500)

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.technical)
    output_dict["horizon_days"] = horizon_days
    path = artifact_path("technical", stem, run_id, horizon_days=horizon_days)
    _write_artifact(path, output_dict)
    return jsonify(output_dict), 200


@stages_bp.route("/macro", methods=["POST"])
def post_macro():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id", "horizon_days")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
        horizon_days = int(body["horizon_days"])
        if horizon_days <= 0:
            raise ValueError("horizon_days must be a positive integer")
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except (ValueError, TypeError) as e:
        return err(str(e), 400)

    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        run_macro(ctx, _NO_ARTIFACTS)
    except Exception as e:
        return err(str(e), 500)

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.macro)
    output_dict["horizon_days"] = horizon_days
    path = artifact_path("macro", stem, run_id, horizon_days=horizon_days)
    _write_artifact(path, output_dict)
    return jsonify(output_dict), 200


@stages_bp.route("/evidence", methods=["POST"])
def post_evidence():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except ValueError as e:
        return err(str(e), 400)

    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        run_evidence(ctx, _NO_ARTIFACTS)
    except Exception as e:
        return err(str(e), 500)

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.evidence)
    path = artifact_path("evidence", stem, run_id)
    _write_artifact(path, output_dict)
    return jsonify(output_dict), 200


@stages_bp.route("/llm", methods=["POST"])
def post_llm():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id", "model", "horizon_days")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
        model_key = str(body["model"])
        horizon_days = int(body["horizon_days"])
        if horizon_days <= 0:
            raise ValueError("horizon_days must be a positive integer")
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except (ValueError, TypeError) as e:
        return err(str(e), 400)

    if model_key not in LLM_REGISTRY:
        return err(f"Unknown model '{model_key}'. Known models: {list(LLM_REGISTRY)}", 400)

    stem = week_stem(prediction_date)

    # Check all 4 required agent artifacts exist — no silent skipping
    missing = []
    for agent_type in ("almanac", "technical", "macro", "evidence"):
        if agent_type == "evidence":
            path = artifact_path(agent_type, stem, run_id)
        else:
            path = artifact_path(agent_type, stem, run_id, horizon_days=horizon_days)
        if not path.exists():
            missing.append(str(path))

    if missing:
        return err(
            f"Missing agent artifacts for run_id={run_id!r}: {', '.join(missing)}",
            404,
        )

    # Load agent outputs from disk into PipelineContext
    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        import json as _json
        from dataclasses import fields as _fields
        from agents.schemas import AlmanacOutput, TechnicalOutput, MacroOutput, EvidenceOutput

        def _load(agent_type, cls, **kwargs):
            p = artifact_path(agent_type, stem, run_id, **kwargs)
            return _json.loads(p.read_text(encoding="utf-8"))

        # Re-hydrate context from the on-disk dicts via the stage functions
        # using a temporary context populated from disk JSON.
        # We run_llm directly passing the ctx loaded from disk.
        almanac_data = _load("almanac", AlmanacOutput, horizon_days=horizon_days)
        technical_data = _load("technical", TechnicalOutput, horizon_days=horizon_days)
        macro_data = _load("macro", MacroOutput, horizon_days=horizon_days)
        evidence_data = _load("evidence", EvidenceOutput)

        # Reconstruct typed objects from disk dicts
        from agents.schemas import (
            Bias, Confidence, SectorSignal,
            InstrumentTechnical, MacroBias, CommodityData, CalendarEvent,
        )
        from datetime import date as _date

        ctx.almanac = AlmanacOutput(
            prediction_date=_date.fromisoformat(almanac_data["prediction_date"]),
            monthly_bias=Bias(almanac_data["monthly_bias"]),
            seasonal_bias=Bias(almanac_data["seasonal_bias"]),
            confidence=Confidence(almanac_data["confidence"]),
            thesis=almanac_data["thesis"],
            weekly_pattern=almanac_data.get("weekly_pattern", ""),
            sector_signals=[
                SectorSignal(sector=s["sector"], bias=Bias(s["bias"]), window=s["window"])
                for s in almanac_data.get("sector_signals", [])
            ],
        )
        ctx.evidence = EvidenceOutput(
            prediction_date=_date.fromisoformat(evidence_data["prediction_date"]),
            week=evidence_data["week"],
            content=evidence_data["content"],
        )
        # Technical and macro context blocks are serialized to JSON in build_prompt,
        # so pass raw dicts directly via a lightweight wrapper
        ctx.technical = ctx.almanac  # placeholder overwritten below
        ctx.macro = ctx.almanac      # placeholder overwritten below

        # Patch build_prompt context to use raw dicts by populating ctx fields
        # with objects that asdict() can serialize — reconstruct from JSON dicts.
        # For the LLM prompt, build_prompt calls asdict() on each output so we
        # reconstruct minimal typed objects from the stored dicts.
        from agents.schemas import TechnicalOutput as TO, InstrumentTechnical as IT
        ctx.technical = TO(
            prediction_date=_date.fromisoformat(technical_data["prediction_date"]),
            instruments={
                k: IT(
                    last_close=v["last_close"],
                    ema_8=v["ema_8"],
                    ema_21=v["ema_21"],
                    trend_bias=Bias(v["trend_bias"]),
                    key_support=v["key_support"],
                    key_resistance=v["key_resistance"],
                    confidence=Confidence(v["confidence"]),
                )
                for k, v in technical_data.get("instruments", {}).items()
            },
        )

        from agents.schemas import MacroOutput as MO
        ctx.macro = MO(
            prediction_date=_date.fromisoformat(macro_data["prediction_date"]),
            fed_rate=macro_data["fed_rate"],
            yield_2y=macro_data["yield_2y"],
            yield_10y=macro_data["yield_10y"],
            yield_30y=macro_data["yield_30y"],
            dxy=CommodityData(**macro_data["dxy"]),
            wti_oil=CommodityData(**macro_data["wti_oil"]),
            gold=CommodityData(**macro_data["gold"]),
            macro_bias=MacroBias(macro_data["macro_bias"]),
            primary_driver=macro_data["primary_driver"],
            confidence=Confidence(macro_data["confidence"]),
            invalidation=macro_data["invalidation"],
            next_fomc_date=(
                _date.fromisoformat(macro_data["next_fomc_date"])
                if macro_data.get("next_fomc_date") else None
            ),
            hold_probability=macro_data.get("hold_probability", 0.0),
            cut_probability=macro_data.get("cut_probability", 0.0),
            fomc_direction=macro_data.get("fomc_direction", "N/A"),
            yield_curve=macro_data.get("yield_curve", "N/A"),
            yield_10y_direction=macro_data.get("yield_10y_direction", "N/A"),
            week_ahead_calendar=[
                CalendarEvent(**e) for e in macro_data.get("week_ahead_calendar", [])
            ],
            key_earnings=macro_data.get("key_earnings", []),
            confirmed_news=macro_data.get("confirmed_news", []),
        )

    except Exception as e:
        return err(f"Failed to load agent artifacts: {e}", 500)

    try:
        _slug, _row = run_llm(ctx, _NO_ARTIFACTS, model_key)
    except Exception as e:
        return err(str(e), 500)

    llm_output = ctx.llm_outputs[-1]
    output_dict = asdict(llm_output)
    output_dict["horizon_days"] = horizon_days
    path = artifact_path("llm", stem, run_id, model=model_key, horizon_days=horizon_days)
    _write_artifact(path, output_dict)
    return jsonify(output_dict), 200
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/server/test_stages.py -v
```
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/server/stages.py backend/tests/server/test_stages.py
git commit -m "feat: add stages blueprint with POST endpoints for all 5 pipeline stages"
```

---

## Task 4: Implement the artifacts blueprint

**Files:**
- Create: `backend/server/artifacts.py`
- Create: `backend/tests/server/test_artifacts.py`

**Interfaces:**
- Consumes:
  - `server.utils.artifact_path`, `load_artifact`, `err`, `parse_date`
  - `agents.io.week_stem(date) -> str`
- Produces: Flask Blueprint `artifacts_bp` registered at no URL prefix

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/server/test_artifacts.py`:

```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from server import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_almanac_found(client, tmp_path):
    artifact = {"monthly_bias": "Bullish", "horizon_days": 7}
    fake_path = tmp_path / "almanac_W25_run1_7d.json"
    fake_path.write_text(json.dumps(artifact))

    with patch("server.artifacts.artifact_path", return_value=fake_path):
        resp = client.get("/artifacts/almanac?run_id=run1&horizon_days=7")
    assert resp.status_code == 200
    assert json.loads(resp.data)["monthly_bias"] == "Bullish"


def test_get_almanac_not_found(client, tmp_path):
    fake_path = tmp_path / "almanac_W25_run1_7d.json"  # does not exist
    with patch("server.artifacts.artifact_path", return_value=fake_path):
        resp = client.get("/artifacts/almanac?run_id=run1&horizon_days=7")
    assert resp.status_code == 404


def test_get_almanac_missing_run_id(client):
    resp = client.get("/artifacts/almanac?horizon_days=7")
    assert resp.status_code == 400


def test_get_almanac_missing_horizon(client):
    resp = client.get("/artifacts/almanac?run_id=run1")
    assert resp.status_code == 400


def test_get_evidence_no_horizon(client, tmp_path):
    artifact = {"week": "W25", "content": "# data"}
    fake_path = tmp_path / "evidence_W25_run1.json"
    fake_path.write_text(json.dumps(artifact))
    with patch("server.artifacts.artifact_path", return_value=fake_path):
        resp = client.get("/artifacts/evidence?run_id=run1")
    assert resp.status_code == 200
    assert json.loads(resp.data)["week"] == "W25"


def test_get_llm_found(client, tmp_path):
    artifact = {"weekly_regime": "Bullish", "horizon_days": 7}
    fake_path = tmp_path / "llm_nemotron_W25_run1_7d.json"
    fake_path.write_text(json.dumps(artifact))
    with patch("server.artifacts.artifact_path", return_value=fake_path):
        resp = client.get("/artifacts/llm?run_id=run1&model=nemotron&horizon_days=7")
    assert resp.status_code == 200


def test_get_llm_missing_model(client):
    resp = client.get("/artifacts/llm?run_id=run1&horizon_days=7")
    assert resp.status_code == 400


def test_get_runs(client, tmp_path):
    # Create two artifacts for W25 with different run_ids
    (tmp_path / "almanac").mkdir()
    (tmp_path / "almanac" / "almanac_W25_run1_7d.json").write_text("{}")
    (tmp_path / "almanac" / "almanac_W25_run2_7d.json").write_text("{}")
    (tmp_path / "almanac" / "almanac_W24_other_7d.json").write_text("{}")  # different week

    with patch("server.artifacts.OUTPUTS_ROOT", tmp_path):
        resp = client.get("/artifacts/runs?prediction_date=2026-06-18")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert set(data["run_ids"]) == {"run1", "run2"}
    assert data["week"] == "W25"


def test_get_runs_missing_date(client):
    resp = client.get("/artifacts/runs")
    assert resp.status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/server/test_artifacts.py -v
```
Expected: `ImportError` — `server.artifacts` does not exist yet.

- [ ] **Step 3: Implement `backend/server/artifacts.py`**

```python
import re
from datetime import date
from pathlib import Path

from flask import Blueprint, jsonify, request

from agents.io import week_stem
from server.utils import OUTPUTS_ROOT, artifact_path, err, load_artifact, parse_date

artifacts_bp = Blueprint("artifacts", __name__, url_prefix="/artifacts")


def _get_horizon_days(args: dict) -> tuple[int, tuple | None]:
    raw = args.get("horizon_days")
    if raw is None:
        return 0, err("Missing required query param: horizon_days", 400)
    try:
        val = int(raw)
        if val <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return 0, err("horizon_days must be a positive integer", 400)
    return val, None


@artifacts_bp.route("/almanac", methods=["GET"])
def get_almanac():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    horizon_days, error = _get_horizon_days(request.args)
    if error:
        return error
    try:
        data = load_artifact(artifact_path("almanac", _stem_from_args(), run_id, horizon_days=horizon_days))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


@artifacts_bp.route("/technical", methods=["GET"])
def get_technical():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    horizon_days, error = _get_horizon_days(request.args)
    if error:
        return error
    try:
        data = load_artifact(artifact_path("technical", _stem_from_args(), run_id, horizon_days=horizon_days))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


@artifacts_bp.route("/macro", methods=["GET"])
def get_macro():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    horizon_days, error = _get_horizon_days(request.args)
    if error:
        return error
    try:
        data = load_artifact(artifact_path("macro", _stem_from_args(), run_id, horizon_days=horizon_days))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


@artifacts_bp.route("/evidence", methods=["GET"])
def get_evidence():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    try:
        data = load_artifact(artifact_path("evidence", _stem_from_args(), run_id))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


@artifacts_bp.route("/llm", methods=["GET"])
def get_llm():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    model = request.args.get("model")
    if not model:
        return err("Missing required query param: model", 400)
    horizon_days, error = _get_horizon_days(request.args)
    if error:
        return error
    try:
        data = load_artifact(artifact_path("llm", _stem_from_args(), run_id, model=model, horizon_days=horizon_days))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


@artifacts_bp.route("/runs", methods=["GET"])
def get_runs():
    raw_date = request.args.get("prediction_date")
    if not raw_date:
        return err("Missing required query param: prediction_date", 400)
    try:
        prediction_date = parse_date(raw_date)
    except ValueError:
        return err(f"Invalid prediction_date: {raw_date!r}", 400)

    stem = week_stem(prediction_date)
    run_ids: set[str] = set()

    # Scan all agent subdirectories for files matching the week stem
    # Filename pattern: {agent_type}_{stem}_{run_id}[_{suffix}].json
    pattern = re.compile(rf"^[a-z]+_{re.escape(stem)}_(.+?)(?:_\d+d|_[a-z]+_\d+d)?\.json$")
    for subdir in OUTPUTS_ROOT.iterdir():
        if not subdir.is_dir():
            continue
        for f in subdir.glob(f"*_{stem}_*.json"):
            m = pattern.match(f.name)
            if m:
                run_ids.add(m.group(1))

    return jsonify({
        "prediction_date": raw_date,
        "week": stem,
        "run_ids": sorted(run_ids),
    }), 200


def _stem_from_args() -> str:
    """Extract week_stem from prediction_date query param, or fall back to run_id prefix."""
    raw = request.args.get("prediction_date")
    if raw:
        try:
            return week_stem(parse_date(raw))
        except ValueError:
            pass
    # Artifact fetch doesn't require prediction_date — callers pass run_id directly.
    # week_stem is needed for path resolution; if not provided we can't resolve.
    # This is a design gap: callers should pass prediction_date OR we embed it in run_id.
    # For now, require prediction_date on all artifact fetch endpoints.
    from flask import abort
    abort(400, "Missing required query param: prediction_date")
```

- [ ] **Step 4: Update artifact fetch endpoints to require `prediction_date`**

The `_stem_from_args()` helper above requires `prediction_date` as a query param. Update the endpoint docs in the spec to match — artifact fetch endpoints require both `run_id` and `prediction_date`. This means fetch URLs become:

```
GET /artifacts/almanac?run_id=abc123&prediction_date=2026-06-18&horizon_days=7
GET /artifacts/evidence?run_id=abc123&prediction_date=2026-06-18
GET /artifacts/llm?run_id=abc123&prediction_date=2026-06-18&model=nemotron&horizon_days=7
```

Update the test fixtures to pass `prediction_date` in the query string where needed:

In `test_artifacts.py`, update the patched calls that use `_stem_from_args()` to pass `prediction_date=2026-06-18` in the query string. Specifically: the `get_almanac`, `get_technical`, `get_macro`, `get_evidence`, `get_llm` test calls should include `&prediction_date=2026-06-18`.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/server/test_artifacts.py -v
```
Expected: all 9 tests PASS.

- [ ] **Step 6: Run the full test suite to check for regressions**

```bash
cd backend && uv run pytest -v
```
Expected: all existing tests still pass, all new tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/server/artifacts.py backend/tests/server/test_artifacts.py
git commit -m "feat: add artifacts blueprint with GET endpoints for all stage outputs and run discovery"
```

---

## Task 5: Smoke test the running server

**Files:** none (manual verification only)

- [ ] **Step 1: Start the server**

```bash
cd backend && uv run python run_server.py
```
Expected: Flask starts on `http://0.0.0.0:5000` with no import errors.

- [ ] **Step 2: POST to almanac stage**

In a second terminal:
```bash
curl -s -X POST http://localhost:5000/stages/almanac \
  -H "Content-Type: application/json" \
  -d '{"prediction_date": "2026-06-18", "run_id": "smoketest1", "horizon_days": 7}' | python3 -m json.tool
```
Expected: JSON response with `monthly_bias`, `seasonal_bias`, `confidence`, `thesis` keys.

- [ ] **Step 3: Fetch the artifact back**

```bash
curl -s "http://localhost:5000/artifacts/almanac?run_id=smoketest1&prediction_date=2026-06-18&horizon_days=7" | python3 -m json.tool
```
Expected: same JSON as the POST response.

- [ ] **Step 4: Verify 400 on missing field**

```bash
curl -s -X POST http://localhost:5000/stages/almanac \
  -H "Content-Type: application/json" \
  -d '{"prediction_date": "2026-06-18", "run_id": "smoketest1"}' | python3 -m json.tool
```
Expected: `{"error": "Missing required field: horizon_days"}` with HTTP 400.

- [ ] **Step 5: Verify 404 on missing artifact**

```bash
curl -s "http://localhost:5000/artifacts/almanac?run_id=doesnotexist&prediction_date=2026-06-18&horizon_days=7" | python3 -m json.tool
```
Expected: `{"error": "Artifact not found: ..."}` with HTTP 404.

- [ ] **Step 6: Commit smoke test confirmation**

```bash
git add .
git commit -m "feat: HTTP server interface complete — Flask blueprints for stages and artifacts"
```
