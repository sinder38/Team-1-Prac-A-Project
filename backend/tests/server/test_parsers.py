"""Round-trip tests: /data markdown -> parser payload -> rehydrated dataclass.

Every archived week must parse into a payload that ``rehydrate.*_from_payload``
accepts without raising (biases/confidence are normalized to valid enum values).
"""

from datetime import date

import pytest

from server.archive import _read_text, _resolve_agent_path
from server.db import parsers, rehydrate

WEEKS = ["W22", "W23", "W24", "W25", "W28", "W29"]
PRED = date(2026, 6, 18)

_AGENTS = {
    "technical": (parsers.parse_technical, rehydrate.technical_from_payload),
    "macro": (parsers.parse_macro, rehydrate.macro_from_payload),
    "almanac": (parsers.parse_almanac, rehydrate.almanac_from_payload),
}


def _text(agent: str, stem: str) -> str:
    path = _resolve_agent_path(agent, stem)
    assert path is not None, f"missing archive file for {agent} {stem}"
    text = _read_text(path)
    assert text, f"empty archive file for {agent} {stem}"
    return text


@pytest.mark.parametrize("stem", WEEKS)
@pytest.mark.parametrize("agent", list(_AGENTS))
def test_parser_rehydrate_round_trip(agent, stem):
    parse_fn, rehydrate_fn = _AGENTS[agent]
    payload = parse_fn(_text(agent, stem), PRED)
    # Must not raise: normalized enums are valid.
    rehydrate_fn(payload)


@pytest.mark.parametrize("stem", WEEKS)
def test_parse_evidence_round_trip(stem):
    text = _text("evidence", stem)
    payload = parsers.parse_evidence(text, PRED, stem)
    assert payload["week"] == stem
    assert payload["content"]
    rehydrate.evidence_from_payload(payload)


def test_w25_technical_concrete_values():
    payload = parsers.parse_technical(_text("technical", "W25"), PRED)
    assert payload["instruments"]["SPX"]["last_close"] == 7501.0


def test_w25_macro_bias():
    payload = parsers.parse_macro(_text("macro", "W25"), PRED)
    assert payload["macro_bias"] == "Binary-risk"


def test_w22_almanac_zero_sectors_is_acceptable():
    # W22's almanac archive has no parseable SECTOR SIGNALS block; that's fine.
    payload = parsers.parse_almanac(_text("almanac", "W22"), PRED)
    assert payload["sector_signals"] == []
    rehydrate.almanac_from_payload(payload)
