<div align="center">

<sub>CP3405 Design Thinking 3 &nbsp;·&nbsp; TR2 2026 &nbsp;·&nbsp; Singapore &nbsp;·&nbsp; Prof. Dr. Tan</sub>

# Market Intelligence — Team 1

<sub>A 10-week Scrum project for automated market analysis, multi-LLM collaboration, human review, and calibrated prediction.</sub>

<br>

![Status](https://img.shields.io/badge/status-active_development-3fb950?style=flat-square&labelColor=161b22)
![Progress](https://img.shields.io/badge/progress-Week_8-58a6ff?style=flat-square&labelColor=161b22)
![Assets](https://img.shields.io/badge/tracked_assets-9-d29922?style=flat-square&labelColor=161b22)
![LLMs](https://img.shields.io/badge/LLM_comparison-4-bc8cff?style=flat-square&labelColor=161b22)
![Backend](https://img.shields.io/badge/backend-Python_%7C_Flask-3776ab?style=flat-square&labelColor=161b22)
![Frontend](https://img.shields.io/badge/frontend-React_%7C_Vite-61dafb?style=flat-square&labelColor=161b22)

</div>

---

## Project Overview

Team 1 is building a repeatable market-intelligence system that combines market data, specialised analysis agents, four large language models, human judgement, and weekly calibration.

The project follows a continuous two-part feedback loop:

- **Look forward:** collect fresh data, run the agents, compare LLM reasoning, complete the Human Score, and lock the next SPX, NDX, and IWM prediction.
- **Look back:** compare the previous locked prediction with actual market results, calculate accuracy, and record lessons for the next sprint.

By Week 10, the repository should contain a transparent history of weekly predictions, evidence, LLM outputs, human decisions, actual results, calibration reports, and software increments.

---

## Current Development Status

> **Snapshot: Week 8 · 22 July 2026**  
> **Done** — implemented or usable &nbsp;·&nbsp; **Ongoing** — active integration or review &nbsp;·&nbsp; **Planned** — not yet implemented

| Component | Status | Current State |
|---|:---:|---|
| Structured weekly prediction workflow | Done | The team produces SPX, NDX, and IWM direction, percentage range, confidence, reasoning, and invalidation conditions. |
| Automated agent pipeline | Done | Almanac, Technical, Macro, and Evidence stages run through the Python pipeline. |
| Macro Agent automation | Done | News and macro inputs are collected automatically from the configured free data sources and transformed web data. |
| Evidence Agent and generated charts | Done | The pipeline fetches actual market data, creates evidence artefacts, and generates chart images. |
| Multi-LLM synthesis | Done | The automated CI pipeline compares Nemotron 3 Super, Tencent HY3, Gemma 4 26B A4B, and Laguna M.1 using identical evidence and synthesis prompts. |
| Flask backend API | Done | Stage execution, saved artefacts, market data, calibration data, Delta execution, and model configuration are exposed through backend routes. |
| React dashboard | Done | The dashboard provides pipeline controls, agent outputs, charts, LLM comparison, saved artefacts, market history, calibration, and review screens. |
| Live frontend–backend features | Done | Agent execution, Evidence, LLM synthesis, Delta evaluation, saved weeks, artefacts, market history, calibration results, and the server model registry use the Flask backend. |
| Demo-only or incomplete frontend features | Ongoing | Stage log descriptions are still generated locally, while Human Score submission and persistence remain under development. |
| Delta Engine | Done | Core prediction-versus-actual comparison, direction and range accuracy, error calculations, automated tests, backend execution, and dashboard access are available. |
| Human Score pipeline integration | Ongoing | The Human Score format and review screen exist, but automated submission, persistence, and full pipeline integration are still being completed. |
| Historical views and richer graphs | Ongoing | Saved-week and market-history features are available; further historical visualisation and interface refinement remain in progress. |
| Local LLM test provider | Done | `pipeline.toml` uses Ollama with `llama3.2:1b` for lightweight local development and testing without consuming OpenRouter limits. |
| CI, type checks, and tests | Done | GitHub Actions, Pyright, pytest, frontend build checks, and pull-request review are part of the development workflow. |

---

## Weekly Intelligence Cycle

Each sprint follows the same evidence-to-learning cycle:

1. **Select the prediction window** after the US market closes.
2. **Fetch market and economic data** for three target indices and six supporting assets.
3. **Run the analysis stages** for Almanac, Macro, Technical, and Evidence.
4. **Query the configured LLMs** — four OpenRouter models in automated CI runs, or the local Ollama model during lightweight development testing.
5. **Compare model outputs** to identify agreement, disagreement, missing evidence, and uncertainty.
6. **Apply human judgement** through the Human Score review.
7. **Lock the prediction** for SPX, NDX, and IWM.
8. **Publish the artefacts** through GitHub and the project interface.
9. **Evaluate the previous prediction** through the Delta Engine.
10. **Record calibration and learning** for the next sprint.

---

## The Nine Tracked Assets

The three equity indices are the prediction targets. The other six assets provide macroeconomic, volatility, and risk-sentiment context.

<table>
<thead>
<tr>
<th align="left">Asset</th>
<th align="left">Ticker</th>
<th align="left">Why We Track It</th>
</tr>
</thead>
<tbody>
<tr>
<td><b>S&amp;P 500</b></td>
<td><code>SPX</code></td>
<td>The main US equity benchmark and one of the three weekly prediction targets.</td>
</tr>
<tr>
<td><b>Nasdaq 100</b></td>
<td><code>NDX</code></td>
<td>A technology-heavy index that often reacts strongly to rates and risk sentiment.</td>
</tr>
<tr>
<td><b>Russell 2000 ETF</b></td>
<td><code>IWM</code></td>
<td>A small-cap proxy that is sensitive to financing conditions and domestic growth.</td>
</tr>
<tr>
<td><b>Gold Futures</b></td>
<td><code>GC</code></td>
<td>A safe-haven, inflation, currency, and market-fear signal.</td>
</tr>
<tr>
<td><b>Crude Oil Futures</b></td>
<td><code>CL</code></td>
<td>An inflation driver and a signal for global demand and geopolitical risk.</td>
</tr>
<tr>
<td><b>10-Year Treasury Futures</b></td>
<td><code>ZN</code></td>
<td>A rates and duration proxy that helps explain pressure on equity valuations.</td>
</tr>
<tr>
<td><b>Long-Term US Treasury ETF</b></td>
<td><code>TLT</code></td>
<td>A bond-market signal for growth expectations, rates, and risk-off behaviour.</td>
</tr>
<tr>
<td><b>CBOE Volatility Index</b></td>
<td><code>VIX</code></td>
<td>A widely used measure of expected equity-market volatility and investor fear.</td>
</tr>
<tr>
<td><b>Bitcoin</b></td>
<td><code>BTC</code></td>
<td>A continuously traded proxy for speculative risk appetite and liquidity sentiment.</td>
</tr>
</tbody>
</table>

---

## Analysis and Evidence Agents

The system contains **three analytical agents** and **one evidence agent**.

| Agent | Purpose | Main Outputs |
|---|---|---|
| **Almanac Agent** | Reviews seasonal patterns, month and day effects, sector seasonality, and market-cycle context. Seasonal evidence is treated cautiously because historical patterns can break. | Seasonal bias, supporting patterns, confidence, and limitations. |
| **Macro Agent** | Collects fundamental drivers such as rates, yields, oil, economic events, market expectations, and confirmed news. It separates facts, expectations, and interpretation. | Macro bias, event calendar, evidence, scoring, and risk factors. |
| **Technical Agent** | Analyses price action, 8-day and 21-day EMAs, trend structure, support, resistance, and invalidation levels. | Directional bias, measured levels, chart evidence, and invalidation conditions. |
| **Evidence Agent** | Fetches actual market data and produces the evidence needed by the agents, calibration process, and Delta Engine. | Actuals, market tables, screenshots, generated charts, and reusable evidence artefacts. |

Typical artefact locations:

```text
data/almanac/almanac_agent_WXX.md
data/macro/macro_agent_WXX.md
data/technical/technical_agent_WXX.md
data/evidence/
data/charts/
```

---

## Multi-LLM Synthesis

After the analysis artefacts are prepared, the same synthesis prompt is sent to four models. Their responses are stored separately and compared before the Human Score is completed.

<table>
<tr>
<td width="25%" align="center" valign="top">

**Nemotron 3 Super**
<br><sub>NVIDIA · 120B A12B</sub>

<br><sub><code>synthesis_nemotron_WXX.txt</code></sub>

</td>
<td width="25%" align="center" valign="top">

**HY3**
<br><sub>Tencent</sub>

<br><sub><code>synthesis_hy3_WXX.txt</code></sub>

</td>
<td width="25%" align="center" valign="top">

**Gemma 4 26B A4B**
<br><sub>Google</sub>

<br><sub><code>synthesis_gemma_WXX.txt</code></sub>

</td>
<td width="25%" align="center" valign="top">

**Laguna M.1**
<br><sub>Poolside</sub>

<br><sub><code>synthesis_laguna_WXX.txt</code></sub>

</td>
</tr>
</table>

The project uses separate model configurations for local development and automated CI runs:

| Configuration | Purpose | Active Models |
|---|---|---|
| `backend/pipeline.toml` | Lightweight local development and pipeline testing | Ollama `llama3.2:1b` |
| `backend/pipeline.ci.toml` | Full automated GitHub Actions run and four-model comparison | Nemotron 3 Super, Tencent HY3, Gemma 4 26B A4B, and Laguna M.1 |
| `backend/server.toml` | Flask server model registry and server-stage settings | Models exposed through the backend and frontend environment |

The four OpenRouter models used by `pipeline.ci.toml` are:

```toml
nvidia/nemotron-3-super-120b-a12b:free
tencent/hy3:free
google/gemma-4-26b-a4b-it:free
poolside/laguna-m.1:free
```

The local `pipeline.toml` configuration currently activates:

```toml
{id = "llama3.2:1b", slug = "llama3.2-1b", provider = "ollama"}
```

The OpenRouter entries in `pipeline.toml` are commented out, so local runs use the smaller Ollama model by default. `gpt-oss-120b` and `gemma-4-31b-it` are also commented out and are not part of the active CI comparison.

The comparison stage records:

- directional calls for SPX, NDX, and IWM;
- predicted percentage ranges and confidence;
- areas of model agreement;
- major disagreements and uncertainty;
- evidence quality and reasoning strength;
- contradictions between model claims and source artefacts; and
- points that require human judgement.

---

## Human Score and Final Prediction

The Human Score is the final review layer before a prediction is locked. It does not simply follow the majority of the LLMs.

The reviewer checks:

- whether each conclusion is supported by evidence;
- whether important market events were missed;
- whether confidence matches the level of uncertainty;
- whether the agents or models contradict each other;
- whether the prediction range is realistic;
- what evidence would invalidate the prediction; and
- whether the human conclusion should validate or override the AI consensus.

The final prediction records:

```text
SPX: direction + percentage range
NDX: direction + percentage range
IWM: direction + percentage range
Confidence: low / medium / high
Main reasoning
Main risks
Invalidation condition
```

Typical output:

```text
data/human/human_score_WXX.md
data/final prediction/prediction_YYYY-WXX.md
```

---

## Delta Engine and Calibration

The Delta Engine evaluates each locked prediction against the immediately following completed market week. It measures direction and range accuracy, builds a cumulative history from valid prediction–actuals pairs, and produces small, reviewable weight suggestions for the next sprint.

Pipeline and API runs only proceed after the relevant Friday market close. The manual CLI assumes that the user has supplied completed actuals. Delta never invents missing historical data, and its suggested weights do not automatically replace the team’s final judgement.

It is designed to calculate:

- direction accuracy;
- range accuracy;
- prediction error percentage;
- per-index results for SPX, NDX, and IWM;
- an overall structured delta report;
- evidence for calibration review; and
- possible future weight adjustments.

```text
Locked Prediction + Actual Results
                │
                ▼
          Delta Engine
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
   Direction   Range    Error
   Accuracy   Accuracy  Percentage
        └───────┼────────┘
                ▼
      Calibration and Learning
```
Delta Engine: Principles and Architecture

The Delta Engine compares a locked prediction with the following completed
week. It measures accuracy, keeps valid historical results and suggests small
weight changes for the next sprint.

## How Delta Works

```mermaid
flowchart TD
    C["Calculate current and<br/>cumulative accuracy"]
    WD{"Direction accuracy<br/>below 60%?"}
    WR{"Range accuracy<br/>below 60%?"}
    DKEEP["Keep LLM and Human Score weights"]
    DSHIFT["Suggest 0.05 transfer<br/>LLM → Human Score"]
    RKEEP["Keep Almanac and Technical weights"]
    RSHIFT["Suggest 0.05 transfer<br/>Almanac → Technical"]
    X["Write next-sprint prescription"]

    C --> WD
    WD -->|No| DKEEP
    WD -->|Yes| DSHIFT
    DKEEP --> WR
    DSHIFT --> WR
    WR -->|No| RKEEP
    WR -->|Yes| RSHIFT
    RKEEP --> X
    RSHIFT --> X
```

The automated pipeline and API enforce the Friday-close check. The CLI is a
manual tool and expects the user to provide completed actuals. The engine never
estimates a missing week. If an older prediction or its matching actuals file
is unavailable, that week is skipped and explained in the report. Suggested
weights are reviewable recommendations; Delta does not silently replace the
team's final decision.

## Application Architecture

```mermaid
flowchart LR
    subgraph EntryPoints["Entry points"]
        CLI["CLI<br/>run_delta_engine.py"]
        PIPE["Weekly pipeline<br/>run_pipeline.py"]
        API["Backend API<br/>POST /stages/delta"]
    end

    subgraph Inputs["Project inputs"]
        PRED["Locked prediction<br/>data/final prediction/"]
        EVID["Evidence actuals<br/>file or API artifact"]
        OLD["Previous Delta JSON<br/>reviewed weights + history"]
    end

    subgraph Delta["Delta package"]
        STAGE["run_delta()<br/>week and Friday-close checks"]
        AGENT["DeltaAgent<br/>coordinates one Delta run"]
        PARSE["parsing.py<br/>read and normalise"]
        SCORE["scoring.py<br/>accuracy and weights"]
        MODEL["models.py<br/>shared result types"]
        REPORT["report.py<br/>Markdown rendering"]
    end

    subgraph Outputs["Stored outputs"]
        MD["data/qa/delta_Wn.md"]
        JSON["data/outputs/delta/<br/>delta_Wn.json"]
    end

    subgraph Consumers["Application consumers"]
        CALAPI["GET /calibration/<br/>accuracy-tracker"]
        UI["Calibration page<br/>charts, coverage and weights"]
        LLM["Next LLM synthesis<br/>Delta context"]
    end

    CLI --> AGENT
    PIPE --> STAGE
    API --> STAGE
    STAGE --> AGENT

    PRED --> AGENT
    EVID -->|API and pipeline| STAGE
    EVID -->|CLI path| AGENT
    OLD --> AGENT

    AGENT --> PARSE
    PARSE --> SCORE
    SCORE -->|Scored rows| AGENT
    AGENT --> REPORT
    MODEL -.-> AGENT
    MODEL -.-> PARSE
    MODEL -.-> SCORE
    MODEL -.-> REPORT

    AGENT --> JSON
    REPORT --> MD
    JSON --> CALAPI
    CALAPI --> UI
    JSON -.-> LLM
```

The three entry points share the same `DeltaAgent`, so the scoring rules stay
the same whether Delta runs from the command line, the weekly pipeline or the
web application.
> **Current status:** the core Delta Engine logic and tests have been developed, and pipeline integration has started. Full backend, frontend, and Human Score integration remains in progress.

Typical output:

```text
data/qa/delta_WXX.md
```

---

## System Architecture

```mermaid
flowchart TB
    subgraph Inputs["Market and Economic Inputs"]
        MD["SPX · NDX · IWM<br/>GC · CL · ZN · TLT · VIX · BTC"]
        NEWS["Economic calendar · rates · confirmed news"]
    end

    subgraph Agents["Agent Pipeline"]
        A["Almanac Agent<br/>Seasonal context"]
        M["Macro Agent<br/>Fundamentals and events"]
        T["Technical Agent<br/>EMA · trend · S/R"]
        E["Evidence Agent<br/>Actuals · tables · charts"]
    end

    subgraph Synthesis["Multi-LLM Synthesis"]
        L["Four configurable LLMs<br/>Identical evidence and prompt"]
        C["LLM Comparison<br/>Consensus · divergence · uncertainty"]
    end

    subgraph Decision["Human Decision"]
        H["Human Score<br/>Evidence and judgement"]
        P["Locked Weekly Prediction<br/>SPX · NDX · IWM"]
    end

    subgraph Feedback["Calibration Loop"]
        D["Delta Engine<br/>Prediction vs actuals"]
        CAL["Accuracy · calibration · learning"]
    end

    subgraph Application["Application Layer"]
        API["Flask API<br/>Stage and artefact routes"]
        UI["React Dashboard<br/>Pipeline · charts · logs · review"]
    end

    MD --> A
    MD --> T
    MD --> E
    MD --> M
    NEWS --> M

    A --> L
    M --> L
    T --> L
    E --> L
    L --> C
    C --> H
    H --> P

    P --> D
    E --> D
    D --> CAL
    CAL -. informs next sprint .-> A
    CAL -. informs next sprint .-> M
    CAL -. informs next sprint .-> T
    CAL -. informs next sprint .-> H

    A --> API
    M --> API
    T --> API
    E --> API
    C --> API
    P --> API
    D --> API
    API --> UI
```

---

## Running the Backend Pipeline

### Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- API keys listed in `backend/.env.example`

### Setup

```bash
cd backend
cp .env.example .env
uv sync
```

Fill in the required values in `backend/.env`. Never commit real API keys.

### Run locally with Ollama

The default development configuration in `pipeline.toml` uses the local `llama3.2:1b` Ollama model:

```bash
uv run python run_pipeline.py
```

Make sure Ollama is installed and the configured model is available before running the local LLM stage.

### Run the full four-model configuration

The CI configuration enables the full automated workflow, including the four OpenRouter models and the Delta stage:

```bash
uv run python run_pipeline.py --config pipeline.ci.toml
```

GitHub Actions uses this configuration with the required API key stored in repository secrets.

### Start the backend server

```bash
uv run python run_server.py
```

The configuration files have separate purposes:

```text
backend/pipeline.toml       # Local development pipeline; Ollama llama3.2:1b is active
backend/pipeline.ci.toml    # Full automated CI pipeline; four OpenRouter models are active
backend/server.toml         # Flask server model registry and server-stage settings
```

---

## Running the Backend API

The Flask application factory and API routes are located in `backend/server/`. Start the API using the project entry point:

```bash
cd backend
uv run python run_server.py
```

`run_server.py` starts the Flask server, while `server.toml` controls the server-side model registry and related stage settings. The API supports agent execution, Evidence and LLM stages, Delta evaluation, saved artefacts, market history, calibration results, and model configuration.

The Flask CLI can also be used during development:

```bash
uv run flask --app "server:create_app" run --debug
```

---

## Running the Frontend

### Requirements

- Node.js
- npm

### Start the dashboard

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

The dashboard currently includes:

- pipeline-stage controls;
- Almanac, Macro, and Technical output cards;
- multi-LLM comparison;
- market charts;
- execution logs;
- calibration views;
- saved-week selection; and
- a Human Score review form.

The dashboard is already connected to the Flask backend for agent execution, Evidence generation, LLM synthesis, Delta evaluation, saved weeks and artefacts, market-price history, calibration data, and server model configuration.

The remaining demo-only or incomplete areas are limited: stage log descriptions are generated locally, and Human Score submission and persistence are still under development.

---

## Quality Assurance

Backend checks:

```bash
cd backend
uv run pyright agents/
uv run pytest tests/
```

Equivalent Makefile shortcuts:

```bash
make check
make test
```

Frontend checks:

```bash
cd frontend
npm run build
```

The repository uses GitHub Actions for automated pipeline, backend, agent, and frontend checks.

### Pull-Request Expectations

A pull request should:

1. address one clear feature, fix, or sprint artefact;
2. include meaningful tests where appropriate;
3. pass type checking and automated checks;
4. avoid placeholder tests that pass without validating behaviour;
5. resolve merge conflicts before final review;
6. explain how the change was tested; and
7. be reviewed before it is merged into `main`.

---

## Repository Structure

<sub>The structure may continue to change as integration work is completed.</sub>

```text
team1-prac-a-project/
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENCE.md
├── .github/
│   └── workflows/                     # CI, pipeline, agent and build checks
├── backend/
│   ├── agents/
│   │   ├── almanac/                   # Seasonal analysis automation
│   │   ├── macro/                     # Macro and news automation
│   │   ├── technical/                 # Technical analysis automation
│   │   ├── evidence/                  # Actuals, evidence and chart generation
│   │   ├── llm/                       # LLM providers and synthesis
│   │   └── pipeline/                  # Shared pipeline orchestration
│   ├── server/                        # Flask stage and artefact API
│   ├── tests/                         # pytest test suite
│   ├── .env.example
│   ├── Makefile
│   ├── pipeline.toml                   # Local pipeline; Ollama llama3.2:1b
│   ├── pipeline.ci.toml                # CI pipeline; four OpenRouter models
│   ├── server.toml                     # Flask server model registry and stage settings
│   ├── run_pipeline.py                 # Automated pipeline entry point
│   └── run_server.py                   # Flask API entry point
├── frontend/
│   ├── src/
│   │   ├── api/                       # Frontend API boundary
│   │   ├── app/                       # Application shell
│   │   ├── components/                # Shared UI components
│   │   ├── hooks/                     # Pipeline state and actions
│   │   ├── lib/                       # Helpers and demo data
│   │   └── pages/                     # Dashboard application pages
│   └── docs/screenshots/
├── data/
│   ├── almanac/
│   ├── macro/
│   ├── technical/
│   ├── evidence/
│   ├── charts/
│   ├── llm/
│   ├── human/
│   ├── final prediction/
│   ├── qa/                            # Delta and calibration reports
│   ├── formats/
│   └── outputs/
├── presentations/
├── scripts/
├── sprints/
└── tasks/
```

---

## Progress So Far

### Early Sprints

- Defined the sprint goal, acceptance criteria, Definition of Done, and weekly prediction format.
- Established protected-branch and pull-request practices.
- Created the Almanac, Macro, Technical, Evidence, LLM comparison, Human Score, final prediction, and QA artefact structure.
- Completed weekly manual predictions and calibration reports to establish the baseline workflow.

### Automation Increment

- Added shared Python schemas, agent interfaces, file handling, and pipeline orchestration.
- Automated Almanac, Macro, Technical, and Evidence stages.
- Added environment-specific LLM execution: local Ollama testing through `pipeline.toml` and four-model OpenRouter synthesis through `pipeline.ci.toml`.
- Added scheduled and CI pipeline configurations.
- Added generated market charts and evidence outputs.

### Application Increment

- Added a Flask backend server for agent execution, artefact access, market data, calibration, Delta evaluation, and model configuration.
- Added a React and Vite dashboard with pipeline, chart, log, calibration, historical-data, and review screens.
- Connected the dashboard to the Flask backend for the main pipeline and data workflows.
- Retained local demonstration behaviour only for stage log descriptions; Human Score submission and persistence remain active work.

### Calibration Increment

- Developed the Delta Engine for prediction-versus-actual comparison.
- Added direction, range, and error calculations.
- Added tests and Pyright validation.
- Added pipeline, Flask API, and dashboard access.
- Human Score submission, persistence, and full feedback-loop integration remain in progress.

---

## Known Limitations and Active Risks

- Local and CI runs use different LLM configurations, so output quality and response format may differ between Ollama testing and the four-model OpenRouter comparison.
- External LLM and data-provider rate limits can cause a pipeline stage to fail.
- The automated Macro Agent depends on free APIs and transformed web data, which may change without notice.
- Delta reports require both a locked prediction and complete actual-results artefacts.
- Stage log descriptions are still generated locally rather than returned by the backend.
- Human Score submission, persistence, and automatic pipeline integration are not complete.
- Historical views, richer graphs, and final frontend polish remain active development tasks.
- The repository structure and output paths may change while branches are merged and refactored.

---

## Resources and References

<table>
<thead>
<tr>
<th align="left">Resource</th>
<th align="left">Purpose</th>
</tr>
</thead>
<tbody>
<tr>
<td><a href="https://dt3-tr2-26-market-intelligence.pages.dev/"><b>DT3 Current Task Brief</b></a></td>
<td>Official course materials</td>
</tr>
<tr>
<td><a href="./tasks/W2Task.html"><b>DT3 Week 2 Task Brief</b></a></td>
<td>Local backup of the Week 2 task</td>
</tr>
<tr>
<td><a href="./tasks/W3Task.html"><b>DT3 Week 3 Task Brief</b></a></td>
<td>Local backup of the Week 3 task</td>
</tr>
<tr>
<td><a href="https://discord.com/channels/1505861202444816455/1505883026771677366"><b>CP3405 Discord</b></a></td>
<td>Team communication and announcements</td>
</tr>
<tr>
<td><a href="https://finviz.com/futures_performance.ashx"><b>Finviz Futures Performance</b></a></td>
<td>Weekly futures and cross-asset performance</td>
</tr>
<tr>
<td><a href="https://finance.yahoo.com/sectors/"><b>Yahoo Finance Sectors</b></a></td>
<td>US sector performance</td>
</tr>
<tr>
<td><a href="https://tradingeconomics.com/calendar"><b>Trading Economics Calendar</b></a></td>
<td>Week-ahead economic events</td>
</tr>
<tr>
<td><a href="https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html"><b>CME FedWatch Tool</b></a></td>
<td>Market-implied Federal Reserve rate probabilities</td>
</tr>
</tbody>
</table>

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the Git workflow, commit-message format, and coding conventions.

**Key rule:** all changes to `main` require a pull request. Do not push directly to the protected branch.

When submitting a pull request, include:

- a concise description of the problem and solution;
- the sprint or issue it supports;
- testing evidence;
- screenshots for visual changes;
- any known limitations; and
- the reviewer or role that should validate the change.

---

## Educational Disclaimer

This repository is an educational project for CP3405 Design Thinking 3. Its market analysis and predictions are not financial advice.
