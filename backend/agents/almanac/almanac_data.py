"""Encoded seasonal data for the Almanac Agent.

The first software increment focuses on W4-W8 because those are the next
prediction weeks. The Jan-Dec monthly records are still included so the
support encoder role can fill missing Stock Trader's Almanac figures without
changing the agent code.

This file is intentionally plain Python data. A teammate should be able to add
or correct an Almanac figure here without touching the logic in
almanac_agent.py.
"""


def _index_stat(
    *,
    avg_return: float | None = None,
    rank: int | None = None,
    up_pct: int | None = None,
    note: str = "",
    verified: bool = False,
    source: str = "",
) -> dict:
    """Create one monthly stat record for SPX, Nasdaq, or Russell.

    Use None when a number is not verified yet. The agent will still render the
    note and say that encoder verification is needed.
    """
    return {
        "avg_return": avg_return,
        "rank": rank,
        "up_pct": up_pct,
        "note": note,
        "verified": verified,
        "source": source,
    }


def _midterm_stat(
    *,
    avg_return: float | None = None,
    rank: int | None = None,
    note: str = "",
    verified: bool = False,
    source: str = "",
) -> dict:
    """Create one midterm-year record.

    The midterm field is mostly about the S&P 500 because our manual W2/W3
    notes used the midterm-year S&P context as the main cycle signal.
    """
    return {
        "avg_return": avg_return,
        "rank": rank,
        "note": note,
        "verified": verified,
        "source": source,
    }


