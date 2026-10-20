"""session_overview 스키마와 등록."""
from openhands.sdk import Action

from cong_agent.tools.session_overview.impl import session_overview
from cong_agent.tools.utils.base import QueryTool


class SessionOverviewAction(Action):
    pass


class SessionOverviewTool(QueryTool):
    action_cls = SessionOverviewAction
    tool_description = "세션 전체 요약: 세그먼트 수·길이·시간 범위, 구역 목록, level별 개수, 인원·평균 속도 범위."
    fn = staticmethod(session_overview)
