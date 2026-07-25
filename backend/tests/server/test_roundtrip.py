"""Round-trip tests: parsed output -> render_md -> parse_md -> compare.

Two guarantees, both over every real /data week:

* ``test_direct_round_trip`` — for technical and macro, parsing the archive and
  re-parsing its rendered Markdown yields an identical output.
* ``test_render_parse_fixed_point`` — for every agent, one render/parse cycle
  reaches a fixed point (a second cycle changes nothing). Almanac needs this
  weaker form because its rendered Markdown normalizes the date to the week's
  Monday and sources ``weekly_pattern`` from static tables, so the very first
  cycle may adjust those two fields.
"""

import json
from dataclasses import asdict

import pytest

from agents.almanac.almanac_agent import AlmanacAgent
from agents.macro.macro_agent import MacroAgent
from agents.technical.technical_agent import TechnicalAgent
from server.db import render
from server.archive import _read_text, _resolve_agent_path, discover_archive_stems

DISCOVERED = discover_archive_stems()
STEMS = sorted(DISCOVERED)

_AGENTS = {
    "technical": TechnicalAgent,
    "macro": MacroAgent,
    "almanac": AlmanacAgent,
}


def _payload(output) -> dict:
    return json.loads(json.dumps(asdict(output), default=str))


def _parse_first(agent: str, stem: str):
    path = _resolve_agent_path(agent, stem)
    assert path is not None, f"missing {agent} archive for {stem}"
    text = _read_text(path)
    assert text, f"empty {agent} archive for {stem}"
    return _AGENTS[agent].parse_md(text, DISCOVERED[stem])


def _reparse(agent: str, output):
    md = render.render_markdown(agent, _payload(output))
    return _AGENTS[agent].parse_md(md, output.prediction_date)


@pytest.mark.parametrize("stem", STEMS)
@pytest.mark.parametrize("agent", ["technical", "macro"])
def test_direct_round_trip(agent, stem):
    o1 = _parse_first(agent, stem)
    assert _reparse(agent, o1) == o1


@pytest.mark.parametrize("stem", STEMS)
@pytest.mark.parametrize("agent", list(_AGENTS))
def test_render_parse_fixed_point(agent, stem):
    o1 = _parse_first(agent, stem)
    o2 = _reparse(agent, o1)
    o3 = _reparse(agent, o2)
    assert o3 == o2
