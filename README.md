<div align="center">

<sub>CP3405 Design Thinking 3 &nbsp;·&nbsp; TR2 2026 &nbsp;·&nbsp; Singapore &nbsp;·&nbsp; Prof. Dr. Tan</sub>

# Market Intelligence — Team 1

<sub>Automated market analysis, multi-LLM comparison, human review, and weekly calibration.</sub>

<br>

![Status](https://img.shields.io/badge/Status-Active_Development-3fb950?style=flat-square&labelColor=161b22)
![Progress](https://img.shields.io/badge/Progress-Week_9-58a6ff?style=flat-square&labelColor=161b22)
![Assets](https://img.shields.io/badge/Tracked_Assets-9-d29922?style=flat-square&labelColor=161b22)
![LLMs](https://img.shields.io/badge/CI_Integrated_LLMs-5-bc8cff?style=flat-square&labelColor=161b22)
![Backend](https://img.shields.io/badge/Backend-Python_%7C_Flask-3776ab?style=flat-square&labelColor=161b22)
![Frontend](https://img.shields.io/badge/Frontend-React_%7C_Vite-61dafb?style=flat-square&labelColor=161b22)

</div>

---

## What This Project Does

Team 1 is building a weekly market-intelligence system for SPX, NDX, and IWM predictions.

It collects market data, runs Almanac, Macro, Technical, and Evidence agents, compares LLM reasoning, applies human review, locks a prediction, and evaluates the result through the Delta Engine.

The local development pipeline uses Ollama with `llama3.2:3b`. The automated CI pipeline uses Nvidia Nemotron 3 Super, InclusionAI Ling 3.0 Flash, Google Gemma 4 26B A4B, OpenAI gpt-oss-20b, and Poolside Laguna XS 2.1 through OpenRouter.

> **Week 8 status:** the automated pipeline, Flask API, React dashboard, multi-LLM comparison, and Delta Engine are available. Human Score submission and persistence remain in progress.  
> See the [full development status](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Development-Status).

---

## Quick Start

### Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- Node.js and npm
- API keys listed in `backend/.env.example`
- Ollama for optional local LLM testing

### Backend

```bash
cd backend
cp .env.example .env
uv sync

# Local pipeline with Ollama
uv run python run_pipeline.py

# Full four-model configuration
uv run python run_pipeline.py --config pipeline.ci.toml

# Flask API
uv run python run_server.py
```

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
| Purpose, weekly workflow, and tracked assets | [Project Overview](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Project-Overview) |
| Current progress and limitations | [Development Status](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Development-Status) |
| Agents, LLMs, and Human Score | [Agents, LLMs, and Human Review](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Agents-LLMs-and-Human-Review) |
| Delta rules, scoring, and outputs | [Delta Engine](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Delta-Engine) |
| Pipeline, Flask API, React dashboard, and diagrams | [System Architecture](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/System-Architecture) |
| Installation, commands, and configuration | [Setup and Configuration](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Setup-and-Configuration) |
| Tests, PRs, repository structure, and references | [Development Guide](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Development-Guide) |

Start from the [Wiki Home](https://github.com/sinder38/Team-1-Prac-A-Project/wiki).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Development Guide](https://github.com/sinder38/Team-1-Prac-A-Project/wiki/Development-Guide).

All changes to `main` require a pull request.

---

## Educational Disclaimer

This repository is an educational project for CP3405 Design Thinking 3. Its market analysis and predictions are not financial advice.
