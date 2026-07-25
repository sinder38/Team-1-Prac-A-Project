# Week 06 Market Report (2026)

**Week ended:** Friday, June 26, 2026
**Days the market was open:** 5

This file lists how the main markets moved last week. **Closing value** = price at the end of Friday. **Weekly change** = up or down for the whole week.

---

## Main Stock Indexes (3 we track)

These are the big U.S. stock benchmarks we score each week.

| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
| S&P 500 — large U.S. companies | SPX | 7,354.02 | **Down 1.95%** |
| Nasdaq 100 — mostly tech | NDX | 29,118.24 | **Down 4.24%** |
| Russell 2000 — smaller companies | IWM | 299.83 | **Up 1.43%** |

**In plain words:** 1 of 3 available index readings rose and 2 fell. IWM led with a up 1.43% move, while NDX was the weakest at down 4.24%.

---

## Other Important Markets

Gold, oil, bonds, fear gauge (VIX), and crypto.

| What it is | Friday close | Up or down this week |
|------------|--------------|----------------------|
| **Gold** | $4,079 per ounce | **Down 3.44%** |
| **Oil** (U.S. crude) | $69.23 per barrel | **Down 9.62%** |
| **10-Year interest rate** | 4.38% | **Slightly lower (about 0.08 points)** |
| **Bonds** (TLT fund) | 87.04 | **Up 0.70%** |
| **VIX** (how scared traders are; lower = calmer) | 18.41 | **Up 12.26%** |
| **Bitcoin** | $60,016 | **Down 5.55%** |

**In plain words:** Fear rose as VIX moved up 12.26%. Oil was down 9.62%, Bitcoin was down 5.55%, and bonds were up 0.70% as the 10-year yield edged down.

---

## 11 Parts of the Stock Market (S&P sectors)

Each row is one industry group in the S&P 500.

| Rank | Industry group | Up or down this week |
|------|----------------|----------------------|
| 1 | Health care | **Up 7.80%** |
| 2 | Real estate | **Up 4.05%** |
| 3 | Utilities (power, water) | **Up 3.88%** |
| 4 | Consumer staples (food, toothpaste, etc.) | Up 2.40% |
| 5 | Energy (oil & gas companies) | Up 0.85% |
| 6 | Industrials | Up 0.41% |
| 7 | Financials (banks, insurance) | Up 0.35% |
| 8 | Materials (chemicals, metals, etc.) | Down 0.03% |
| 9 | Consumer discretionary (cars, hotels, shopping) | **Down 2.19%** |
| 10 | Communication (phones, media, ads) | **Down 2.74%** |
| 11 | Technology | **Down 5.28%** |

### Best 3 this week
1. **Health care** — up 7.80%. Move based on health care and pharmaceuticals via XLV.
2. **Real estate** — up 4.05%. Move based on property and REIT stocks via XLRE.
3. **Utilities (power, water)** — up 3.88%. Move based on regulated power and water utilities via XLU.

### Worst 3 this week
1. **Technology** — down 5.28%. Move based on software, chips, and hardware via XLK.
2. **Communication (phones, media, ads)** — down 2.74%. Move based on telecom, media, and internet platforms via XLC.
3. **Consumer discretionary (cars, hotels, shopping)** — down 2.19%. Move based on consumer spending-sensitive stocks via XLY.

**In plain words:** Sector breadth showed a mixed market: 7 of 11 available sectors finished green. Health care led at up 7.80%, while Technology lagged at down 5.28%.

---

## Charts & Screenshots

Saved in the **evidence** folder:

| What the picture shows | File name |
|------------------------|-----------|
| 1-week performance chart (Yahoo Finance) | [finviz_1W_2026_W26.png](./finviz_1W_2026_W26.png) |
| S&P 500 sector heatmap (Yahoo Finance) | [finviz_sectors_5D_2026_W26.png](./finviz_sectors_5D_2026_W26.png) |

## Where the numbers came from

- 1-week performance chart generated from Yahoo Finance weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- S&P 500 sector heatmap generated from Yahoo Finance sector ETF weekly returns (matplotlib)
- Yahoo Finance adjusted daily close data via yfinance for SPX (^GSPC), NDX (^NDX), IWM, Gold (GC=F), Oil (CL=F), TLT, VIX (^VIX), Bitcoin (BTC-USD), and sector ETFs
- 10-year Treasury yield from FRED series DGS10
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC
- Sources accessed: Saturday, July 25, 2026
