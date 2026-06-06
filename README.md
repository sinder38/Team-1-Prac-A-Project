<div align="center">

<sub>CP3405 Design Thinking 3 &nbsp;·&nbsp; TR2 2026 &nbsp;·&nbsp; Singapore &nbsp;·&nbsp; Prof. Dr. Tan</sub>

# Market Intelligence — Team 1

<sub>A 10-week sprint exercise in structured market analysis, AI collaboration, and calibrated prediction.</sub>

<br>

![Sprints](https://img.shields.io/badge/sprints-10-58a6ff?style=flat-square&labelColor=161b22)
![LLMs](https://img.shields.io/badge/LLMs-4-3fb950?style=flat-square&labelColor=161b22)
![Assets](https://img.shields.io/badge/assets-9-d29922?style=flat-square&labelColor=161b22)
![Location](https://img.shields.io/badge/Singapore-TR2_2026-bc8cff?style=flat-square&labelColor=161b22)

</div>

---

## Project Overview

Each week, our team runs a full intelligence cycle:

1. **Reads real market data** — S&P 500, Nasdaq 100, Russell 2000, and 8 macro assets
2. **Builds structured analysis** — Almanac (seasonal), Macro (fundamentals), and Technical (chart) agents
3. **Queries four AI models** — Claude, ChatGPT, Gemini, DeepSeek with identical prompts
4. **Applies human judgment** — Our team's reasoning overrides or validates AI consensus
5. **Makes a prediction** — SPX, NDX, IWM direction + % range + confidence level
6. **Measures calibration** — Were we right *and* confident, or wrong *but* honest about uncertainty?

By Week 10 we will have a 10-sprint track record of predictions vs. actuals, a public GitHub history showing our reasoning, and a live web application that any user can access to see our analysis.

---

## The Nine Tracked Assets

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
<td>The benchmark. 500 largest US companies.</td>
</tr>
<tr>
<td><b>Nasdaq 100</b></td>
<td><code>NDX</code></td>
<td>Tech-heavy. Fastest-moving index.</td>
</tr>
<tr>
<td><b>Russell 2000</b></td>
<td><code>IWM</code></td>
<td>Small caps. Most rate-sensitive.</td>
</tr>
<tr>
<td><b>Gold</b></td>
<td><code>GC</code></td>
<td>Safe haven. Inflation &amp; fear gauge.</td>
</tr>
<tr>
<td><b>Crude Oil</b></td>
<td><code>CL</code></td>
<td>Inflation driver. Geopolitical signal.</td>
</tr>
<tr>
<td><b>10-Year Treasury Yield</b></td>
<td><code>ZN</code></td>
<td>The gravity on all asset valuations.</td>
</tr>
<tr>
<td><b>US Bonds</b></td>
<td><code>TLT</code></td>
<td>Stocks + bonds both down = fear signal.</td>
</tr>
<tr>
<td><b>VIX</b></td>
<td><code>VIX</code></td>
<td>Volatility index. Fear measure. 15 = calm, 30+ = panic.</td>
</tr>
<tr>
<td><b>Bitcoin</b></td>
<td><code>BTC</code></td>
<td>Risk appetite proxy. 24/7 trading.</td>
</tr>
</tbody>
</table>

---

## The Three-Agent Framework

<table>
<tr>
<td width="33%" valign="top">

**Almanac Agent** &nbsp;<sub>R3</sub>

Seasonal patterns from 75 years of market history. This week's month rank, day-of-week effects, sector seasonality, and presidential cycle context.

Confidence is deliberately lower than charts — patterns break.

<sub><code>data/almanac/almanac_agent_WXX.md</code></sub>

</td>
<td width="33%" valign="top">

**Macro Agent** &nbsp;<sub>R4</sub>

The fundamental drivers: Fed rate probabilities, yield curve, dollar, oil, economic calendar surprises, confirmed news events.

Separated into three layers — confirmed facts, market expectations, and our interpretation.

<sub><code>data/macro/macro_agent_WXX.md</code></sub>

</td>
<td width="33%" valign="top">

**Technical Agent** &nbsp;<sub>R5</sub>

Chart reading: 8-day EMA, 21-day EMA, trendlines, support/resistance levels. Specific invalidation levels.

No vague calls like "looks bullish" — only measured statements like "bullish while above 7,350."

<sub><code>data/technical/technical_agent_WXX.md</code></sub>

</td>
</tr>
</table>

---

## Multi-LLM Synthesis

After the three agents are built, we paste them into an identical prompt and query all four models. We save all four raw responses and fill a comparison table — where do they agree (high confidence), where do they diverge (flag as uncertainty), and which model's reasoning is strongest this week.

<table>
<tr>
<td width="25%" align="center" valign="top">

**Claude**
<br><sub>Anthropic</sub>

<br><sub><code>synthesis_claude_WXX.txt</code></sub>

</td>
<td width="25%" align="center" valign="top">

**ChatGPT**
<br><sub>OpenAI</sub>

<br><sub><code>synthesis_chatgpt_WXX.txt</code></sub>

</td>
<td width="25%" align="center" valign="top">

**Gemini**
<br><sub>Google</sub>

<br><sub><code>synthesis_gemini_WXX.txt</code></sub>

</td>
<td width="25%" align="center" valign="top">

**DeepSeek**
<br><sub>DeepSeek</sub>

<br><sub><code>synthesis_deepseek_WXX.txt</code></sub>

</td>
</tr>
</table>

---

## The Ten Scrum Roles

<table>
<thead>
<tr>
<th align="left">Role</th>
<th align="left">Responsibility</th>
<th align="left">GitHub Artifact</th>
</tr>
</thead>
<tbody>
<tr>
<td><b>R1 — Product Owner</b></td>
<td>Sprint goal. Definition of done.</td>
<td>
<code>sprints/sprint_goal_WXX.md</code><br>
<code>sprints/acceptance_criteria_WXX.md</code>
</td>
</tr>
<tr>
<td><b>R2 — Scrum Master</b></td>
<td>Stand-ups. Retrospective. Blockers.</td>
<td>
<code>sprints/standup_WXX.md</code><br>
<code>sprints/retrospective_WXX.md</code>
</td>
</tr>
<tr>
<td><b>R3 — Almanac Agent Lead</b></td>
<td>Seasonal pattern analysis.</td>
<td><code>data/almanac/almanac_agent_WXX.md</code></td>
</tr>
<tr>
<td><b>R4 — Macro Agent Lead</b></td>
<td>Fed, rates, oil, calendar.</td>
<td><code>data/macro/macro_agent_WXX.md</code></td>
</tr>
<tr>
<td><b>R5 — Technical Agent Lead</b></td>
<td>Charts. EMA zones. Key levels.</td>
<td><code>data/technical/technical_agent_WXX.md</code></td>
</tr>
<tr>
<td><b>R6 — LLM Synthesis Operator</b></td>
<td>Query all four models. Comparison table.</td>
<td>
<code>data/llm/synthesis_*_WXX.txt</code><br>
<code>data/llm/llm_comparison_WXX.md</code>
</td>
</tr>
<tr>
<td><b>R7 — Human Score Analyst</b></td>
<td>Five-dimension scoring. Override paragraph. Final prediction.</td>
<td><code>data/human/human_score_WXX.md</code></td>
</tr>
<tr>
<td><b>R8 — Data &amp; Evidence Lead</b></td>
<td>Data sourcing. Screenshots. Actuals recording.</td>
<td><code>data/evidence/actuals_WXX.md</code>
<code>data/evidence/finviz_*.png</code></td>
</tr>
<tr>
<td><b>R9 — GitHub &amp; Integration Lead</b></td>
<td>Repository organization. Commits. Release tags.</td>
<td>All required content merged
    README up to date
    Repository maintained
</td>
</tr>
<tr>
<td><b>R10 — QA &amp; Learning Log Lead</b></td>
<td>Calibration scoring. LLM horse race. Learning log.</td>
<td>
<code>data/qa/calibration_log.md</code><br>
<code>data/qa/llm_horserace.md</code><br>
<code>data/qa/learning_log_WXX.md</code>
</td>
</tr>
</tbody>
</table>

---

## Repository Structure

<sub>May not be fully up to date</sub>

```
team1-prac-a-project/
├── README.md                          # This file
├── CONTRIBUTING.md                    # Git workflow & coding standards
├── CODE_OF_CONDUCT.md                 # Code of conduct
├── LICENCE.md                         # Project licencing 
├── /.github/                          # GitHub Actions
├── /sprints/                          # Sprint details
├── /scripts/                          # Various helper scripts
├── /data/
│   ├── /evidence/                     # Data & screenshots 
│   ├── /almanac/                      # Analysis from Investors Almanac
│   ├── /macro/                        # Fundamental analysis
│   ├── /technical/                    # Technical analysis
│   ├── /charts/                       # Charts Screenshots
│   ├── /llm/                          # LLM outputs and comparisons
│   ├── /formats/                      # Formats for each agent
│   ├── /final prediction/             # Our final prediction
│   ├── /qa/                           # Quality assurance
│   └── /human/                        # Human predictions
└── /presentations/                    # Class presentations
```
---

## Resources & References

<table>
<thead>
<tr>
<th align="left">Resource</th>
<th align="left">What it's for</th>
</tr>
</thead>
<tbody>
<tr>
<td><a href="https://dt3-tr2-26-market-intelligence.pages.dev/"><b>DT3 Task Brief</b></a></td>
<td>Official course materials</td>
</tr>
<tr>
<td><a href="https://discord.com/channels/1505861202444816455/1505883026771677366"><b>CP3405 Discord</b></a></td>
<td>Team comms &amp; announcements</td>
</tr>
<tr>
<td><a href="https://finviz.com/futures_performance.ashx"><b>Finviz Futures Performance</b></a></td>
<td>All 9 assets, 1W performance view</td>
</tr>
<tr>
<td><a href="https://finance.yahoo.com/sectors/"><b>Yahoo Finance Sectors</b></a></td>
<td>11 sectors, 5D view</td>
</tr>
<tr>
<td><a href="https://tradingeconomics.com/calendar"><b>TradingEconomics Calendar</b></a></td>
<td>Week-ahead economic events</td>
</tr>
<tr>
<td><a href="https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html"><b>CME FedWatch Tool</b></a></td>
<td>Fed rate probabilities</td>
</tr>
</tbody>
</table>

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for git workflow, commit message format, and code style conventions.

**Key rule:** All changes to `main` require a pull request. No direct pushes.