# MONTHLY_STATS uses month numbers as keys:
#   1 = January, 2 = February, ... 12 = December.
#
# For each month we keep:
# - sp500: normal S&P 500 monthly stats
# - midterm: special midterm-year context, important because 2026 is midterm
# - nasdaq: Nasdaq / NDX monthly stats
# - russell: Russell 2000 / IWM monthly stats
# - monthly_bias: simple label used by the agent when no weekly pattern exists
#
# verified=True means the value came from team notes already used in W2/W3.
# verified=False means the support encoder should still check the Almanac page.
MONTHLY_STATS = {
    1: {
        "month": "January",
        "sp500": _index_stat(
            note="Exact January S&P 500 stats still need Almanac page verification."
        ),
        "midterm": _midterm_stat(
            note="Midterm year January adjustment not verified yet."
        ),
        "nasdaq": _index_stat(
            note="Exact January Nasdaq stats still need Almanac page verification."
        ),
        "russell": _index_stat(
            note="Exact January Russell 2000 stats still need Almanac page verification."
        ),
        "monthly_bias": "Mixed",
    },
    2: {
        "month": "February",
        "sp500": _index_stat(
            note="Exact February S&P 500 stats still need Almanac page verification."
        ),
        "midterm": _midterm_stat(
            note="Midterm year February adjustment not verified yet."
        ),
        "nasdaq": _index_stat(
            note="Exact February Nasdaq stats still need Almanac page verification."
        ),
        "russell": _index_stat(
            note="Exact February Russell 2000 stats still need Almanac page verification."
        ),
        "monthly_bias": "Mixed",
    },
    3: {
        "month": "March",
        "sp500": _index_stat(
            note="Exact March S&P 500 stats still need Almanac page verification."
        ),
        "midterm": _midterm_stat(
            note="Midterm year March adjustment not verified yet."
        ),
        "nasdaq": _index_stat(
            note=(
                "Technology seasonality begins to improve during the March-July "
                "window in our team notes."
            )
        ),
        "russell": _index_stat(
            note="Exact March Russell 2000 stats still need Almanac page verification."
        ),
        "monthly_bias": "Mixed",
    },
    4: {
        "month": "April",
        "sp500": _index_stat(
            note="Exact April S&P 500 stats still need Almanac page verification."
        ),
        "midterm": _midterm_stat(
            note="Midterm year April adjustment not verified yet."
        ),
        "nasdaq": _index_stat(
            note="Exact April Nasdaq stats still need Almanac page verification."
        ),
        "russell": _index_stat(
            note="Exact April Russell 2000 stats still need Almanac page verification."
        ),
        "monthly_bias": "Mixed",
    },
    5: {
       "month": "May",
       "sp500": _index_stat(
           avg_return=0.3,
           rank=8,
           up_pct=61,
           verified=True,
           source="data/almanac/almanac_agent_W22.md",
       ),
       "midterm": _midterm_stat(
           avg_return=-0.7,
           note="This is the active 2026 context for S&P 500.",
           verified=True,
           source="data/almanac/almanac_agent_W22.md",
       ),
       "nasdaq": _index_stat(
           avg_return=1.1,
           rank=5,
           verified=True,
           source="data/almanac/almanac_agent_W22.md",
       ),
       "russell": _index_stat(
           avg_return=1.3,
           rank=4,
           verified=True,
           source="data/almanac/almanac_agent_W22.md",
       ),
       "monthly_bias": "Mixed",
    },
    6: {
       "month": "June",
       "sp500": _index_stat(
           rank=9,
           note="Normal June ranks #9 of 12 months.",
           verified=True,
           source="data/almanac/almanac_agent_W23.md",
       ),
       "midterm": _midterm_stat(
           avg_return=-2.1,
           rank=12,
           note="Dead last in the midterm-year pattern for S&P 500.",
           verified=True,
           source="data/almanac/almanac_agent_W23.md",
       ),
       "nasdaq": _index_stat(
           avg_return=1.0,
           rank=9,
           verified=True,
           source="data/almanac/almanac_agent_W23.md",
       ),
       "russell": _index_stat(
           avg_return=0.8,
           rank=9,
           verified=True,
           source="data/almanac/almanac_agent_W23.md",
       ),
       "monthly_bias": "Bearish",
    },
    7: {
        "month": "July",
        "sp500": _index_stat(
            note=(
                "Historically one of the stronger summer months, with early-July "
                "strength often carrying the month."
            )
        ),
        "midterm": _midterm_stat(
            note=(
                "Midterm-year context still sits inside the Q2-Q3 Weak Spot, "
                "so normal July strength should be discounted."
            )
        ),
        "nasdaq": _index_stat(
            note=(
                "Historically strong in July, especially around the first-half "
                "to second-half turn."
            )
        ),
        "russell": _index_stat(
            note=(
                "Small caps can lag if rates stay high, even when July "
                "seasonality is supportive."
            )
        ),
        "monthly_bias": "Mixed",
    },
    8: {
        "month": "August",
        "sp500": _index_stat(
            note="Exact August S&P 500 stats still need Almanac page verification."
        ),
        "midterm": _midterm_stat(
            note="Midterm-year context remains inside the Q2-Q3 Weak Spot in our team notes."
        ),
        "nasdaq": _index_stat(
            note="Exact August Nasdaq stats still need Almanac page verification."
        ),
        "russell": _index_stat(
            note="Exact August Russell 2000 stats still need Almanac page verification."
        ),
        "monthly_bias": "Mixed",
    },
    9: {
        "month": "September",
        "sp500": _index_stat(
            note=(
                "September is normally treated cautiously in Almanac-style "
                "seasonality; exact figures still need verification."
            )
        ),
        "midterm": _midterm_stat(
            note="Midterm year September adjustment not verified yet."
        ),
        "nasdaq": _index_stat(
            note="Exact September Nasdaq stats still need Almanac page verification."
        ),
        "russell": _index_stat(
            note="Exact September Russell 2000 stats still need Almanac page verification."
        ),
        "monthly_bias": "Bearish",
    },
    10: {
        "month": "October",
        "sp500": _index_stat(
            note="Exact October S&P 500 stats still need Almanac page verification."
        ),
        "midterm": _midterm_stat(
            note=(
                "Q4 Sweet Spot can begin to matter later in the year, but exact "
                "midterm-year adjustment is not verified yet."
            )
        ),
        "nasdaq": _index_stat(
            note="Exact October Nasdaq stats still need Almanac page verification."
        ),
        "russell": _index_stat(
            note="Exact October Russell 2000 stats still need Almanac page verification."
        ),
        "monthly_bias": "Mixed",
    },
    11: {
        "month": "November",
        "sp500": _index_stat(
            note="Exact November S&P 500 stats still need Almanac page verification."
        ),
        "midterm": _midterm_stat(
            note=(
                "Q4 Sweet Spot context is normally more constructive after the "
                "Q2-Q3 Weak Spot, but exact figures still need verification."
            )
        ),
        "nasdaq": _index_stat(
            note="Exact November Nasdaq stats still need Almanac page verification."
        ),
        "russell": _index_stat(
            note="Exact November Russell 2000 stats still need Almanac page verification."
        ),
        "monthly_bias": "Bullish",
    },
    12: {
        "month": "December",
        "sp500": _index_stat(
            note="Exact December S&P 500 stats still need Almanac page verification."
        ),
        "midterm": _midterm_stat(
            note=(
                "Q4 Sweet Spot context remains relevant, but exact midterm-year "
                "adjustment is not verified yet."
            )
        ),
        "nasdaq": _index_stat(
            note="Exact December Nasdaq stats still need Almanac page verification."
        ),
        "russell": _index_stat(
            note="Exact December Russell 2000 stats still need Almanac page verification."
        ),
        "monthly_bias": "Bullish",
    },
}

