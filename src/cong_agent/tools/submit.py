"""판정 제출 도구와 검증.

LLM이 넣은 숫자 카운트 필드는 걷어내고, 근거 세그먼트의 인원 수는 세션
관측값에서 코드가 직접 넣는다 (congestion-llm-gating schema.py와 같은 방어).
"""
from typing import Any

from cong_agent.session import Session
from cong_agent.tools.base import Tool, ToolError, check_index

VALID_ASSESSMENT = ("normal", "caution", "anomaly")
VALID_ACTION = ("none", "monitor", "alert")
REQUIRED = ("assessment", "action", "evidence_segments", "summary", "reasoning")
_FORBIDDEN_NUMERIC = {"total_people", "total", "count", "num_people", "people_count"}


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


def _submit(session: Session, **args: Any) -> str:
    validate_judgment(session, args)
    return "판정을 받았습니다. 실행을 마칩니다."


SUBMIT_TOOL = Tool(
    "submit_judgment",
    "최종 판정 제출. 호출하면 실행이 끝난다. action은 실행되지 않는 대응 권고 수준이다.",
    {"type": "object", "properties": {
        "assessment": {"type": "string", "enum": list(VALID_ASSESSMENT)},
        "action": {"type": "string", "enum": list(VALID_ACTION)},
        "evidence_segments": {"type": "array", "items": {"type": "integer"}, "minItems": 1,
                              "description": "판정 근거가 된 세그먼트 번호"},
        "summary": {"type": "string", "description": "질문에 대한 한두 문장 답"},
        "reasoning": {"type": "string", "description": "도구로 확인한 관측값에 근거한 설명"}},
     "required": list(REQUIRED)},
    _submit,
)
