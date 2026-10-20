"""도구 registry. 새 도구는 여기 목록에 명시적으로 추가한다."""
import inspect
from typing import Any

from cong_agent.session import Session
from cong_agent.tools.base import Tool, ToolError
from cong_agent.tools.query import QUERY_TOOLS
from cong_agent.tools.submit import SUBMIT_TOOL, validate_judgment

TOOLS: dict[str, Tool] = {t.name: t for t in [*QUERY_TOOLS, SUBMIT_TOOL]}


def tool_specs() -> list[dict[str, Any]]:
    return [t.spec() for t in TOOLS.values()]


def run_tool(session: Session, name: str, args: dict[str, Any]) -> str:
    """도구를 실행해 관측 문자열을 돌려준다. 입력 오류는 ToolError로 올린다."""
    tool = TOOLS.get(name)
    if tool is None:
        raise ToolError(f"없는 도구입니다: {name!r}. 사용 가능한 도구: {', '.join(TOOLS)}")
    try:
        inspect.signature(tool.run).bind(session, **args)
    except TypeError as e:
        raise ToolError(f"{name} 인자가 잘못됐습니다: {e}") from e
    return tool.run(session, **args)


__all__ = ["TOOLS", "Tool", "ToolError", "run_tool", "tool_specs", "validate_judgment"]
