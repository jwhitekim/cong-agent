"""도구 입력 오류와 공용 입력 검사."""
from typing import Any

from cong_agent.environment import Session


class ToolError(Exception):
    """에이전트에게 오류 관측으로 돌려줄 입력 오류. 루프는 계속된다."""


def check_index(session: Session, i: Any, label: str = "세그먼트 번호") -> int:
    last = len(session.segments) - 1
    if not isinstance(i, int) or isinstance(i, bool):
        raise ToolError(f"{label}는 정수여야 합니다: {i!r}")
    if not 0 <= i <= last:
        raise ToolError(f"{label} {i}는 범위 밖입니다. 유효 범위: 0–{last}")
    return i


def check_range(session: Session, start: int | None, end: int | None) -> tuple[int, int]:
    """start·end 검사. 생략하면 처음·끝."""
    start = 0 if start is None else check_index(session, start, "start")
    end = len(session.segments) - 1 if end is None else check_index(session, end, "end")
    if end < start:
        raise ToolError(f"end({end})는 start({start})보다 작을 수 없습니다")
    return start, end
