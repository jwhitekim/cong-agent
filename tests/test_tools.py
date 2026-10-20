import re

import pytest

from cong_agent.tools import TOOLS, ToolError, run_tool, tool_specs
from cong_agent.tools.format import index_list, num, window_note


# --- format ---

def test_num_rounds_floats_only():
    assert num(3.14159) == "3.14"
    assert num(7) == "7"


def test_window_note():
    assert window_note(19, 19) == ""
    assert "20–49" in window_note(19, 49)


def test_index_list_truncates():
    out = index_list(list(range(60)))
    assert "49" in out and "50," not in out and "처음 50개" in out


def test_registry_specs():
    names = [s["name"] for s in tool_specs()]
    assert names == ["session_overview", "view_segments", "find_segments", "zone_trend", "submit_judgment"]


# --- session_overview ---

def test_overview_trigger_counts_sum(session):
    out = run_tool(session, "session_overview", {})
    n_trig = sum(1 for s in session.segments if s.trigger)
    m = re.search(r"트리거 있는 세그먼트 (\d+)개: (.*)", out)
    assert int(m.group(1)) == n_trig
    assert sum(int(x) for x in re.findall(r"\b(\d+)\b", m.group(2))) == n_trig
    assert "세그먼트 30개" in out


# --- view_segments ---

def test_view_truncates_to_20_rows(session):
    out = run_tool(session, "view_segments", {"start": 0, "end": 29})
    rows = [l for l in out.splitlines() if re.match(r"^\d+ \|", l)]
    assert [int(r.split(" |")[0]) for r in rows] == list(range(20))
    assert "남은 범위: 20–29" in out


def test_view_out_of_range(session):
    with pytest.raises(ToolError, match="유효 범위: 0–29"):
        run_tool(session, "view_segments", {"start": 0, "end": 45})


def test_view_shows_trigger_reason(session):
    out = run_tool(session, "view_segments", {"start": 20, "end": 20})
    assert "hotspot(+surge)" in out and "A구역 14명" in out


# --- find_segments ---

def test_find_by_trigger(session):
    out = run_tool(session, "find_segments", {"trigger": "stagnation"})
    assert "일치 2개" in out and "12, 13" in out


def test_find_no_match(session):
    out = run_tool(session, "find_segments", {"min_total": 999})
    assert "일치 0개" in out


def test_find_requires_condition(session):
    with pytest.raises(ToolError):
        run_tool(session, "find_segments", {})


# --- zone_trend ---

def test_zone_trend(session):
    out = run_tool(session, "zone_trend", {"zone": "A", "start": 18, "end": 23})
    counts = [s.zone_counts["A"] for s in session.segments[18:24]]
    assert f"최소 {min(counts)}, 최대 {max(counts)}" in out
    peak = [s.index for s in session.segments[18:24] if s.zone_counts["A"] == max(counts)]
    assert ", ".join(map(str, peak)) in out


def test_zone_unknown(session):
    with pytest.raises(ToolError, match="A, B, C"):
        run_tool(session, "zone_trend", {"zone": "D"})


# --- 공통 ---

def test_unknown_tool_lists_names(session):
    with pytest.raises(ToolError, match="session_overview"):
        run_tool(session, "count_people", {})


def test_bad_argument_name(session):
    with pytest.raises(ToolError, match="인자"):
        run_tool(session, "view_segments", {"begin": 0, "end": 3})


JUDGMENT_WORDS = re.compile(r"\b(normal|caution|anomaly|monitor|alert)\b|LEAK_")


def test_query_outputs_never_contain_judgment(session):
    n = len(session.segments)
    outputs = [run_tool(session, "session_overview", {})]
    outputs += [run_tool(session, "view_segments", {"start": i, "end": min(i + 19, n - 1)}) for i in range(0, n, 20)]
    outputs += [run_tool(session, "find_segments", {"trigger": t}) for t in ("surge", "stagnation", "hotspot", "conflict")]
    outputs += [run_tool(session, "find_segments", {"level": l}) for l in ("low", "medium", "high")]
    outputs += [run_tool(session, "zone_trend", {"zone": z}) for z in session.zones]
    for out in outputs:
        assert not JUDGMENT_WORDS.search(out), out
    for name in ("session_overview", "view_segments", "find_segments", "zone_trend"):
        assert not JUDGMENT_WORDS.search(TOOLS[name].description)
