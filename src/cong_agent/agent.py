"""에이전트 루프: LLM이 도구를 고르면 실행하고 관측을 돌려주기를 반복한다.

OpenHands software-agent-sdk의 Agent / Tool / Conversation 분리를 단순화했다.
- LLMClient가 다음 행동(도구 호출)을 고른다
- 도구가 관측을 만든다 (tools/)
- 루프가 대화 기록과 궤적을 관리한다 (이 파일 + trajectory.py)

한 단계 = LLM 호출 한 번. 최종 상태는 submitted | step_limit | error.
"""
from dataclasses import dataclass, field
from typing import Any

from cong_agent.llm import LLMClient
from cong_agent.prompt import SYSTEM_PROMPT
from cong_agent.session import Session
from cong_agent.tools import ToolError, run_tool, tool_specs, validate_judgment
from cong_agent.trajectory import Trajectory

DEFAULT_MAX_STEPS = 15
SUBMIT = "submit_judgment"
NO_TOOL_NUDGE = "도구를 호출해 사실을 확인하거나, 근거가 모였으면 submit_judgment로 판정을 제출하세요."


@dataclass
class RunResult:
    status: str
    steps: int
    judgment: dict[str, Any] | None = None
    error: str | None = None
    usage: dict[str, int] = field(default_factory=dict)


def run_agent(session: Session, question: str, llm: LLMClient, trajectory: Trajectory,
              max_steps: int = DEFAULT_MAX_STEPS) -> RunResult:
    tools = tool_specs()
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    usage = {"input_tokens": 0, "output_tokens": 0}
    trajectory.write({"type": "run_start", "session": str(session.path), "session_id": session.session_id,
                      "question": question, "model": llm.model, "max_steps": max_steps})

    def finish(status: str, steps: int, judgment=None, error=None) -> RunResult:
        trajectory.write({"type": "run_end", "status": status, "steps": steps,
                          "judgment": judgment, "error": error, "usage": usage})
        return RunResult(status, steps, judgment, error, dict(usage))

    for step in range(1, max_steps + 1):
        try:
            resp = llm.complete(SYSTEM_PROMPT, messages, tools)
        except Exception as e:
            return finish("error", step - 1, error=f"{type(e).__name__}: {e}")
        for k in usage:
            usage[k] += resp.usage.get(k, 0)
        messages.append({"role": "assistant", "content": resp.assistant_content()})

        observations = []
        judgment = None
        for call in resp.tool_calls:
            try:
                output = run_tool(session, call.name, call.args)
                if call.name == SUBMIT:
                    judgment = validate_judgment(session, call.args)
                is_error = False
            except ToolError as e:
                output, is_error = f"오류: {e}", True
            observations.append({"tool_use_id": call.id, "tool": call.name, "args": call.args,
                                  "output": output, "is_error": is_error})

        trajectory.write({"type": "step", "step": step, "text": resp.text, "observations": observations,
                          "usage": resp.usage, "retries": resp.retries})

        if judgment is not None:
            return finish("submitted", step, judgment=judgment)

        if observations:
            # 병렬 호출 결과는 한 user 메시지에 모아 돌려준다
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": o["tool_use_id"], "content": o["output"],
                 "is_error": o["is_error"]} for o in observations]})
        else:
            messages.append({"role": "user", "content": NO_TOOL_NUDGE})

    return finish("step_limit", max_steps)
