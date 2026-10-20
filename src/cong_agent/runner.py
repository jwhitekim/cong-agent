"""OpenHands SDK로 에이전트를 구성하고 실행한다.

루프·재시도·이벤트 저장·반복 감지는 SDK가 맡는다. 여기서는
- 도메인 도구 등록과 Agent·Conversation 구성
- 실행 뒤 대화 상태와 저장된 판정으로 최종 상태 결정
- run.json 기록
만 한다.

최종 상태
    FINISHED + 판정 있음        → submitted
    FINISHED + 판정 없음        → no_judgment
    STUCK                       → stuck
    ERROR(MaxIterationsReached) → step_limit
    그 외 ERROR / 예외          → error
"""
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.sdk.conversation.state import ConversationExecutionStatus
from openhands.sdk.event.conversation_error import ConversationErrorEvent
from pydantic import SecretStr

from cong_agent.prompt import SYSTEM_PROMPT
from cong_agent.session import Session
from cong_agent.tools.openhands import JudgmentStore, register_tools

DEFAULT_MODEL = "anthropic/claude-opus-5-5"
DEFAULT_MAX_STEPS = 15
MAX_RETRIES = 3


@dataclass
class RunResult:
    status: str
    judgment: dict[str, Any] | None
    error: str | None
    usage: dict[str, int] = field(default_factory=dict)
    run_dir: str = ""


def build_llm(model: str | None = None) -> LLM:
    key = os.environ.get("ANTHROPIC_API_KEY")
    return LLM(model=model or os.environ.get("CONG_AGENT_MODEL", DEFAULT_MODEL),
               api_key=SecretStr(key) if key else None,
               num_retries=MAX_RETRIES, usage_id="cong-agent")


def build_agent(session: Session, llm: LLM, store: JudgmentStore) -> Agent:
    names = register_tools(session, store)
    # 기본 도구는 FinishTool·ThinkTool 두 개뿐이다. 터미널·파일·브라우저 도구는 넣지 않는다.
    return Agent(llm=llm, tools=[Tool(name=n) for n in names],
                 include_default_tools=["FinishTool", "ThinkTool"], system_prompt=SYSTEM_PROMPT)


def _usage(conversation: Any) -> dict[str, int]:
    total = {"input_tokens": 0, "output_tokens": 0}
    for metrics in conversation.conversation_stats.usage_to_metrics.values():
        u = metrics.accumulated_token_usage
        if u is not None:
            total["input_tokens"] += u.prompt_tokens
            total["output_tokens"] += u.completion_tokens
    return total


def _status(conversation: Any, store: JudgmentStore) -> tuple[str, str | None]:
    state = conversation.state.execution_status
    if state == ConversationExecutionStatus.FINISHED:
        return ("submitted" if store.judgment is not None else "no_judgment"), None
    if state == ConversationExecutionStatus.STUCK:
        return "stuck", None
    errors = [e for e in conversation.state.events if isinstance(e, ConversationErrorEvent)]
    if errors and errors[-1].code == "MaxIterationsReached":
        return "step_limit", None
    if errors:
        return "error", f"{errors[-1].code}: {errors[-1].detail}"
    return "error", f"예상하지 못한 종료 상태: {state}"


def run(session: Session, question: str, llm: LLM, run_dir: str | Path,
        max_steps: int = DEFAULT_MAX_STEPS) -> RunResult:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    store = JudgmentStore()
    conversation = Conversation(
        agent=build_agent(session, llm, store), workspace=str(run_dir),
        persistence_dir=str(run_dir / "conversation"), max_iteration_per_run=max_steps,
        visualizer=None, delete_on_close=False)

    error = None
    try:
        conversation.send_message(question)
        conversation.run()
        status, error = _status(conversation, store)
    except Exception as e:
        status, error = "error", f"{type(e).__name__}: {e}"

    result = RunResult(status=status, judgment=store.judgment, error=error,
                       usage=_usage(conversation), run_dir=str(run_dir))
    summary = {"question": question, "session": str(session.path), "session_id": session.session_id,
               "model": llm.model, "max_steps": max_steps, **asdict(result)}
    (run_dir / "run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str),
                                     encoding="utf-8")
    return result
