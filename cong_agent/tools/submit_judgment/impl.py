"""submit_judgment 실행 로직: 판정 검증과 저장.

LLM이 넣은 숫자 카운트 필드는 걷어내고, 근거 세그먼트의 인원 수는 세션
관측값에서 코드가 직접 넣는다 (congestion-llm-gating schema.py와 같은 방어).
검증을 통과해도 실행은 끝내지 않는다 — 종료는 SDK 기본 finish 도구가 맡는다.
"""
from typing import Any

from openhands.sdk import Action
from openhands.sdk.tool import ToolExecutor

from cong_agent.environment import Session
from cong_agent.tools.utils.base import CongestionObservation
from cong_agent.tools.utils.errors import ToolError, check_index

VALID_ASSESSMENT = ("normal", "caution", "anomaly")
VALID_ACTION = ("none", "monitor", "alert")
REQUIRED = ("assessment", "action", "evidence_segments", "summary", "reasoning")
_FORBIDDEN_NUMERIC = {"total_people", "total", "count", "num_people", "people_count"}
ACCEPTED_MESSAGE = "판정을 받았습니다. 더 확인할 것이 없으면 finish를 호출해 실행을 끝내세요."


class JudgmentStore:
    """검증을 통과한 판정을 담는다. 유효한 제출이 여러 번이면 마지막 것이 남는다."""

    def __init__(self) -> None:
        self.judgment: dict[str, Any] | None = None


def validate_judgment(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    missing = [k for k in REQUIRED if k not in args]
    if missing:
        raise ToolError(f"필수 필드가 없습니다: {', '.join(missing)}")
    if args["assessment"] not in VALID_ASSESSMENT:
        raise ToolError(f"assessment는 {', '.join(VALID_ASSESSMENT)} 중 하나여야 합니다: {args['assessment']!r}")
    if args["action"] not in VALID_ACTION:
        raise ToolError(f"action은 {', '.join(VALID_ACTION)} 중 하나여야 합니다: {args['action']!r}")
    ev = args["evidence_segments"]
    if not isinstance(ev, list) or not ev:
        raise ToolError("evidence_segments는 세그먼트 번호 1개 이상의 목록이어야 합니다")
    ev = [check_index(session, i, "evidence_segments의 번호") for i in ev]
    for k in ("summary", "reasoning"):
        if not isinstance(args[k], str) or not args[k].strip():
            raise ToolError(f"{k}는 비어 있지 않은 문자열이어야 합니다")

    judgment = {k: v for k, v in args.items() if k not in _FORBIDDEN_NUMERIC}
    judgment["evidence_segments"] = ev
    judgment["evidence_totals"] = {i: session.segments[i].total for i in ev}
    return judgment


class SubmitJudgmentExecutor(ToolExecutor):
    def __init__(self, session: Session, store: JudgmentStore):
        self.session = session
        self.store = store

    def __call__(self, action: Action, conversation: Any = None) -> CongestionObservation:
        args = {k: getattr(action, k) for k in REQUIRED}
        args.update(action.model_extra or {})
        try:
            judgment = validate_judgment(self.session, args)
        except ToolError as e:
            return CongestionObservation.from_text(text=str(e), is_error=True)
        self.store.judgment = judgment
        return CongestionObservation.from_text(text=ACCEPTED_MESSAGE)
