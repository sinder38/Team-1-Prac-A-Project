# Week 09 Market Report (2026)

**Week ended:** Friday, July 17, 2026
**Days the market was open:** 5

This file lists how the main markets moved last week. **Closing value** = price at the end of Friday. **Weekly change** = up or down for the whole week.

---

## Main Stock Indexes (3 we track)

These are the big U.S. stock benchmarks we score each week.

| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
| S&P 500 — large U.S. companies | SPX | 7,469.51 | **Down 1.40%** |
| Nasdaq 100 — mostly tech | NDX | 28,526.56 | **Down 4.35%** |
| Russell 2000 — smaller companies | IWM | 293.99 | **Down 0.68%** |

**In plain words:** All 3 available index readings finished lower. IWM led with a down 0.68% move, while NDX was the weakest at down 4.35%.

---

## Other Important Markets

Gold, oil, bonds, fear gauge (VIX), and crypto.

| What it is | Friday close | Up or down this week |
|------------|--------------|----------------------|
| **Gold** | $4,006 per ounce | **Down 2.39%** |
| **Oil** (U.S. crude) | $80.22 per barrel | **Up 12.34%** |
| **10-Year interest rate** | 4.55% | **Flat (about 0.00 points)** |
| **Bonds** (TLT fund) | 84.71 | **Up 0.28%** |
| **VIX** (how scared traders are; lower = calmer) | 18.24 | **Up 21.36%** |
| **Bitcoin** | $62,914 | **Down 1.89%** |

**In plain words:** Fear rose as VIX moved up 21.36%. Oil was up 12.34%, Bitcoin was down 1.89%, and bonds were up 0.28% as the 10-year yield was little changed.

---

## 11 Parts of the Stock Market (S&P sectors)

Each row is one industry group in the S&P 500.

| Rank | Industry group | Up or down this week |
|------|----------------|----------------------|
| 1 | Energy (oil & gas companies) | **Up 4.36%** |
| 2 | Real estate | **Up 3.06%** |
| 3 | Consumer staples (food, toothpaste, etc.) | **Up 2.51%** |
| 4 | Financials (banks, insurance) | Up 1.55% |
| 5 | Health care | Up 1.09% |
| 6 | Utilities (power, water) | Up 0.78% |
| 7 | Materials (chemicals, metals, etc.) | Up 0.11% |
| 8 | Industrials | Down 0.87% |
| 9 | Consumer discretionary (cars, hotels, shopping) | **Down 0.90%** |
| 10 | Communication (phones, media, ads) | **Down 1.07%** |
| 11 | Technology | **Down 6.04%** |

### Best 3 this week
1. **Energy (oil & gas companies)** — up 4.36%. Move based on oil and gas producers via XLE.
2. **Real estate** — up 3.06%. Move based on property and REIT stocks via XLRE.
3. **Consumer staples (food, toothpaste, etc.)** — up 2.51%. Move based on defensive food and household products via XLP.

### Worst 3 this week
1. **Technology** — down 6.04%. Move based on software, chips, and hardware via XLK.
2. **Communication (phones, media, ads)** — down 1.07%. Move based on telecom, media, and internet platforms via XLC.
3. **Consumer discretionary (cars, hotels, shopping)** — down 0.90%. Move based on consumer spending-sensitive stocks via XLY.

**In plain words:** Sector breadth showed a mixed market: 7 of 11 available sectors finished green. Energy (oil & gas companies) led at up 4.36%, while Technology lagged at down 6.04%.

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
- Sources accessed: Friday, July 17, 2026
