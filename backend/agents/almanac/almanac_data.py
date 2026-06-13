# Almanac seasonal data encoded from Stock Trader's Almanac 2026
# Source: Stock Trader's Almanac 2026, pp. 65–66, p. 94, pp. 10–11

# ── S&P 500 Monthly Statistics ────────────────────────────────────────────────
# avg_return: normal average % return
# up_pct: % of years the month was up
# rank: rank among 12 months (1 = best)

SP500_MONTHLY = {
    "January":   {"avg_return": 1.0,  "up_pct": 62, "rank": 4},
    "February":  {"avg_return": 0.1,  "up_pct": 57, "rank": 9},
    "March":     {"avg_return": 0.8,  "up_pct": 62, "rank": 6},
    "April":     {"avg_return": 1.5,  "up_pct": 67, "rank": 2},
    "May":       {"avg_return": 0.3,  "up_pct": 61, "rank": 8},
    "June":      {"avg_return": 0.2,  "up_pct": 56, "rank": 9},
    "July":      {"avg_return": 1.2,  "up_pct": 61, "rank": 3},
    "August":    {"avg_return": 0.1,  "up_pct": 55, "rank": 10},
    "September": {"avg_return": -0.6, "up_pct": 47, "rank": 12},
    "October":   {"avg_return": 0.8,  "up_pct": 61, "rank": 7},
    "November":  {"avg_return": 1.5,  "up_pct": 65, "rank": 1},
    "December":  {"avg_return": 1.4,  "up_pct": 73, "rank": 5},
}

# ── Nasdaq Monthly Statistics 
NASDAQ_MONTHLY = {
    "January":   {"avg_return": 2.5,  "up_pct": 65, "rank": 2},
    "February":  {"avg_return": 0.8,  "up_pct": 58, "rank": 7},
    "March":     {"avg_return": 0.5,  "up_pct": 58, "rank": 8},
    "April":     {"avg_return": 2.1,  "up_pct": 67, "rank": 3},
    "May":       {"avg_return": 1.1,  "up_pct": 61, "rank": 5},
    "June":      {"avg_return": 1.0,  "up_pct": 56, "rank": 6},
    "July":      {"avg_return": 2.6,  "up_pct": 63, "rank": 1},
    "August":    {"avg_return": 0.5,  "up_pct": 54, "rank": 9},
    "September": {"avg_return": -0.8, "up_pct": 46, "rank": 12},
    "October":   {"avg_return": 0.4,  "up_pct": 57, "rank": 10},
    "November":  {"avg_return": 2.0,  "up_pct": 65, "rank": 4},
    "December":  {"avg_return": 1.8,  "up_pct": 72, "rank": 11},
}

# ── Russell 2000 Monthly Statistics 
RUSSELL2000_MONTHLY = {
    "January":   {"avg_return": 2.4,  "up_pct": 68, "rank": 1},
    "February":  {"avg_return": 0.9,  "up_pct": 60, "rank": 6},
    "March":     {"avg_return": 1.0,  "up_pct": 61, "rank": 5},
    "April":     {"avg_return": 1.8,  "up_pct": 65, "rank": 3},
    "May":       {"avg_return": 1.3,  "up_pct": 63, "rank": 4},
    "June":      {"avg_return": 0.8,  "up_pct": 57, "rank": 9},
    "July":      {"avg_return": 1.9,  "up_pct": 64, "rank": 2},
    "August":    {"avg_return": 0.3,  "up_pct": 53, "rank": 10},
    "September": {"avg_return": -1.0, "up_pct": 45, "rank": 12},
    "October":   {"avg_return": 0.7,  "up_pct": 58, "rank": 8},
    "November":  {"avg_return": 2.2,  "up_pct": 67, "rank": 7},
    "December":  {"avg_return": 1.6,  "up_pct": 70, "rank": 11},
}

# ── Midterm Year Adjustments 
# avg_return: midterm-year specific average % return for S&P 500
# rank: rank among 12 months in midterm years only
# Note: 2026 is a midterm election year — use these instead of normal averages

MIDTERM_YEAR_SP500 = {
    "January":   {"avg_return": 0.5,  "rank": 6},
    "February":  {"avg_return": -0.3, "rank": 9},
    "March":     {"avg_return": 0.2,  "rank": 7},
    "April":     {"avg_return": 0.8,  "rank": 4},
    "May":       {"avg_return": -0.7, "rank": 10},   # W02 reference
    "June":      {"avg_return": -2.1, "rank": 12},   # W03 reference — worst month
    "July":      {"avg_return": -0.5, "rank": 8},
    "August":    {"avg_return": -1.5, "rank": 11},
    "September": {"avg_return": -2.0, "rank": 12},
    "October":   {"avg_return": 2.5,  "rank": 1},    # Midterm bottom — Sweet Spot begins
    "November":  {"avg_return": 3.2,  "rank": 2},
    "December":  {"avg_return": 2.8,  "rank": 3},
}

# ── Sector Seasonality Windows 
# signal: "LONG" (bullish) or "SHORT" (bearish)
# start_month / end_month: inclusive window
# avg_return: 25-year average return during the window
# etf: representative ETF

