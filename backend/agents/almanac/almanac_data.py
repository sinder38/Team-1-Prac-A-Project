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
        "name": "Mid-June weakness / Triple-Witching week",
        "tendency": "Bearish / mixed",
        "strength": "Moderate",
        "bullets": [
            "Monday, June 15: Monday of Triple-Witching Week — Dow down 15 of last 28.",
            "Triple-Witching Week often up in bull markets and down in bears (Almanac p.108).",
            "Wednesday, June 17: FOMC meeting scheduled — policy announcement can swing risk.",
            "Thursday, June 18: June Triple-Witching Day mixed, but down 8 of last 10.",
            "Friday, June 19: Juneteenth National Independence Day — market closed.",
            "Historical performance trends lower, driven heavily by seasonal options-week behaviour.",
            "Net: bearish / mixed. Triple-Witching tends negative, but FOMC can shift sentiment quickly.",
        ],
        "seasonal_bias": "Bearish",
        "confidence": "Medium",
        "thesis": (
            "Mid-June Triple-Witching week carries a bearish historical lean, with "
            "the Dow down 15 of last 28 on Monday and triple-witching Friday down 8 "
            "of last 10. June is already the weakest month in the midterm-year "
            "pattern. The FOMC meeting on Wednesday is the wildcard — a dovish "
            "surprise could offset the seasonal drag, but the Almanac base case "
            "stays cautious heading into a holiday-shortened Friday."
        ),
        "source": "Stock Trader's Almanac 2026 p.87, p.108",
    },
    (6, 4): {
        "label": "Late June Week, 22-26 June",
        "name": "Week after June Triple-Witching",
        "tendency": "Bearish",
        "strength": "Moderate",
        "bullets": [
            "Monday, June 22: Week after June Triple-Witching — Dow down 29 of last 35.",
            "Average loss for S&P 500 since 1990 during this week is -0.8%.",
            "Summer doldrums can begin in late June as institutional activity slows (p.81).",
            "Midterm-year June is dead last among all months for S&P 500 (avg -2.1%).",
            "Net: bearish. Strong historical headwind with no offsetting holiday pattern this week.",
        ],
        "seasonal_bias": "Bearish",
        "confidence": "Medium",
        "thesis": (
            "The week after June Triple-Witching has one of the most consistent "
            "bearish records in the Almanac — the Dow has fallen 29 of the last 35 "
            "post-witching weeks. Combined with June ranking #12 (dead last) in the "
            "midterm-year pattern, the seasonal signal is clearly negative. "
            "Quarter-end positioning may provide some late-week support, but the "
            "historical Almanac base case is bearish heading into late June."
        ),
        "source": "Stock Trader's Almanac 2026 p.89, p.81",
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
        "name": "Early-July holiday week / post-Independence Day",
        "tendency": "Mixed / slightly bullish",
        "strength": "Moderate",
        "bullets": [
            "Monday, July 6: Elevated volatility after Independence Day is common; thin holiday liquidity.",
            "July is the best month of Q3: ranks #3 for Dow (+1.6%) and #3 for S&P 500 (+1.3%) in midterm years.",
            "NASDAQ midterm-year July ranks only #7 with average return -0.8% — tech is a relative drag.",
            "Beware the 'Summer Rally' hype — historically the weakest rally of all seasons (Almanac p.76).",
            "New-month and second-half inflows support large-cap indexes, but tech divergence is notable.",
            "Net: mixed. Strong macro month, but this specific week sees post-holiday volatility and NASDAQ midterm weakness.",
        ],
        "seasonal_bias": "Mixed",
        "confidence": "Medium",
        "thesis": (
            "July is historically the best month of Q3, ranking #3 for the Dow "
            "and S&P 500 in midterm years, so the macro Almanac backdrop is "
            "constructive. However, this particular week carries post-Independence "
            "Day volatility risk, and NASDAQ midterm-year July performance is "
            "actually weak (ranked #7, avg -0.8%). The signal is mixed — the "
            "month is bullishly positioned, but the week itself lacks a clean "
            "directional edge."
        ),
        "source": "Stock Trader's Almanac 2026 p.97, p.99, p.76",
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
    (7, 3): {
        "label": "Third July Week, 20-24 July",
        "name": "Week after July monthly expiration",
        "tendency": "Mixed / slightly bullish",
        "strength": "Medium",
        "bullets": [
            "Week after July monthly expiration: Dow up 17 of last 23.",
            "Historical examples show large swings: 2002 +3.1%, 2006 +3.2%, 2007 -4.2%, 2009 +4.0%, 2010 +3.2%, 2015 -2.9%.",
            "July remains seasonally favorable as the best performing Dow and S&P 500 month of the third quarter.",
            "Midterm-year July ranks #3 for Dow and S&P 500, while NASDAQ midterm-year July ranks #7.",
            "Post-options-expiration trading can create volatility and sharp market moves.",
            "Net: mixed with slight bullish bias, but volatility risk remains elevated.",
        ],
        "seasonal_bias": "Mixed",
        "confidence": "Medium",
        "thesis": (
            "The third week of July combines a favorable July seasonal backdrop "
            "with post-options-expiration volatility. The Dow has advanced 17 of "
            "the last 23 times during the week after July monthly expiration, "
            "creating a slight bullish historical tendency. However, the wide "
            "range of past outcomes shows that this period can produce sharp "
            "moves in either direction, keeping confidence at a medium level."
        ),
    },
    (7, 4): {
        "label": "Late July Week, 27-31 July",
        "name": "End-of-July weakness / transition into August",
        "tendency": "Bearish",
        "strength": "Low-Medium",
        "bullets": [
            "Friday, July 31: Last Trading Day in July has historically been weak.",
            "NASDAQ and S&P 500 are down 12 of the last 20 times on the last trading day of July.",
            "Dow is down 13 of the last 20 times on the last trading day of July.",
            "End-of-month positioning may increase volatility before the August seasonal period.",
            "August begins with a weaker historical seasonal backdrop, especially for Dow and NASDAQ.",
            "Net: slight bearish tendency into the August transition.",
        ],
        "seasonal_bias": "Bearish",
        "confidence": "Low-Medium",
        "thesis": (
            "The final week of July transitions from a historically strong July "
            "seasonal period into the weaker August period. The last trading day "
            "of July has shown a bearish tendency, with the Dow down 13 of the "
            "last 20 occurrences and both the S&P 500 and NASDAQ down 12 of the "
            "last 20. The pattern is not a strong standalone signal, but it "
            "adds caution heading into August."
        ),
        "source": "Stock Trader's Almanac 2026 July/August 2026 section",
    },
    (8, 1): {
        "label": "Early August Week, 3-7 August",
        "name": "First trading days of August weakness",
        "tendency": "Bearish",
        "strength": "Medium",
        "bullets": [
            "Monday, August 3: First Trading Day in August has historically been weak.",
            "Dow has declined 19 of the last 28 times on the first trading day of August.",
            "The first nine trading days of August are historically weak (Almanac pages 74 and 138).",
            "Early August seasonal weakness creates a cautious backdrop after July strength.",
            "Net: bearish seasonal bias during the opening part of August.",
        ],
        "seasonal_bias": "Bearish",
        "confidence": "Medium",
        "thesis": (
            "The beginning of August carries a historically weak seasonal pattern. "
            "The Dow has fallen 19 of the last 28 times on the first trading day "
            "of August, and the first nine trading days of August have also shown "
            "weakness historically. This creates a cautious seasonal setup heading "
            "into the middle of the month."
        ),
        "source": "Stock Trader's Almanac 2026 August 2026 section",
    },
    (8, 2): {
        "label": "Second August Week, 10-14 August",
        "name": "Mid-August seasonal improvement",
        "tendency": "Mixed",
        "strength": "Low-Medium",
        "bullets": [
            "August is historically one of the weakest months in modern market history.",
            "Since 1988, August ranks as the worst Dow month and second worst S&P 500 month.",
            "Mid-August has historically been stronger than the beginning and end of August.",
            "The seasonal pattern improves temporarily in the middle of the month despite August's overall weakness.",
            "Net: mixed. Mid-month strength offsets broader August seasonal weakness.",
        ],
        "seasonal_bias": "Mixed",
        "confidence": "Low-Medium",
        "thesis": (
            "The second week of August sits between two conflicting seasonal signals. "
            "August remains historically weak, ranking as the worst Dow month and "
            "second worst S&P 500 month since 1988, but mid-August has historically "
            "performed better than the beginning and end of the month. The seasonal "
            "setup is therefore mixed rather than strongly bearish."
        ),
        "source": "Stock Trader's Almanac 2026 August 2026 section",
    },
    (8, 3): {
        "label": "August Expiration Week, 17-21 August",
        "name": "August monthly expiration week",
        "tendency": "Mixed",
        "strength": "Medium",
        "bullets": [
            "Monday, August 17: Monday before August Monthly Expiration has historically been positive.",
            "Dow is up 19 of the last 30 times on the Monday before August Monthly Expiration.",
            "Average gain for this Monday pattern is +0.2%.",
            "Friday, August 21: August Monthly Expiration Day has been weaker recently.",
            "Dow is down 8 of the last 15 times on August Monthly Expiration Day.",
            "Net: mixed. Early expiration-week strength is offset by weaker expiration-day performance.",
        ],
        "seasonal_bias": "Mixed",
        "confidence": "Medium",
        "thesis": (
            "August expiration week contains conflicting seasonal signals. "
            "The Monday before expiration has historically shown mild strength, "
            "with the Dow up 19 of the last 30 occurrences and an average gain "
            "of 0.2%. However, August Monthly Expiration Day has weakened recently, "
            "with the Dow down 8 of the last 15 occurrences. The overall signal "
            "is mixed heading into the end of August."
        ),
        "source": "Stock Trader's Almanac 2026 August 2026 section",
    },
    (8, 4): {
        "label": "Late August Week, 24-28 August",
        "name": "Week after August monthly expiration / late-August weakness",
        "tendency": "Mixed to bearish",
        "strength": "Medium",
        "bullets": [
            "Week after August Monthly Expiration has historically been mixed.",
            "Dow is down 10 of the last 20 times during the week after August Monthly Expiration.",
            "The week after expiration saw a major decline in 2022, when the Dow fell 4.2%.",
            "Thursday, August 27: August's third-to-last trading day has shown strong historical S&P 500 performance,"
            "including a 19-year winning streak from 2003-2021.",
            "Friday, August 28: August's next-to-last trading day has been weaker, with the S&P 500 down 19 of the last 29 years.",
            "Net: mixed. Late-month strength patterns are offset by weaker expiration follow-through and next-to-last-day weakness.",
        ],
        "seasonal_bias": "Mixed",
        "confidence": "Medium",
        "thesis": (
            "Late August contains conflicting seasonal signals. The week after "
            "monthly expiration has been mixed, with the Dow down 10 of the last "
            "20 occurrences. Late-month trading days show both strength and "
            "weakness: the third-to-last trading day had a long positive streak "
            "through 2021, while the next-to-last trading day has historically "
            "been weak with the S&P 500 down 19 of the last 29 years. The overall "
            "signal remains mixed heading into September."
        ),
        "source": "Stock Trader's Almanac 2026 August 2026 section",
    },
    (9, 1): {
        "label": "Early September Week, 31 August-4 September",
        "name": "Labor Day transition / early September weakness",
        "tendency": "Mixed to bearish",
        "strength": "Medium",
        "bullets": [
            "Monday, August 31: Last Trading Day in August has been mixed historically.",
            "S&P 500 was up 14 of the last 25 years on the last trading day of August, but down 6 of the last 10.",
            "Tuesday, September 1: First Trading Day in September has shown mixed performance.",
            "S&P 500 was up 18 of the last 30 years on the first trading day of September, but down 10 of the last 17.",
            "September begins with a weak seasonal backdrop as the month is historically the weakest month for major indexes.",
            "Net: mixed early-week action with a bearish monthly seasonal backdrop.",
        ],
        "seasonal_bias": "Bearish",
        "confidence": "Medium",
        "thesis": (
            "The transition from August into September carries mixed short-term "
            "signals but a historically weak monthly backdrop. The final trading "
            "day of August has recently weakened, while the first trading day of "
            "September has also become less reliable. September remains the "
            "historically weakest month for major indexes, creating a cautious "
            "seasonal setup."
        ),
        "source": "Stock Trader's Almanac 2026 August/September 2026 section",
    },
    (9, 2): {
        "label": "Post-Labor Day Week, 7-11 September",
        "name": "Day after Labor Day weakness",
        "tendency": "Bearish",
        "strength": "Medium",
        "bullets": [
            "Monday, September 7: Labor Day — market closed.",
            "Tuesday, September 8: Day After Labor Day has historically weakened recently.",
            "Dow is up 16 of the last 31 times on the day after Labor Day.",
            "Recent trend is weaker, with Dow down 12 of the last 15 occurrences.",
            "September seasonal weakness often begins after the Labor Day holiday.",
            "Net: bearish bias due to recent post-Labor Day weakness.",
        ],
        "seasonal_bias": "Bearish",
        "confidence": "Medium",
        "thesis": (
            "The post-Labor Day period has historically shown mixed results, "
            "but recent performance has been notably weak. The Dow is down "
            "12 of the last 15 occurrences after Labor Day despite a longer "
            "historical record of 16 gains in 31 occurrences. Combined with "
            "September's weak seasonal reputation, the setup favors caution."
        ),
        "source": "Stock Trader's Almanac 2026 September 2026 section",
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
    "covered_sprint_weeks": ["W22", "W23", "W25", "W26", "W27", "W28", "W29",
                             "W30", "W31", "W32", "W33", "W34", "W35", "W36", "W37"],
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
    "Trader's Almanac June/July seasonal summaries. W25-W37 entries are encoded "
    "for the first software increment. Jan-Dec monthly records are structured "
    "for data encoder follow-up where exact page figures are not yet verified."
)
