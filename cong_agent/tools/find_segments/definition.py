"""find_segments 스키마와 등록."""
from openhands.sdk import Action
from pydantic import Field

from cong_agent.environment import LEVELS
from cong_agent.tools.find_segments.impl import find_segments
from cong_agent.tools.utils.base import QueryTool


class FindSegmentsAction(Action):
    level: str | None = Field(default=None, description=f"혼잡 등급: {', '.join(LEVELS)}")
    min_total: int | None = Field(default=None, description="이 인원 이상")
    max_avg_speed: float | None = Field(default=None, description="평균 속도(px/s)가 이 값 이하")
    min_density_slope: float | None = Field(default=None, description="density_slope가 이 값 이상")


class FindSegmentsTool(QueryTool):
    action_cls = FindSegmentsAction
    tool_description = ("조건(level, 최소 인원, 최대 평균 속도, 최소 밀도 추세)에 맞는 세그먼트 번호와 "
                        "일치 개수. 조건은 AND로 결합.")
    fn = staticmethod(find_segments)
