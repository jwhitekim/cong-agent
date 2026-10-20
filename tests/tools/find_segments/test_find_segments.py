import pytest
from pydantic import ValidationError

from cong_agent.tools.find_segments import FindSegmentsAction, FindSegmentsTool
from cong_agent.tools.find_segments.impl import find_segments
from cong_agent.tools.utils.errors import ToolError


def test_slow_segments(session):
    out = find_segments(session, max_avg_speed=0.5)
    assert "일치 3개" in out and "12, 13, 14" in out


def test_combined_conditions(session):
    expected = [s.index for s in session.segments if s.level == "low" and s.density_slope >= 0.4]
    assert expected == [25]
    out = find_segments(session, level="low", min_density_slope=0.4)
    assert "일치 1개" in out and "세그먼트: 25" in out


def test_no_match_is_not_error(session):
    assert "일치 0개" in find_segments(session, min_total=999)


def test_requires_a_condition(session):
    with pytest.raises(ToolError, match="하나 이상"):
        find_segments(session)


def test_bad_level(session):
    with pytest.raises(ToolError, match="low, medium, high"):
        find_segments(session, level="very_high")


def test_trigger_argument_rejected():
    with pytest.raises(ValidationError):
        FindSegmentsAction(trigger="hotspot")


def test_executor_passes_only_given_arguments(session):
    (tool,) = FindSegmentsTool.create(session=session)
    assert tool.name == "find_segments"
    obs = tool.executor(FindSegmentsAction(max_avg_speed=0.5))
    assert "조건 max_avg_speed=0.5:" in obs.content[0].text
