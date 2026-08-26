# Week 12 Market Report (2026)

**Week ended:** Friday, August 7, 2026
**Days the market was open:** 5

This file lists how the main markets moved last week. **Closing value** = price at the end of Friday. **Weekly change** = up or down for the whole week.

---

## Main Stock Indexes (3 we track)

These are the big U.S. stock benchmarks we score each week.

| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
| S&P 500 — large U.S. companies | SPX | 7,757.64 | **Up 3.58%** |
| Nasdaq 100 — mostly tech | NDX | 29,722.30 | **Up 5.12%** |
| Russell 2000 — smaller companies | IWM | 301.56 | **Up 3.56%** |

**In plain words:** All 3 available index readings finished higher. NDX led with a up 5.12% move, while IWM was the weakest at up 3.56%.

---

## Other Important Markets

Gold, oil, bonds, fear gauge (VIX), and crypto.

| What it is | Friday close | Up or down this week |
|------------|--------------|----------------------|
| **Gold** | $4,341 per ounce | **Up 7.20%** |
| **Oil** (U.S. crude) | $78.18 per barrel | **Down 7.67%** |
| **10-Year interest rate** | 4.69% | **Slightly lower (about 0.06 points)** |
| **Bonds** (TLT fund) | 82.76 | **Up 1.03%** |
| **VIX** (how scared traders are; lower = calmer) | 14.90 | **Down 6.82%** |
| **Bitcoin** | $64,880 | **Up 3.29%** |

**In plain words:** Fear eased as VIX moved down 6.82%. Oil was down 7.67%, Bitcoin was up 3.29%, and bonds were up 1.03% as the 10-year yield edged down.

---

## 11 Parts of the Stock Market (S&P sectors)

Each row is one industry group in the S&P 500.

| Rank | Industry group | Up or down this week |
|------|----------------|----------------------|
| 1 | Technology | **Up 7.20%** |
| 2 | Materials (chemicals, metals, etc.) | **Up 4.82%** |
| 3 | Consumer discretionary (cars, hotels, shopping) | **Up 3.25%** |
| 4 | Industrials | Up 2.97% |
| 5 | Communication (phones, media, ads) | Up 2.78% |
| 6 | Health care | Up 1.93% |
| 7 | Financials (banks, insurance) | Up 1.16% |
| 8 | Consumer staples (food, toothpaste, etc.) | Up 0.08% |
| 9 | Real estate | **Down 0.20%** |
| 10 | Utilities (power, water) | **Down 1.67%** |
| 11 | Energy (oil & gas companies) | **Down 3.44%** |

### Best 3 this week
1. **Technology** — up 7.20%. Move based on software, chips, and hardware via XLK.
2. **Materials (chemicals, metals, etc.)** — up 4.82%. Move based on chemicals, metals, and industrial inputs via XLB.
3. **Consumer discretionary (cars, hotels, shopping)** — up 3.25%. Move based on consumer spending-sensitive stocks via XLY.

### Worst 3 this week
1. **Energy (oil & gas companies)** — down 3.44%. Move based on oil and gas producers via XLE.
2. **Utilities (power, water)** — down 1.67%. Move based on regulated power and water utilities via XLU.
3. **Real estate** — down 0.20%. Move based on property and REIT stocks via XLRE.

**In plain words:** Sector breadth showed a broad rally: 8 of 11 available sectors finished green. Technology led at up 7.20%, while Energy (oil & gas companies) lagged at down 3.44%.

---

## Charts & Screenshots

Saved in the **evidence** folder:

| What the picture shows | File name |
|------------------------|-----------|
| 1-week performance chart (Yahoo Finance) | [finviz_1W_2026_W32.png](./finviz_1W_2026_W32.png) |
| S&P 500 sector heatmap (Yahoo Finance) | [finviz_sectors_5D_2026_W32.png](./finviz_sectors_5D_2026_W32.png) |

## Where the numbers came from

- 1-week performance chart generated from Yahoo Finance weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- Yahoo Finance adjusted daily close data via yfinance for SPX (^GSPC), NDX (^NDX), IWM, Gold (GC=F), Oil (CL=F), TLT, VIX (^VIX), Bitcoin (BTC-USD), and sector ETFs
- 10-year Treasury yield from FRED series DGS10
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sources accessed: Saturday, August 8, 2026
