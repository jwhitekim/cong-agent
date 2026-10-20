import pytest

from cong_agent.tools.utils.errors import ToolError
from cong_agent.tools.zone_trend import ZoneTrendAction, ZoneTrendTool
from cong_agent.tools.zone_trend.impl import zone_trend


def test_stats_and_peak(session):
    out = zone_trend(session, "A", 18, 23)
    counts = [s.zone_counts["A"] for s in session.segments[18:24]]
    assert f"최소 {min(counts)}, 최대 {max(counts)}" in out
    peak = [s.index for s in session.segments[18:24] if s.zone_counts["A"] == max(counts)]
    assert ", ".join(map(str, peak)) in out


def test_whole_range_by_default(session):
    assert "세그먼트 0–29 (30개)" in zone_trend(session, "B")


def test_unknown_zone(session):
    with pytest.raises(ToolError, match="A, B, C"):
        zone_trend(session, "D")


def test_executor(session):
    (tool,) = ZoneTrendTool.create(session=session)
    assert tool.name == "zone_trend"
    obs = tool.executor(ZoneTrendAction(zone="D"))
    assert obs.is_error and "A, B, C" in obs.content[0].text
