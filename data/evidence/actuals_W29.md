# Week 09 Market Report (2026)

**Week ended:** Friday, July 17, 2026
**Days the market was open:** 5

This file lists how the main markets moved last week. **Closing value** = price at the end of Friday. **Weekly change** = up or down for the whole week.

---

## Main Stock Indexes (3 we track)

These are the big U.S. stock benchmarks we score each week.

| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
| S&P 500 — large U.S. companies | SPX | 7,457.69 | **Down 1.55%** |
| Nasdaq 100 — mostly tech | NDX | 28,592.66 | **Down 4.13%** |
| Russell 2000 — smaller companies | IWM | 294.04 | **Down 0.66%** |

**In plain words:** All 3 available index readings finished lower. IWM led with a down 0.66% move, while NDX was the weakest at down 4.13%.

---

## Other Important Markets

Gold, oil, bonds, fear gauge (VIX), and crypto.

| What it is | Friday close | Up or down this week |
|------------|--------------|----------------------|
| **Gold** | $4,013 per ounce | **Down 2.23%** |
| **Oil** (U.S. crude) | $82.49 per barrel | **Up 15.52%** |
| **10-Year interest rate** | 4.57% | **Slightly higher (about 0.01 points)** |
| **Bonds** (TLT fund) | 84.52 | **Up 0.06%** |
| **VIX** (how scared traders are; lower = calmer) | 18.77 | **Up 24.88%** |
| **Bitcoin** | $63,899 | **Down 0.36%** |

**In plain words:** Fear rose as VIX moved up 24.88%. Oil was up 15.52%, Bitcoin was down 0.36%, and bonds were up 0.06% as the 10-year yield edged up.

---

## 11 Parts of the Stock Market (S&P sectors)

Each row is one industry group in the S&P 500.

| Rank | Industry group | Up or down this week |
|------|----------------|----------------------|
| 1 | Energy (oil & gas companies) | **Up 4.72%** |
| 2 | Real estate | **Up 2.18%** |
| 3 | Consumer staples (food, toothpaste, etc.) | **Up 1.27%** |
| 4 | Financials (banks, insurance) | Up 0.99% |
| 5 | Health care | Up 0.16% |
| 6 | Utilities (power, water) | Down 0.53% |
| 7 | Materials (chemicals, metals, etc.) | Down 0.71% |
| 8 | Communication (phones, media, ads) | Down 0.89% |
| 9 | Industrials | **Down 1.38%** |
| 10 | Consumer discretionary (cars, hotels, shopping) | **Down 1.54%** |
| 11 | Technology | **Down 5.48%** |

### Best 3 this week
1. **Energy (oil & gas companies)** — up 4.72%. Move based on oil and gas producers via XLE.
2. **Real estate** — up 2.18%. Move based on property and REIT stocks via XLRE.
3. **Consumer staples (food, toothpaste, etc.)** — up 1.27%. Move based on defensive food and household products via XLP.

### Worst 3 this week
1. **Technology** — down 5.48%. Move based on software, chips, and hardware via XLK.
2. **Consumer discretionary (cars, hotels, shopping)** — down 1.54%. Move based on consumer spending-sensitive stocks via XLY.
3. **Industrials** — down 1.38%. Move based on manufacturers, transport, and machinery via XLI.

**In plain words:** Sector breadth showed a mixed market: 5 of 11 available sectors finished green. Energy (oil & gas companies) led at up 4.72%, while Technology lagged at down 5.48%.

---

## Charts & Screenshots

Saved in the **evidence** folder:

| What the picture shows | File name |
|------------------------|-----------|
| 1-week performance chart (Yahoo Finance) | [finviz_1W_2026_W29.png](./finviz_1W_2026_W29.png) |
| S&P 500 sector heatmap (Yahoo Finance) | [finviz_sectors_5D_2026_W29.png](./finviz_sectors_5D_2026_W29.png) |

## Where the numbers came from

- 1-week performance chart generated from Yahoo Finance weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- Yahoo Finance adjusted daily close data via yfinance for SPX (^GSPC), NDX (^NDX), IWM, Gold (GC=F), Oil (CL=F), TLT, VIX (^VIX), Bitcoin (BTC-USD), and sector ETFs
- 10-year Treasury yield from FRED series DGS10
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sources accessed: Sunday, July 19, 2026
