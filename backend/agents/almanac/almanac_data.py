"""Encoded seasonal data for the Almanac Agent.

This first software increment focuses on the next several sprint weeks. The
structure is intentionally simple so more months and exact Almanac figures can
be added without changing the agent interface.
"""

MONTHLY_STATS = {
    5: {
        "month": "May",
        "sp500": "ranks #8 of 12 months. Up 61% of the time. Avg +0.3% normally.",
        "midterm": "Midterm year May avg: -0.7% for S&P 500.",
        "nasdaq": "avg +1.1%, ranks #5 normally.",
        "russell": "avg +1.3%, ranks #4 normally.",
        "monthly_bias": "Mixed",
    },
    6: {
        "month": "June",
        "sp500": "ranks #9 of 12 months normally. Ranks #12 in midterm year - dead last.",
        "midterm": "Midterm year June avg: about -2.1% for S&P 500 in our team notes.",
        "nasdaq": "avg +1.0%, ranks #9 normally.",
        "russell": "avg +0.8%, ranks #9 normally.",
        "monthly_bias": "Bearish",
    },
    7: {
        "month": "July",
        "sp500": "historically one of the stronger summer months, with early-July strength often carrying the month.",
        "midterm": "Midterm-year context still sits inside the Q2-Q3 Weak Spot, so normal July strength should be discounted.",
        "nasdaq": "historically strong in July, especially around the first-half to second-half turn.",
        "russell": "small caps can lag if rates stay high, even when July seasonality is supportive.",
        "monthly_bias": "Mixed",
    },
}


WEEKLY_PATTERNS = {
    (6, 3): {
        "label": "Mid-June Week, 15-19 June",
        "name": "Mid-June weakness / CPI follow-through week",
        "bullets": [
            "June midterm-year weakness remains the main seasonal background.",
            "The market is still inside the Q2-Q3 Weak Spot, so rallies should be treated carefully.",
            "A holiday-shortened week around Juneteenth can reduce liquidity and make moves less reliable.",
            "Net: bearish-neutral lean unless macro data forces a clear risk-on reversal.",
        ],
        "seasonal_bias": "Bearish",
        "confidence": "Medium",
        "thesis": (
            "Seasonality is still a headwind in mid-June because June is the weakest "
            "month in the midterm-year pattern. Technology seasonality is the main "
            "positive offset, but the broader Almanac setup stays cautious."
        ),
    },
    (6, 4): {
        "label": "Late June Week, 22-26 June",
        "name": "Late-June / quarter-end positioning",
        "bullets": [
            "Late June can see quarter-end positioning and rebalancing flows.",
            "Midterm-year June remains weak even if short-term bounces appear.",
            "Summer trading volume may start to thin, which can exaggerate moves.",
            "Net: mixed, with bearish seasonal context but possible quarter-end support.",
        ],
        "seasonal_bias": "Mixed",
        "confidence": "Low-Medium",
        "thesis": (
            "Late June has mixed signals. The midterm-year June backdrop is still "
            "negative, but quarter-end positioning can create short-term support. "
            "The Almanac signal should be used as a caution flag rather than a high "
            "confidence directional call."
        ),
    },
    (6, 5): {
        "label": "Turn-of-Month Week, 29 June-3 July",
        "name": "End-of-quarter / early-July transition",
        "bullets": [
            "The week crosses from weak midterm-year June into stronger early-July seasonality.",
            "Month-end and quarter-end flows may support large-cap indexes.",
            "The Independence Day holiday period can reduce volume and increase noise.",
            "Net: mixed to slightly bullish if risk appetite improves.",
        ],
        "seasonal_bias": "Mixed",
        "confidence": "Low-Medium",
        "thesis": (
            "This week is a transition from June weakness into early-July support. "
            "The signal is mixed because holiday liquidity and quarter-end flows can "
            "overpower the normal monthly pattern."
        ),
    },
    (7, 1): {
        "label": "Early July Week, 6-10 July",
        "name": "Early-July strength",
        "bullets": [
            "Early July is often one of the more constructive parts of the summer calendar.",
            "New-month and second-half inflows can support index performance.",
            "The midterm-year Weak Spot still argues against overconfidence.",
            "Net: modest bullish lean, but confidence should stay moderate.",
        ],
        "seasonal_bias": "Bullish",
        "confidence": "Medium",
        "thesis": (
            "Early July is the best seasonal window in this covered period. The "
            "Almanac lean turns more constructive, but the midterm-year Weak Spot "
            "means the team should avoid treating it as a guaranteed rally."
        ),
    },
    (7, 2): {
        "label": "Second July Week, 13-17 July",
        "name": "Post-holiday July follow-through",
        "bullets": [
            "July strength can continue after the holiday period if breadth confirms.",
            "Technology seasonality remains supportive through July.",
            "If rates or inflation pressure rise again, small caps may not benefit from the seasonal setup.",
            "Net: cautiously bullish for Nasdaq/technology, more mixed for small caps.",
        ],
        "seasonal_bias": "Mixed",
        "confidence": "Medium",
        "thesis": (
            "The second week of July keeps some positive seasonal support, especially "
            "for technology. The signal is less clean for Russell 2000 because small "
            "caps are more sensitive to rates and risk appetite."
        ),
    },
}


SECTOR_WINDOWS = [
    {
        "sector": "Technology (XLK)",
        "bias": "Bullish",
        "window": "seasonal LONG window (March-July). Supports Nasdaq while the window remains active.",
    },
    {
        "sector": "Banking / Financials (XLF)",
        "bias": "Bearish",
        "window": "seasonal SHORT window (May-July). Headwind for banks and financials.",
    },
    {
        "sector": "Gold / Silver",
        "bias": "Bearish",
        "window": "seasonal SHORT window (mid-May-June). Weakens after spring strength.",
    },
    {
        "sector": "Materials (XLB)",
        "bias": "Bearish",
        "window": "seasonal SHORT window (May-October). Six-month seasonal headwind.",
    },
    {
        "sector": "Oil / Energy (XLE)",
        "bias": "Bearish",
        "window": "seasonal SHORT begins in early June, but geopolitical oil spikes can override it.",
    },
    {
        "sector": "Healthcare (XLV)",
        "bias": "Neutral",
        "window": "defensive sector; not a strong seasonal LONG/SHORT signal in the current sprint notes.",
    },
]


SOURCE_NOTE = (
    "Stock Trader's Almanac 2026 team notes from W02/W03, plus public Stock "
    "Trader's Almanac June/July seasonal summaries. Encoded for sprint W4-W8 "
    "software increment."
)
