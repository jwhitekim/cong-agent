"""도구 공통 타입.

도구는 이름·설명·JSON 입력 스키마와 순수 함수 `run(session, **args) -> str`이다.
관측은 사실과 단순 집계만 담는다. 판정(assessment/action)은 만들지 않는다.
"""
from dataclasses import dataclass
from typing import Any, Callable

from cong_agent.session import Session


class ToolError(Exception):
    """에이전트에게 오류 관측으로 돌려줄 입력 오류. 루프는 계속된다."""


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    run: Callable[..., str]

    def spec(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}


def check_index(session: Session, i: Any, label: str = "세그먼트 번호") -> int:
    last = len(session.segments) - 1
    if not isinstance(i, int) or isinstance(i, bool):
        raise ToolError(f"{label}는 정수여야 합니다: {i!r}")
    if not 0 <= i <= last:
        raise ToolError(f"{label} {i}는 범위 밖입니다. 유효 범위: 0–{last}")
    return i