# MIDTERM_INDEX_ADJUSTMENTS stores verified midterm-year data.
#
# 2026 is a midterm election year, so some monthly averages may differ from
# normal seasonality. The key is the month number, for example 5 = May and
# 6 = June.
#
# Use None when a value was not verified in the W22/W23 team notes.
# This is mainly for data tracking and future encoder follow-up.

MIDTERM_INDEX_ADJUSTMENTS = {
    5: {
        "month": "May",
        "sp500_avg_return": -0.7,
        "dow_avg_return": None,
        "nasdaq_avg_return": None,
        "russell_avg_return": None,
        "note": "Only S&P 500 May midterm average was verified in the W22 team output.",
        "source": "data/almanac/almanac_agent_W22.md",
        "verified": True,
    },
    6: {
        "month": "June",
        "sp500_avg_return": -2.1,
        "dow_avg_return": -1.8,
        "nasdaq_avg_return": -1.5,
        "russell_avg_return": None,
        "note": "June midterm-year context is bearish. Russell 2000 midterm average was not verified in the team notes.",
        "source": "data/almanac/almanac_agent_W22.md and data/almanac/almanac_agent_W23.md",
        "verified": True,
    },
}

# WEEKLY_PATTERNS is more specific than MONTHLY_STATS.
#
# The key is (month, week_of_month). For example:
# - (6, 3) = third week of June
# - (7, 1) = first week of July
#
# Each entry gives the agent enough detail to write the "SPECIFIC WEEK PATTERN"
# section in the Markdown output.
WEEKLY_PATTERNS = {
      (5, 4): {
          "label": "Memorial Day Week, 26-30 May",
          "name": "Memorial Day week / week after options expiration",
          "description": (
              "Memorial Day week has a bearish lean, but the week after options "
              "expiration gives a mild bullish offset."
          ),
          "tendency": "Mixed / slight bearish",
          "strength": "Low-Medium",
          "applicable_dates": "26-30 May 2026",
          "source": "data/almanac/almanac_agent_W22.md",
          "bullets": [
              "Memorial Day week: Dow down 17 of last 29. Bearish lean.",
              "Day after Memorial Day: Dow down 8 of last 10. Recent trend bearish.",
              "Week after options expiration: S&P up 30 of 45, avg +0.40%. Mild bullish offset.",
              "Net: mixed / slight bearish lean.",
          ],
          "seasonal_bias": "Mixed",
          "confidence": "Low-Medium",
          "thesis": (
              "Seasonality suggests caution in late May during a midterm year. "
              "Technology is the one seasonal bright spot. Banking and Materials "
              "face active headwinds. Conflicting week patterns keep confidence low."
          ),
      },
    (6, 1): {
          "label": "Early June Week, 2-6 June",
          "name": "Early June midterm-year weakness",
          "description": (
              "Early June has a slight bearish lean because June is weak in the "
              "midterm-year pattern, with no strong holiday pattern to offset it."
          ),
          "tendency": "Slight bearish",
          "strength": "Medium",
          "applicable_dates": "2-6 June 2026",
          "source": "data/almanac/almanac_agent_W23.md",
          "bullets": [
              "No specific holiday pattern is active this week.",
              "Early June is transitional as summer doldrums begin.",
              "Volume tends to decline in early June as institutional activity slows.",
              "NFP on Friday 5 June is the dominant market event this week.",
              (
                  "Net: slight bearish lean from June midterm-year context. "
                  "No strong specific week pattern."
              ),
          ],
          "seasonal_bias": "Bearish",
          "confidence": "Medium",
          "thesis": (
              "June 2026 is the worst month of the year in a midterm cycle. "
              "Four sectors now have active seasonal short signals. Technology "
              "remains the one seasonal bright spot. Summer doldrums beginning "
              "means volume may decline and moves may be exaggerated."
          ),
      },
    (6, 3): {
        "label": "Mid-June Week, 15-19 June",
        "name": "Mid-June weakness / CPI follow-through week",
        "tendency": "Bearish-neutral",
        "strength": "Moderate",
        "bullets": [
            "Pattern tendency: bearish-neutral. Pattern strength: moderate.",
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
        "tendency": "Mixed",
        "strength": "Low-Medium",
        "bullets": [
            "Pattern tendency: mixed. Pattern strength: low-medium.",
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
        "tendency": "Mixed to slightly bullish",
        "strength": "Low-Medium",
        "bullets": [
            "Pattern tendency: mixed to slightly bullish. Pattern strength: low-medium.",
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
        "tendency": "Bullish",
        "strength": "Moderate",
        "bullets": [
            "Pattern tendency: bullish. Pattern strength: moderate.",
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
        "tendency": "Mixed",
        "strength": "Moderate",
        "bullets": [
            "Pattern tendency: mixed. Pattern strength: moderate.",
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

# These sector windows come from the Almanac-style seasonal notes used by the
# team. The agent converts each entry into a SectorSignal object.
#
# Keep the words "seasonal LONG" or "seasonal SHORT" in the window text when
# possible, because the current validator checks for those phrases.
SECTOR_WINDOWS = [
    {
        "sector": "Technology (XLK)",
        "bias": "Bullish",
        "direction": "Long",
        "start_month": "March",
        "end_month": "July",
        "window": "seasonal LONG window (March-July). Supports Nasdaq.",
        "source": "data/almanac/almanac_agent_W22.md and data/almanac/almanac_agent_W23.md",
    },
    {
        "sector": "Banking / Financials (XLF)",
        "bias": "Bearish",
        "direction": "Short",
        "start_month": "May",
        "end_month": "July",
        "window": "seasonal SHORT window (May-July). Headwind for financials.",
        "source": "data/almanac/almanac_agent_W22.md and data/almanac/almanac_agent_W23.md",
    },
    {
        "sector": "Gold / Silver",
        "bias": "Bearish",
        "direction": "Short",
        "start_month": "mid-May",
        "end_month": "June",
        "window": "seasonal SHORT window (mid-May-June).",
        "source": "data/almanac/almanac_agent_W22.md and data/almanac/almanac_agent_W23.md",
    },
    {
        "sector": "Materials (XLB)",
        "bias": "Bearish",
        "direction": "Short",
        "start_month": "May",
        "end_month": "October",
        "window": "seasonal SHORT window (May-October).",
        "source": "data/almanac/almanac_agent_W22.md and data/almanac/almanac_agent_W23.md",
    },
    {
        "sector": "Oil / Energy (XLE)",
        "bias": "Bearish",
        "direction": "Short",
        "start_month": "early June",
        "end_month": None,
        "window": "seasonal SHORT begins in early June.",
        "source": "data/almanac/almanac_agent_W23.md",
    },
]

# This is not used directly in the report yet, but it is useful for reviewers.
# It explains what is already covered and what the support data encoder role
# should improve later.
DATA_COVERAGE = {
    "monthly_records": "Jan-Dec keys exist; exact numeric fields are filled where the team has already verified them.",
    "verified_months": ["May", "June"],
    "verified_sources": [
        "data/almanac/almanac_agent_W22.md",
        "data/almanac/almanac_agent_W23.md",
    ],
    "covered_sprint_weeks": ["W22", "W23", "W25", "W26", "W27", "W28", "W29"],
    "support_encoder_completed": [
        "Cross-checked May monthly stats against W22 output.",
        "Cross-checked June monthly stats against W23 output.",
        "Encoded Memorial Day week and Early June weekly patterns.",
        "Added structured sector seasonality windows for current sprint sectors.",
        "Marked unverified Jan-Dec monthly values as follow-up instead of guessing.",
    ],
    "encoder_follow_up": [
        "Fill exact S&P 500 average return, rank, and up percentage for months outside May/June.",
        "Fill exact Nasdaq and Russell 2000 monthly stats where not already verified.",
        "Fill exact midterm-year monthly adjustments for months outside May/June.",
        "Add more named weekly patterns as later sprint dates become clear.",
    ],
}

# The Markdown output uses this in the final Source line. It is deliberately
# honest about which data is already encoded and which parts still need exact
# page verification.
SOURCE_NOTE = (
    "Stock Trader's Almanac 2026 team notes from W22/W23, plus public Stock "
    "Trader's Almanac June/July seasonal summaries. W25-W29 entries are encoded "
    "for the first software increment. Jan-Dec monthly records are structured "
    "for data encoder follow-up where exact page figures are not yet verified."
)
