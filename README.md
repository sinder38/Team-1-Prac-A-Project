<div align="center">

<sub>CP3405 Design Thinking 3 &nbsp;·&nbsp; TR2 2026 &nbsp;·&nbsp; Singapore &nbsp;·&nbsp; Prof. Dr. Tan</sub>

# Market Intelligence — Team 1

<sub>Automated Market Analysis, Multi-LLM Comparison, Human review, and Weekly Calibration.</sub>

<br>

![Status](https://img.shields.io/badge/Status-Active_Development-3fb950?style=flat-square&labelColor=161b22)
![Progress](https://img.shields.io/badge/Progress-Week_9-58a6ff?style=flat-square&labelColor=161b22)
![Assets](https://img.shields.io/badge/Tracked_Assets-9-d29922?style=flat-square&labelColor=161b22)
![LLMs](https://img.shields.io/badge/CI_LLM_Models-5-bc8cff?style=flat-square&labelColor=161b22)
![Local LLM](https://img.shields.io/badge/Local_LLM-Ollama-ffffff?style=flat-square&labelColor=161b22&logo=ollama&logoColor=white)
![Backend](https://img.shields.io/badge/Backend-Python_%7C_Flask-3776ab?style=flat-square&labelColor=161b22)
![Frontend](https://img.shields.io/badge/Frontend-React_%7C_Vite-61dafb?style=flat-square&labelColor=161b22)

</div>

---

## What This Project Does

Team 1 is building a weekly market-intelligence system for SPX, NDX, and IWM predictions.

It collects market data, runs Almanac, Macro, Technical, and Evidence agents, compares LLM reasoning, applies human review, locks a prediction, and evaluates the result through the Delta Engine.

The local development pipeline uses Ollama with `llama3.2:3b`. The automated CI pipeline uses Nvidia Nemotron 3 Super, InclusionAI Ling 3.0 Flash, Google Gemma 4 26B A4B, OpenAI gpt-oss-20b, and Poolside Laguna XS 2.1 through OpenRouter.

> **Week 9 Status:** The Automated Pipeline, Flask API, React Dashboard, Multi-LLM Comparison, and Delta Engine are available. Human Score submission and persistence remain in progress.  
> See the [Full Development Status](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Development-Status).

---


## Quick Start

### Requirements

 - Python 3.12+
 - [`uv`](https://docs.astral.sh/uv/)
 - Node.js and npm
 - API keys listed in `backend/.env.example`
-- Ollama for optional local LLM testing
+- [Ollama](https://ollama.com) - used by the default local config's LLM stage
+  (`llama3.2:3b`); not needed for the CI configuration

 ### Backend

```bash
 cd backend
 cp .env.example .env
 uv sync

 # Local pipeline with Ollama (start `ollama serve` first)
 ollama pull llama3.2:3b
 uv run python run_pipeline.py

 # Full CI configuration (OpenRouter models; see pipeline.ci.toml)
 uv run python run_pipeline.py --config pipeline.ci.toml

 # Flask API
 uv run python run_server.py
```

#### Local models

The API server also exposes a few small local models to the frontend's
Stage 3 picker (see `[llm].models` in `backend/server.toml`). The pipeline
accepts **any** model Ollama can serve — add an entry to the relevant TOML
and pull the tag:

```toml
# backend/pipeline.toml or backend/server.toml, under [llm].models
{id = "qwen2.5:1.5b", slug = "qwen2.5-1.5b", provider = "ollama"},
```

`slug` names the synthesis artifacts and defaults to the id **without its
size tag** (`mistral:7b` → `mistral`), so set it explicitly when the tag
matters. Run `ollama pull <id>` for each model you enable.


### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

See [Setup and Configuration](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Setup-and-Configuration) for details.

---

## Documentation

| Topic | Wiki page |
|---|---|
| Purpose, Weekly Workflow, and Tracked Assets | [Project Overview](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Project-Overview) |
| Current Progress and Limitations | [Development Status](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Development-Status) |
| Agents, LLMs, and Human Score | [Agents, LLMs, and Human Review](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Agents-LLMs-and-Human-Review) |
| Delta Rules, Scoring, and Outputs | [Delta Engine](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Delta-Engine) |
| Pipeline, Flask API, React Dashboard, and Diagrams | [System Architecture](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/System-Architecture) |
| Installation, Commands, and Configuration | [Setup and Configuration](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Setup-and-Configuration) |
| Tests, PRs, Repository Structure, and References | [Development Guide](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Development-Guide) |

Start from the [Wiki Home](https://github.com/sinder38/Team-1-Prac-A-Project/wiki).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Development Guide](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Development-Guide).

All changes to `main` require a pull request.

---

## Educational Disclaimer

This repository is an educational project for CP3405 Design Thinking 3. Its market analysis and predictions are not financial advice.
