"""혼잡도 도구 공개 목록. 새 도구는 폴더를 만들고 TOOL_CLASSES에 넣는다."""
from openhands.sdk import ToolDefinition
from openhands.sdk.tool import register_tool

from cong_agent.environment import Session
from cong_agent.tools.find_segments import FindSegmentsTool
from cong_agent.tools.session_overview import SessionOverviewTool
from cong_agent.tools.submit_judgment import SubmitJudgmentTool
from cong_agent.tools.submit_judgment.impl import JudgmentStore
from cong_agent.tools.view_segments import ViewSegmentsTool
from cong_agent.tools.zone_trend import ZoneTrendTool

TOOL_CLASSES: tuple[type[ToolDefinition], ...] = (
    SessionOverviewTool, ViewSegmentsTool, FindSegmentsTool, ZoneTrendTool, SubmitJudgmentTool)


def register_tools(session: Session, store: JudgmentStore) -> list[str]:
    """세션과 store를 쥔 도구 인스턴스를 SDK registry에 등록하고 이름 목록을 돌려준다.

    SDK registry는 프로세스 전역이라, 같은 이름으로 다시 등록해 이전 세션을 덮어쓴다.
    """
    names = []
    for cls in TOOL_CLASSES:
        (tool,) = cls.create(session=session, store=store)
        register_tool(cls.name, tool)
        names.append(cls.name)
    return names


__all__ = ["TOOL_CLASSES", "JudgmentStore", "register_tools"]
