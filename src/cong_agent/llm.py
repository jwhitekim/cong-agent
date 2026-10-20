"""LLM 경계. 에이전트 루프는 LLMClient Protocol만 안다.

메시지 형식은 Anthropic Messages API를 그대로 쓴다(벤더가 하나뿐이라 변환
계층을 두지 않는다). 재시도는 AnthropicClient 안에서만 한다.
"""
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

DEFAULT_MODEL = "claude-opus-5-5"
MAX_RETRIES = 3
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class RefusalError(Exception):
    """모델(과 fallback 모델)이 요청을 거절했다. 재시도하지 않는다."""


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall]
    usage: dict[str, int] = field(default_factory=dict)
    retries: int = 0
    # API가 돌려준 content 블록 원본. thinking 블록은 바꾸지 않고 다시 보내야 하므로
    # 있으면 이것을 그대로 대화 기록에 붙인다.
    raw_content: list[dict[str, Any]] | None = None

    def assistant_content(self) -> list[dict[str, Any]]:
        """대화 기록에 붙일 assistant 메시지 content."""
        if self.raw_content is not None:
            return self.raw_content
        content: list[dict[str, Any]] = []
        if self.text:
            content.append({"type": "text", "text": self.text})
        content += [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.args} for c in self.tool_calls]
        return content


class LLMClient(Protocol):
    model: str

    def complete(self, system: str, messages: list[dict[str, Any]],
                 tools: list[dict[str, Any]]) -> LLMResponse: ...


class ScriptedClient:
    """테스트용. 미리 정한 응답을 순서대로 돌려준다. 예외를 넣으면 그 자리에서 던진다."""

    model = "scripted"

    def __init__(self, responses: list[LLMResponse | Exception]):
        self._responses = list(responses)
        self.calls: list[list[dict[str, Any]]] = []

    def complete(self, system, messages, tools):
        self.calls.append([dict(m) for m in messages])
        if not self._responses:
            raise RuntimeError("ScriptedClient: 준비된 응답이 없습니다")
        r = self._responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def is_retryable(e: Exception) -> bool:
    import anthropic

    if isinstance(e, (anthropic.APIConnectionError, anthropic.RateLimitError)):
        return True
    return isinstance(e, anthropic.APIStatusError) and e.status_code >= 500


def with_retries(fn: Callable[[], Any], retryable: Callable[[Exception], bool],
                 max_retries: int = MAX_RETRIES, base_delay: float = 1.0,
                 sleep: Callable[[float], None] = time.sleep) -> tuple[Any, int]:
    """fn을 호출하고 (결과, 재시도 횟수)를 돌려준다. 일시적 오류만 지수 백오프로 재시도."""
    for attempt in range(max_retries + 1):
        try:
            return fn(), attempt
        except Exception as e:
            if attempt == max_retries or not retryable(e):
                raise
            sleep(base_delay * 2**attempt)
    raise AssertionError("unreachable")


class AnthropicClient:
    def __init__(self, model: str | None = None, max_tokens: int = 16000):
        import anthropic

        self.model = model or os.environ.get("CONG_AGENT_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens
        # SDK 자체 재시도는 끄고 with_retries 한 곳에서만 재시도한다
        self._client = anthropic.Anthropic(max_retries=0)

    def complete(self, system, messages, tools):
        # 안전 분류기 거절 시 서버가 권장 모델로 다시 돌린다 (fallbacks="default")
        resp, retries = with_retries(
            lambda: self._client.beta.messages.create(
                model=self.model, max_tokens=self.max_tokens,
                system=system, messages=messages, tools=tools,
                betas=[FALLBACK_BETA], fallbacks="default"),
            is_retryable,
        )
        if resp.stop_reason == "refusal":
            category = getattr(resp.stop_details, "category", None)
            raise RefusalError(f"모델이 요청을 거절했습니다 (category={category})")
        text = "".join(b.text for b in resp.content if b.type == "text")
        calls = [ToolCall(b.id, b.name, dict(b.input)) for b in resp.content if b.type == "tool_use"]
        usage = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
        return LLMResponse(text=text, tool_calls=calls, usage=usage, retries=retries,
                           raw_content=[b.to_dict() for b in resp.content])
