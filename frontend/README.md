# Market Intelligence Dashboard (Frontend)

React dashboard for the CP3405 Market Intelligence platform. It provides the UI
for running the prediction pipeline **one stage at a time**, viewing each agent's
output, comparing LLM results, tracking calibration accuracy, browsing price
charts, and filling in the weekly **Human Score** report.

**Stack:** Vite 4 · React 18 · Tailwind CSS 3 · lucide-react (icons) · lightweight-charts (candles)

> **Single-user, browser-only.** There is no login, no accounts, and no
> server/client split — everything runs locally in the browser.
>
> **Backend not connected.** Every call in `src/api/` currently returns bundled
> example data so the UI is fully usable without a backend. Each file is marked
> with a `TODO (backend task)` showing the real endpoint a teammate will wire up.

---

## Quick start

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). No Python, API keys, or
backend are required to run the demo.

### Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server on port 3000 (opens the browser) |
| `npm run build` | Production build → `dist/` |
| `npm run preview` | Serve the production build locally |

---

## How it works (demo behaviour)

- **Manual pipeline.** On the Dashboard the 5 stages are run individually — each
  has its own **Run** button and only the next pending stage is unlocked.
  Agent cards appear after stage 2, the LLM comparison after stage 3.
- **Human Score is the final stage.** Stages 1–4 are the AI pipeline; stage 5 is
  completed by submitting the report on the **Review** page.
- **Saved weeks** can be selected to view previously-completed outputs; choosing a
  new date resets the pipeline for a fresh manual run.

---

## Project structure

```
frontend/
├── index.html                  # HTML entry; mounts #root and loads src/main.jsx
├── vite.config.js              # Vite + React, dev server :3000, (commented) /api proxy
├── tailwind.config.js          # Tailwind content paths
├── postcss.config.js           # PostCSS (tailwind + autoprefixer)
├── package.json                # Dependencies and scripts
└── src/
    ├── main.jsx                # React root render + global CSS import
    ├── index.css               # Tailwind layers + scrollbar/body styles
    │
    ├── app/
    │   └── App.jsx             # Top-level layout; holds page state and wires usePipeline → pages
    │
    ├── pages/                  # One component per screen (route-like views)
    │   ├── index.js            # Barrel export for all pages
    │   ├── DashboardPage.jsx   # Pipeline controller + agent signal cards
    │   ├── ChartsPage.jsx      # Instrument selector + candlestick chart + stats
    │   ├── LogsPage.jsx        # Execution logs with search/filter + run-next button
    │   ├── CalibrationPage.jsx # Accuracy tracker, weekly trend, per-agent bars
    │   ├── ReviewPage.jsx      # Wraps the Human Score report form
    │   └── SettingsPage.jsx    # "About" page (no accounts / data-source notes)
    │
    ├── components/             # Reusable UI grouped by feature
    │   ├── layout/
    │   │   ├── LeftNavigation.jsx  # Icon sidebar
    │   │   ├── TopHeader.jsx       # Breadcrumb header
    │   │   └── index.js
    │   ├── pipeline/
    │   │   ├── PipelineController.jsx # Per-stage run controls + status + reset
    │   │   ├── WeekPicker.jsx         # Date picker + saved-week dropdown
    │   │   └── index.js
    │   ├── agents/
    │   │   ├── AgentCard.jsx          # Single agent card (+ AgentCardPlaceholder)
    │   │   ├── AgentOutputsGrid.jsx   # 3-card grid + LLM panel
    │   │   ├── LlmComparisonPanel.jsx # LLM consensus / per-model breakdown
    │   │   └── index.js
    │   ├── charts/
    │   │   ├── PriceChart.jsx         # lightweight-charts candles + 8/21 EMA + volume
    │   │   └── index.js
    │   └── review/
    │       ├── ReviewForm.jsx         # Fill-in Human Score report (+ copy as Markdown)
    │       └── index.js
    │
    ├── hooks/
    │   └── usePipeline.js      # Central state: stages, logs, outputs, weeks, run/reset/complete
    │
    ├── api/                    # Backend boundary — stubbed with example data (TODO: FastAPI)
    │   ├── index.js            # Barrel export for all api functions
    │   ├── http.js             # fetch helper scaffold (API_BASE, getJson) for real calls
    │   ├── pipeline.js         # status / logs / per-stage run
    │   ├── agents.js           # available weeks / agent outputs
    │   ├── calibration.js      # accuracy tracker
    │   ├── validation.js       # submit human score
    │   └── market.js           # instruments / price history
    │
    └── lib/                    # Pure helpers, constants, and demo data
        ├── date.js            # todayIso, dateToWeekLabel (ISO week), formatDateTime
        ├── defaults.js        # Empty/default shapes (outputs, calibration, review form)
        ├── agentDisplay.js    # Parse raw agent text → card content (bias, confidence, metrics)
        ├── exampleData.js     # Demo weeks, agent outputs, logs, stage helpers
        ├── marketData.js      # Deterministic OHLC/EMA/volume generator for charts
        └── constants/
            ├── index.js       # Barrel export for all constants
            ├── navigation.js  # Sidebar items + page titles
            ├── agents.js      # Agent labels and bar colors
            └── review.js      # Human Score dimensions, calls, confidence, evidence
```

### Conventions

- **Barrels (`index.js`)** in each folder keep imports short, e.g.
  `import { AgentCard } from '../components/agents'`.
- **`api/` is the only place** that should talk to the backend. UI and hooks never
  call `fetch` directly — they call `api/*` functions, so swapping stubs for real
  endpoints is isolated.
- **`lib/` is framework-free** (no React) — pure functions and data, easy to test.

---

## Backend integration (TODO)

The backend (FastAPI) is a separate teammate's task. To connect it:

1. Implement the endpoints below in `backend/api/`.
2. Replace the example-data return values in each `src/api/*.js` file (each has a
   `TODO` comment with the exact endpoint).
3. Uncomment the `/api` proxy in `vite.config.js` (targets `http://localhost:8000`).
4. Use `http.js` (`getJson` / `API_BASE`) for the actual requests.

| Endpoint | Stub file |
|----------|-----------|
| `GET /api/pipeline/status` | `api/pipeline.js` |
| `GET /api/pipeline/logs` | `api/pipeline.js` |
| `POST /api/pipeline/stage/{index}/run` | `api/pipeline.js` |
| `GET /api/weeks` | `api/agents.js` |
| `GET /api/agents/outputs?week=` | `api/agents.js` |
| `GET /api/calibration/accuracy-tracker` | `api/calibration.js` |
| `POST /api/validation/human-score` | `api/validation.js` |
| `GET /api/market/history?symbol=` | `api/market.js` |

The shapes the UI expects are documented by the example data in `src/lib/`
(`exampleData.js` for pipeline/agents/calibration, `marketData.js` for charts).

---

## CI

GitHub Actions runs `npm ci` and `npm run build` on changes under `frontend/`.
