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

def test_overview_level_counts_sum(session):
    out = run_tool(session, "session_overview", {})
    m = re.search(r"level\)별 세그먼트: (.*)", out)
    assert sum(int(x) for x in re.findall(r"\b(\d+)\b", m.group(1))) == len(session.segments)
    assert "세그먼트 30개" in out
    assert f"최소 {min(s.total for s in session.segments)}" in out
    assert "평균 속도(avg_speed) 최소 0.30" in out


# --- view_segments ---

def test_view_truncates_to_20_rows(session):
    out = run_tool(session, "view_segments", {"start": 0, "end": 29})
    rows = [l for l in out.splitlines() if re.match(r"^\d+ \|", l)]
    assert [int(r.split(" |")[0]) for r in rows] == list(range(20))
    assert "남은 범위: 20–29" in out


def test_view_out_of_range(session):
    with pytest.raises(ToolError, match="유효 범위: 0–29"):
        run_tool(session, "view_segments", {"start": 0, "end": 45})


# --- find_segments ---

def test_find_slow_segments(session):
    out = run_tool(session, "find_segments", {"max_avg_speed": 0.5})
    assert "일치 3개" in out and "12, 13, 14" in out


def test_find_combined_conditions(session):
    out = run_tool(session, "find_segments", {"level": "low", "min_density_slope": 0.4})
    expected = [s.index for s in session.segments if s.level == "low" and s.density_slope >= 0.4]
    assert expected == [25]
    assert "일치 1개" in out and "세그먼트: 25" in out


def test_find_no_match(session):
    out = run_tool(session, "find_segments", {"min_total": 999})
    assert "일치 0개" in out


def test_find_requires_condition(session):
    with pytest.raises(ToolError, match="하나 이상"):
        run_tool(session, "find_segments", {})


def test_find_rejects_trigger_argument(session):
    with pytest.raises(ToolError, match="인자"):
        run_tool(session, "find_segments", {"trigger": "hotspot"})


def test_find_rejects_non_numeric_speed(session):
    with pytest.raises(ToolError, match="숫자"):
        run_tool(session, "find_segments", {"max_avg_speed": "slow"})


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
# 원본 fixture의 트리거 이름과 trigger_reason 문장 조각
TRIGGER_WORDS = re.compile(r"\b(surge|stagnation|hotspot|conflict)\b|trigger|배 > 1\.4|임계 8\.0|지속")


def test_query_outputs_never_contain_judgment(session):
    n = len(session.segments)
    outputs = [run_tool(session, "session_overview", {})]
    outputs += [run_tool(session, "view_segments", {"start": i, "end": min(i + 19, n - 1)}) for i in range(0, n, 20)]
    outputs += [run_tool(session, "find_segments", {"max_avg_speed": 1.0, "min_total": 0})]
    outputs += [run_tool(session, "find_segments", {"level": l}) for l in ("low", "medium", "high")]
    outputs += [run_tool(session, "zone_trend", {"zone": z}) for z in session.zones]
    for out in outputs:
        assert not JUDGMENT_WORDS.search(out), out
        assert not TRIGGER_WORDS.search(out), out
    for name in ("session_overview", "view_segments", "find_segments", "zone_trend"):
        assert not JUDGMENT_WORDS.search(TOOLS[name].description)
        assert not TRIGGER_WORDS.search(TOOLS[name].description)
