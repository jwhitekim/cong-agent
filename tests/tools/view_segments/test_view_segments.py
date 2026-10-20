import re

import pytest
from pydantic import ValidationError

from cong_agent.tools.utils.errors import ToolError
from cong_agent.tools.view_segments import ViewSegmentsAction, ViewSegmentsTool
from cong_agent.tools.view_segments.impl import view_segments


def test_truncates_to_20_rows(session):
    out = view_segments(session, 0, 29)
    rows = [l for l in out.splitlines() if re.match(r"^\d+ \|", l)]
    assert [int(r.split(" |")[0]) for r in rows] == list(range(20))
    assert "남은 범위: 20–29" in out


def test_out_of_range(session):
    with pytest.raises(ToolError, match="유효 범위: 0–29"):
        view_segments(session, 0, 45)


def test_end_before_start(session):
    with pytest.raises(ToolError, match="작을 수 없습니다"):
        view_segments(session, 5, 2)


def test_executor_turns_error_into_observation(session):
    (tool,) = ViewSegmentsTool.create(session=session)
    assert tool.name == "view_segments"
    ok = tool.executor(ViewSegmentsAction(start=0, end=2))
    assert not ok.is_error and ok.content[0].text.startswith("idx |")
    bad = tool.executor(ViewSegmentsAction(start=0, end=99))
    assert bad.is_error and "유효 범위: 0–29" in bad.content[0].text


def test_unknown_argument_rejected():
    with pytest.raises(ValidationError):
        ViewSegmentsAction(begin=0, end=3)