SECTOR_SEASONALITY = [
    {
        "sector": "Technology",
        "etf": "XLK",
        "signal": "LONG",
        "start_month": "March",
        "end_month": "July",
        "avg_return": 10.9,
        "notes": "Mid-March to mid-July. Strongest seasonal long of any sector.",
    },
    {
        "sector": "Banking",
        "etf": "XLF",
        "signal": "SHORT",
        "start_month": "May",
        "end_month": "July",
        "avg_return": -6.3,
        "notes": "Early May to early July. Headwind for financials.",
    },
    {
        "sector": "Gold/Silver",
        "etf": "XAU",
        "signal": "SHORT",
        "start_month": "May",
        "end_month": "June",
        "avg_return": -6.8,
        "notes": "Mid-May to late June. Often contradicts spot gold price action.",
    },
    {
        "sector": "Materials",
        "etf": "XLB",
        "signal": "SHORT",
        "start_month": "May",
        "end_month": "October",
        "avg_return": -5.1,
        "notes": "Mid-May to mid-October. 6-month seasonal headwind.",
    },
    {
        "sector": "Oil/Energy",
        "etf": "XLE",
        "signal": "SHORT",
        "start_month": "June",
        "end_month": "August",
        "avg_return": -5.7,
        "notes": "Early June to late August. New signal active from W03 sprint.",
    },
    {
        "sector": "Healthcare",
        "etf": "XLV",
        "signal": "LONG",
        "start_month": "October",
        "end_month": "May",
        "avg_return": 8.7,
        "notes": "Early October to early May. Window ended early May — neutral now.",
    },
    {
        "sector": "Utilities",
        "etf": "UTY",
        "signal": "LONG",
        "start_month": "March",
        "end_month": "October",
        "avg_return": 9.3,
        "notes": "Mid-March to early October. Seasonal long but overridden by high 10-year yield (4.60%).",
    },
]

# ── Notable Weekly Patterns 
# tendency: "bullish", "bearish", or "mixed"
# strength: "STRONG", "MODERATE", "WEAK"
# record: human-readable historical record string

WEEKLY_PATTERNS = [
    {
        "name": "Memorial Day Week",
        "description": "The full week containing Memorial Day (last Monday of May)",
        "tendency": "bearish",
        "strength": "MODERATE",
        "record": "Dow down 17 of last 29",
        "applicable": "Last week of May",
        "notes": "Recent record more bearish than 29-year average implies.",
    },
    {
        "name": "Day After Memorial Day",
        "description": "The Tuesday immediately after Memorial Day",
        "tendency": "bearish",
        "strength": "MODERATE",
        "record": "Dow down 8 of last 10",
        "applicable": "Tuesday after Memorial Day",
        "notes": "Strong recent trend — more reliable than full-week pattern.",
    },
    {
        "name": "Week After May Options Expiration",
        "description": "The week following May options expiration Friday",
        "tendency": "bullish",
        "strength": "MODERATE",
        "record": "S&P up 30 of last 45, avg +0.40%",
        "applicable": "Week after third Friday of May",
        "notes": "Mild bullish offset. Conflicts with Memorial Day week bearish pattern.",
    },
    {
        "name": "Week After June Triple Witching",
        "description": "The week after June options/futures expiration (triple witching)",
        "tendency": "bearish",
        "strength": "STRONG",
        "record": "Dow down 28 of last 34",
        "applicable": "Week after third Friday of June",
        "notes": "One of the strongest bearish weekly patterns in the Almanac.",
    },
    {
        "name": "Santa Claus Rally",
        "description": "Last 5 trading days of December + first 2 of January",
        "tendency": "bullish",
        "strength": "STRONG",
        "record": "S&P up 34 of last 45, avg +1.3%",
        "applicable": "Late December to early January",
        "notes": "If Santa Claus does not call, bears may come to Broad and Wall.",
    },
    {
        "name": "First Five Days of January",
        "description": "Performance of S&P in first 5 trading days of January",
        "tendency": "bullish",
        "strength": "MODERATE",
        "record": "Predictive of full-year direction 75% of the time",
        "applicable": "First week of January",
        "notes": "Early Warning System for January Barometer.",
    },
    {
        "name": "January Barometer",
        "description": "As January goes, so goes the year",
        "tendency": "bullish",
        "strength": "STRONG",
        "record": "Accurate 88.7% of the time since 1950",
        "applicable": "Full month of January",
        "notes": "Most reliable annual indicator in the Almanac.",
    },
]

# ── 4-Year Presidential Cycle Context 
PRESIDENTIAL_CYCLE = {
    "current_year": 2026,
    "cycle_year": "midterm",
    "weak_spot": {"start": "Q2", "end": "Q3"},
    "sweet_spot": {"start": "Q4 midterm", "end": "Q2 pre-election"},
    "sp500_avg_weak_spot": -2.5,
    "sp500_avg_sweet_spot": 19.3,
    "notes": (
        "10 of last 16 bear markets bottomed in midterm year October. "
        "Q4 2026 Sweet Spot begins after midterm election results are known. "
        "Full year net gain forecast: +4% to +8% but front-loaded with pain in Q2–Q3."
    ),
}
