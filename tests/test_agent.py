import json

import pytest

from cong_agent.agent import run_agent
from cong_agent.llm import LLMResponse, ScriptedClient, ToolCall
from cong_agent.prompt import SYSTEM_PROMPT
from cong_agent.tools import TOOLS, ToolError, validate_judgment
from cong_agent.trajectory import Trajectory

GOOD = {"assessment": "caution", "action": "monitor", "evidence_segments": [20, 21],
        "summary": "A구역 국소 밀집", "reasoning": "A구역 인원이 다른 구역보다 많다"}


def call(name, args=None, i=[0]):
    i[0] += 1
    return LLMResponse(text="", tool_calls=[ToolCall(f"t{i[0]}", name, args or {})],
                       usage={"input_tokens": 10, "output_tokens": 2})


@pytest.fixture
def traj(tmp_path):
    return Trajectory(tmp_path / "trajectory.jsonl")


# --- 판정 검증 (spec 시나리오) ---

def test_invalid_assessment(session):
    with pytest.raises(ToolError, match="normal, caution, anomaly"):
        validate_judgment(session, {**GOOD, "assessment": "danger"})


def test_evidence_out_of_range(session):
    with pytest.raises(ToolError, match="유효 범위: 0–29"):
        validate_judgment(session, {**GOOD, "evidence_segments": [512]})


def test_missing_field(session):
    bad = dict(GOOD)
    del bad["reasoning"]
    with pytest.raises(ToolError, match="reasoning"):
        validate_judgment(session, bad)


def test_forbidden_numeric_removed_and_totals_injected(session):
    j = validate_judgment(session, {**GOOD, "total_people": 99})
    assert "total_people" not in j
    assert j["evidence_totals"] == {20: session.segments[20].total, 21: session.segments[21].total}
    assert 99 not in j["evidence_totals"].values()


def test_prompt_names_all_tools():
    for name in TOOLS:
        assert name in SYSTEM_PROMPT


# --- 루프 ---

def test_submitted_after_two_tools(session, traj):
    llm = ScriptedClient([call("session_overview"), call("view_segments", {"start": 18, "end": 22}),
                          call("submit_judgment", GOOD)])
    r = run_agent(session, "가장 혼잡한 구간은?", llm, traj)
    assert (r.status, r.steps) == ("submitted", 3)
    assert r.judgment["evidence_segments"] == [20, 21]
    assert r.usage == {"input_tokens": 30, "output_tokens": 6}
    events = traj.read()
    assert [e["type"] for e in events] == ["run_start", "step", "step", "step", "run_end"]
    assert events[0]["model"] == "scripted" and events[0]["max_steps"] == 15
    # 두 번째 LLM 호출은 첫 도구 관측을 tool_result로 받았다
    last = llm.calls[1][-1]
    assert last["role"] == "user" and last["content"][0]["type"] == "tool_result"


def test_step_limit(session, traj):
    llm = ScriptedClient([call("session_overview") for _ in range(20)])
    r = run_agent(session, "q", llm, traj, max_steps=15)
    assert r.status == "step_limit" and r.judgment is None
    assert len(llm.calls) == 15


def test_unknown_tool_and_bad_submit_keep_running(session, traj):
    llm = ScriptedClient([call("count_people"), call("submit_judgment", {**GOOD, "assessment": "danger"}),
                          call("submit_judgment", GOOD)])
    r = run_agent(session, "q", llm, traj)
    assert (r.status, r.steps) == ("submitted", 3)
    steps = [e for e in traj.read() if e["type"] == "step"]
    assert steps[0]["observations"][0]["is_error"] and "session_overview" in steps[0]["observations"][0]["output"]
    assert steps[1]["observations"][0]["is_error"] and "caution" in steps[1]["observations"][0]["output"]


def test_text_only_reply_gets_nudge(session, traj):
    llm = ScriptedClient([LLMResponse("생각 중", []), call("submit_judgment", GOOD)])
    r = run_agent(session, "q", llm, traj)
    assert r.status == "submitted"
    assert "submit_judgment" in llm.calls[1][-1]["content"]


def test_error_keeps_earlier_steps(session, traj):
    llm = ScriptedClient([call("session_overview"), call("session_overview"), call("session_overview"),
                          RuntimeError("API 실패")])
    r = run_agent(session, "q", llm, traj)
    assert (r.status, r.steps) == ("error", 3)
    events = traj.read()
    assert [e["step"] for e in events if e["type"] == "step"] == [1, 2, 3]
    assert events[-1]["status"] == "error" and "API 실패" in events[-1]["error"]


def test_retries_recorded(session, traj):
    first = call("session_overview")
    first.retries = 1
    run_agent(session, "q", ScriptedClient([first, call("submit_judgment", GOOD)]), traj)
    assert traj.read()[1]["retries"] == 1


def test_trajectory_survives_write_after_failure(tmp_path):
    t = Trajectory(tmp_path / "t.jsonl")
    t.write({"type": "step", "step": 1})
    with pytest.raises(TypeError):
        t.write({(1, 2): "튜플 키는 JSON으로 못 쓴다"})
    assert t.read() == [{"type": "step", "step": 1}]


def test_no_image_blocks_sent(session, traj):
    llm = ScriptedClient([call("view_segments", {"start": 0, "end": 5}), call("submit_judgment", GOOD)])
    run_agent(session, "q", llm, traj)
    blob = json.dumps(llm.calls, ensure_ascii=False, default=str)
    assert '"image"' not in blob
