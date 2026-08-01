# Week 11 Market Report (2026)

**Week ended:** Friday, July 31, 2026
**Days the market was open:** 5

This file lists how the main markets moved last week. **Closing value** = price at the end of Friday. **Weekly change** = up or down for the whole week.

---

## Main Stock Indexes (3 we track)

These are the big U.S. stock benchmarks we score each week.

| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
| S&P 500 — large U.S. companies | SPX | 7,489.72 | **Up 1.05%** |
| Nasdaq 100 — mostly tech | NDX | 28,274.20 | **Up 0.52%** |
| Russell 2000 — smaller companies | IWM | 291.20 | **Up 0.01%** |

**In plain words:** All 3 available index readings finished higher. SPX led with a up 1.05% move, while IWM was the weakest at up 0.01%.

---

## Other Important Markets

Gold, oil, bonds, fear gauge (VIX), and crypto.

| What it is | Friday close | Up or down this week |
|------------|--------------|----------------------|
| **Gold** | $4,049 per ounce | **Down 0.45%** |
| **Oil** (U.S. crude) | $84.67 per barrel | **Down 5.20%** |
| **10-Year interest rate** | 4.68% | **Slightly lower (about 0.01 points)** |
| **Bonds** (TLT fund) | 82.25 | **Down 1.20%** |
| **VIX** (how scared traders are; lower = calmer) | 15.99 | **Down 13.94%** |
| **Bitcoin** | $62,814 | **Down 2.00%** |

**In plain words:** Fear eased as VIX moved down 13.94%. Oil was down 5.20%, Bitcoin was down 2.00%, and bonds were down 1.20% as the 10-year yield edged down.

---

## 11 Parts of the Stock Market (S&P sectors)

Each row is one industry group in the S&P 500.

| Rank | Industry group | Up or down this week |
|------|----------------|----------------------|
| 1 | Consumer discretionary (cars, hotels, shopping) | **Up 6.11%** |
| 2 | Communication (phones, media, ads) | **Up 1.83%** |
| 3 | Financials (banks, insurance) | **Up 1.12%** |
| 4 | Consumer staples (food, toothpaste, etc.) | Up 1.09% |
| 5 | Health care | Down 0.01% |
| 6 | Energy (oil & gas companies) | Down 0.12% |
| 7 | Technology | Down 0.30% |
| 8 | Industrials | Down 1.54% |
| 9 | Materials (chemicals, metals, etc.) | **Down 1.62%** |
| 10 | Real estate | **Down 1.92%** |
| 11 | Utilities (power, water) | **Down 4.19%** |

### Best 3 this week
1. **Consumer discretionary (cars, hotels, shopping)** — up 6.11%. Move based on consumer spending-sensitive stocks via XLY.
2. **Communication (phones, media, ads)** — up 1.83%. Move based on telecom, media, and internet platforms via XLC.
3. **Financials (banks, insurance)** — up 1.12%. Move based on banks, brokers, and insurers via XLF.

### Worst 3 this week
1. **Utilities (power, water)** — down 4.19%. Move based on regulated power and water utilities via XLU.
2. **Real estate** — down 1.92%. Move based on property and REIT stocks via XLRE.
3. **Materials (chemicals, metals, etc.)** — down 1.62%. Move based on chemicals, metals, and industrial inputs via XLB.

**In plain words:** Sector breadth showed a mixed market: 4 of 11 available sectors finished green. Consumer discretionary (cars, hotels, shopping) led at up 6.11%, while Utilities (power, water) lagged at down 4.19%.

---

## Charts & Screenshots

Saved in the **evidence** folder:

| What the picture shows | File name |
|------------------------|-----------|
| 1-week performance chart (Yahoo Finance) | [finviz_1W_2026_W31.png](./finviz_1W_2026_W31.png) |
| S&P 500 sector heatmap (Yahoo Finance) | [finviz_sectors_5D_2026_W31.png](./finviz_sectors_5D_2026_W31.png) |

## Where the numbers came from

- 1-week performance chart generated from Yahoo Finance weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- Yahoo Finance adjusted daily close data via yfinance for SPX (^GSPC), NDX (^NDX), IWM, Gold (GC=F), Oil (CL=F), TLT, VIX (^VIX), Bitcoin (BTC-USD), and sector ETFs
- 10-year Treasury yield from FRED series DGS10
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sources accessed: Saturday, August 1, 2026
