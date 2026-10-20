"""zone_trend 스키마와 등록."""
from openhands.sdk import Action
from pydantic import Field

from cong_agent.tools.utils.base import QueryTool
from cong_agent.tools.zone_trend.impl import zone_trend


class ZoneTrendAction(Action):
    zone: str = Field(description="구역 이름")
    start: int | None = Field(default=None, description="시작 세그먼트 번호(포함). 생략하면 0")
    end: int | None = Field(default=None, description="끝 세그먼트 번호(포함). 생략하면 마지막")


class ZoneTrendTool(QueryTool):
    action_cls = ZoneTrendAction
    tool_description = "한 구역의 인원 최소·최대·평균과 최대 인원 세그먼트. 범위를 생략하면 전체."
    fn = staticmethod(zone_trend)
