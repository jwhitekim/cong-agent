"""view_segments 스키마와 등록."""
from openhands.sdk import Action
from pydantic import Field

from cong_agent.tools.utils.base import QueryTool
from cong_agent.tools.utils.format import WINDOW
from cong_agent.tools.view_segments.impl import view_segments


class ViewSegmentsAction(Action):
    start: int = Field(description="시작 세그먼트 번호(포함)")
    end: int = Field(description="끝 세그먼트 번호(포함)")


class ViewSegmentsTool(QueryTool):
    action_cls = ViewSegmentsAction
    tool_description = f"start–end 범위 세그먼트의 관측값 표. 한 번에 최대 {WINDOW}행."
    fn = staticmethod(view_segments)
