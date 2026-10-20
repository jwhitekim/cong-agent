import anthropic
import httpx2
import pytest

from cong_agent.llm import LLMResponse, ToolCall, is_retryable, with_retries


def _status_error(cls, code):
    req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("err", response=httpx2.Response(code, request=req), body=None)


def _flaky(errors):
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if errors:
            raise errors.pop(0)
        return "ok"

    return fn, calls


def test_retries_rate_limit_then_succeeds():
    fn, calls = _flaky([_status_error(anthropic.RateLimitError, 429)])
    delays = []
    result, retries = with_retries(fn, is_retryable, sleep=delays.append)
    assert (result, retries, calls["n"]) == ("ok", 1, 2)
    assert delays == [1.0]


def test_gives_up_after_three_retries():
    fn, calls = _flaky([_status_error(anthropic.InternalServerError, 500) for _ in range(5)])
    with pytest.raises(anthropic.InternalServerError):
        with_retries(fn, is_retryable, sleep=lambda _: None)
    assert calls["n"] == 4  # 첫 시도 + 재시도 3회


def test_bad_request_fails_immediately():
    fn, calls = _flaky([_status_error(anthropic.BadRequestError, 400)])
    with pytest.raises(anthropic.BadRequestError):
        with_retries(fn, is_retryable, sleep=lambda _: None)
    assert calls["n"] == 1


def test_assistant_content_prefers_raw_blocks():
    raw = [{"type": "thinking", "thinking": "", "signature": "s"}, {"type": "text", "text": "hi"}]
    assert LLMResponse("hi", [], raw_content=raw).assistant_content() is raw
    built = LLMResponse("", [ToolCall("t1", "session_overview", {})]).assistant_content()
    assert built == [{"type": "tool_use", "id": "t1", "name": "session_overview", "input": {}}]
