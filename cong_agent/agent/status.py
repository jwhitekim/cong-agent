"""실행 결과와 최종 상태 판정.

    FINISHED + 판정 있음        → submitted
    FINISHED + 판정 없음        → no_judgment
    STUCK                       → stuck
    ERROR(MaxIterationsReached) → step_limit
    그 외 ERROR / 예외          → error
"""
from dataclasses import dataclass, field
from typing import Any

from openhands.sdk.conversation.state import ConversationExecutionStatus
from openhands.sdk.event.conversation_error import ConversationErrorEvent

from cong_agent.tools import JudgmentStore


@dataclass
class RunResult:
    status: str
    judgment: dict[str, Any] | None
    error: str | None
    usage: dict[str, int] = field(default_factory=dict)
    run_dir: str = ""


def final_status(conversation: Any, store: JudgmentStore) -> tuple[str, str | None]:
    """(최종 상태, 오류 메시지)."""
    state = conversation.state.execution_status
    if state == ConversationExecutionStatus.FINISHED:
        return ("submitted" if store.judgment is not None else "no_judgment"), None
    if state == ConversationExecutionStatus.STUCK:
        return "stuck", None
    errors = [e for e in conversation.state.events if isinstance(e, ConversationErrorEvent)]
    # 단계 초과는 사람이 읽는 메시지가 아니라 오류 코드로 판단한다
    if errors and errors[-1].code == "MaxIterationsReached":
        return "step_limit", None
    if errors:
        return "error", f"{errors[-1].code}: {errors[-1].detail}"
    return "error", f"예상하지 못한 종료 상태: {state}"


def token_usage(conversation: Any) -> dict[str, int]:
    total = {"input_tokens": 0, "output_tokens": 0}
    for metrics in conversation.conversation_stats.usage_to_metrics.values():
        u = metrics.accumulated_token_usage
        if u is not None:
            total["input_tokens"] += u.prompt_tokens
            total["output_tokens"] += u.completion_tokens
    return total
