import re

from cong_agent.tools.session_overview import SessionOverviewAction, SessionOverviewTool
from cong_agent.tools.session_overview.impl import session_overview


def test_level_counts_sum_to_segment_count(session):
    out = session_overview(session)
    m = re.search(r"level\)별 세그먼트: (.*)", out)
    assert sum(int(x) for x in re.findall(r"\b(\d+)\b", m.group(1))) == len(session.segments)
    assert "세그먼트 30개" in out
    assert f"최소 {min(s.total for s in session.segments)}" in out
    assert "평균 속도(avg_speed) 최소 0.30" in out


def test_tool_name_and_observation(session):
    (tool,) = SessionOverviewTool.create(session=session)
    assert tool.name == "session_overview"
    obs = tool.executor(SessionOverviewAction())
    assert not obs.is_error and "세그먼트 30개" in obs.content[0].text
