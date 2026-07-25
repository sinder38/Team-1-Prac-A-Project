# Week 10 Market Report (2026)

**Week ended:** Friday, July 24, 2026
**Days the market was open:** 4

This file lists how the main markets moved last week. **Closing value** = price at the end of Friday. **Weekly change** = up or down for the whole week.

---

## Main Stock Indexes (3 we track)

These are the big U.S. stock benchmarks we score each week.

| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
| S&P 500 — large U.S. companies | SPX | 7,408.30 | **Down 0.66%** |
| Nasdaq 100 — mostly tech | NDX | 28,454.81 | **Down 0.48%** |
| Russell 2000 — smaller companies | IWM | 292.09 | **Down 0.66%** |

**In plain words:** All 3 available index readings finished lower. NDX led with a down 0.48% move, while IWM was the weakest at down 0.66%.

---

## Other Important Markets

Gold, oil, bonds, fear gauge (VIX), and crypto.

| What it is | Friday close | Up or down this week |
|------------|--------------|----------------------|
| **Gold** | $4,068 per ounce | **Up 1.37%** |
| **Oil** (U.S. crude) | $89.31 per barrel | **Up 8.27%** |
| **10-Year interest rate** | 4.71% | **Slightly higher (about 0.16 points)** |
| **Bonds** (TLT fund) | 83.17 | **Down 1.60%** |
| **VIX** (how scared traders are; lower = calmer) | 18.58 | **Down 1.01%** |
| **Bitcoin** | $65,045 | **Up 1.79%** |

**In plain words:** Fear eased as VIX moved down 1.01%. Oil was up 8.27%, Bitcoin was up 1.79%, and bonds were down 1.60% as the 10-year yield edged up.

---

## 11 Parts of the Stock Market (S&P sectors)

Each row is one industry group in the S&P 500.

| Rank | Industry group | Up or down this week |
|------|----------------|----------------------|
| 1 | Energy (oil & gas companies) | **Up 2.95%** |
| 2 | Utilities (power, water) | **Up 2.26%** |
| 3 | Technology | **Up 1.63%** |
| 4 | Industrials | Up 1.41% |
| 5 | Health care | Up 0.22% |
| 6 | Materials (chemicals, metals, etc.) | Down 0.47% |
| 7 | Financials (banks, insurance) | Down 0.76% |
| 8 | Real estate | Down 1.03% |
| 9 | Consumer staples (food, toothpaste, etc.) | **Down 2.32%** |
| 10 | Communication (phones, media, ads) | **Down 4.76%** |
| 11 | Consumer discretionary (cars, hotels, shopping) | **Down 5.79%** |

### Best 3 this week
1. **Energy (oil & gas companies)** — up 2.95%. Move based on oil and gas producers via XLE.
2. **Utilities (power, water)** — up 2.26%. Move based on regulated power and water utilities via XLU.
3. **Technology** — up 1.63%. Move based on software, chips, and hardware via XLK.

### Worst 3 this week
1. **Consumer discretionary (cars, hotels, shopping)** — down 5.79%. Move based on consumer spending-sensitive stocks via XLY.
2. **Communication (phones, media, ads)** — down 4.76%. Move based on telecom, media, and internet platforms via XLC.
3. **Consumer staples (food, toothpaste, etc.)** — down 2.32%. Move based on defensive food and household products via XLP.

**In plain words:** Sector breadth showed a mixed market: 5 of 11 available sectors finished green. Energy (oil & gas companies) led at up 2.95%, while Consumer discretionary (cars, hotels, shopping) lagged at down 5.79%.

---

## Charts & Screenshots

Saved in the **evidence** folder:

| What the picture shows | File name |
|------------------------|-----------|
| 1-week performance chart (Yahoo Finance) | [finviz_1W_2026_W30.png](./finviz_1W_2026_W30.png) |
| S&P 500 sector heatmap (Yahoo Finance) | [finviz_sectors_5D_2026_W30.png](./finviz_sectors_5D_2026_W30.png) |

## Where the numbers came from

- 1-week performance chart generated from Yahoo Finance weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- Yahoo Finance adjusted daily close data via yfinance for SPX (^GSPC), NDX (^NDX), IWM, Gold (GC=F), Oil (CL=F), TLT, VIX (^VIX), Bitcoin (BTC-USD), and sector ETFs
- 10-year Treasury yield from FRED series DGS10
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sources accessed: Saturday, July 25, 2026
