# Week 10 Market Report (2026)

**Week ended:** Friday, July 24, 2026
**Days the market was open:** 5

This file lists how the main markets moved last week. **Closing value** = price at the end of Friday. **Weekly change** = up or down for the whole week.

---

## Main Stock Indexes (3 we track)

These are the big U.S. stock benchmarks we score each week.

| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
| S&P 500 — large U.S. companies | SPX | 7,411.98 | **Down 0.61%** |
| Nasdaq 100 — mostly tech | NDX | 28,128.34 | **Down 1.62%** |
| Russell 2000 — smaller companies | IWM | 291.17 | **Down 0.98%** |

**In plain words:** All 3 available index readings finished lower. SPX led with a down 0.61% move, while NDX was the weakest at down 1.62%.

---

## Other Important Markets

Gold, oil, bonds, fear gauge (VIX), and crypto.

| What it is | Friday close | Up or down this week |
|------------|--------------|----------------------|
| **Gold** | $4,056 per ounce | **Up 1.07%** |
| **Oil** (U.S. crude) | $90.47 per barrel | **Up 9.67%** |
| **10-Year interest rate** | 4.71% | **Slightly higher (about 0.16 points)** |
| **Bonds** (TLT fund) | 83.25 | **Down 1.50%** |
| **VIX** (how scared traders are; lower = calmer) | 18.58 | **Down 1.01%** |
| **Bitcoin** | $64,113 | **Up 0.33%** |

**In plain words:** Fear eased as VIX moved down 1.01%. Oil was up 9.67%, Bitcoin was up 0.33%, and bonds were down 1.50% as the 10-year yield edged up.

---

## 11 Parts of the Stock Market (S&P sectors)

Each row is one industry group in the S&P 500.

| Rank | Industry group | Up or down this week |
|------|----------------|----------------------|
| 1 | Energy (oil & gas companies) | **Up 3.36%** |
| 2 | Utilities (power, water) | **Up 2.48%** |
| 3 | Industrials | **Up 1.81%** |
| 4 | Materials (chemicals, metals, etc.) | Up 1.44% |
| 5 | Real estate | Up 1.17% |
| 6 | Health care | Up 0.92% |
| 7 | Technology | Up 0.17% |
| 8 | Financials (banks, insurance) | Up 0.09% |
| 9 | Consumer staples (food, toothpaste, etc.) | **Down 1.24%** |
| 10 | Communication (phones, media, ads) | **Down 3.93%** |
| 11 | Consumer discretionary (cars, hotels, shopping) | **Down 5.22%** |

### Best 3 this week
1. **Energy (oil & gas companies)** — up 3.36%. Move based on oil and gas producers via XLE.
2. **Utilities (power, water)** — up 2.48%. Move based on regulated power and water utilities via XLU.
3. **Industrials** — up 1.81%. Move based on manufacturers, transport, and machinery via XLI.

### Worst 3 this week
1. **Consumer discretionary (cars, hotels, shopping)** — down 5.22%. Move based on consumer spending-sensitive stocks via XLY.
2. **Communication (phones, media, ads)** — down 3.93%. Move based on telecom, media, and internet platforms via XLC.
3. **Consumer staples (food, toothpaste, etc.)** — down 1.24%. Move based on defensive food and household products via XLP.

**In plain words:** Sector breadth showed a broad rally: 8 of 11 available sectors finished green. Energy (oil & gas companies) led at up 3.36%, while Consumer discretionary (cars, hotels, shopping) lagged at down 5.22%.

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
- Sources accessed: Friday, July 24, 2026
