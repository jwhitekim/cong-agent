import pytest
from openhands.sdk import Conversation
from openhands.sdk.testing import TestLLM
from pydantic import ValidationError

from cong_agent.prompt import SYSTEM_PROMPT
from cong_agent.runner import build_agent
from cong_agent.tools.openhands import (FindSegmentsAction, FindSegmentsTool, JudgmentStore,
                                        SubmitJudgmentAction, SubmitJudgmentTool, ViewSegmentsAction,
                                        ViewSegmentsTool)

GOOD = dict(assessment="caution", action="monitor", evidence_segments=[20, 21],
            summary="A구역 쏠림", reasoning="A구역 인원이 다른 구역보다 많다")


def text(obs):
    return obs.content[0].text


# --- 3.1 Executor ---

def test_query_executor_ok(session):
    (tool,) = ViewSegmentsTool.create(session=session)
    obs = tool.executor(ViewSegmentsAction(start=0, end=2))
    assert not obs.is_error and text(obs).startswith("idx |")


def test_query_executor_error_observation(session):
    (tool,) = ViewSegmentsTool.create(session=session)
    obs = tool.executor(ViewSegmentsAction(start=0, end=99))
    assert obs.is_error and "유효 범위: 0–29" in text(obs)


def test_unknown_argument_rejected_by_schema():
    with pytest.raises(ValidationError):
        FindSegmentsAction(trigger="hotspot")


def test_none_arguments_not_passed(session):
    (tool,) = FindSegmentsTool.create(session=session)
    obs = tool.executor(FindSegmentsAction(max_avg_speed=0.5))
    assert "조건 max_avg_speed=0.5:" in text(obs)


# --- 3.2 판정 저장 ---

def _submit(session, store, **kw):
    (tool,) = SubmitJudgmentTool.create(session=session, store=store)
    return tool.executor(SubmitJudgmentAction(**kw))


def test_valid_submit_is_stored_and_counts_stripped(session):
    store = JudgmentStore()
    obs = _submit(session, store, **GOOD, total_people=99)
    assert not obs.is_error and "finish" in text(obs)
    assert "total_people" not in store.judgment
    assert store.judgment["evidence_totals"] == {20: session.segments[20].total, 21: session.segments[21].total}


def test_invalid_submit_not_stored(session):
    store = JudgmentStore()
    obs = _submit(session, store, **{**GOOD, "assessment": "danger"})
    assert obs.is_error and "normal, caution, anomaly" in text(obs)
    assert store.judgment is None
    obs = _submit(session, store, **{**GOOD, "evidence_segments": [512]})
    assert obs.is_error and "유효 범위: 0–29" in text(obs)
    assert store.judgment is None


def test_last_valid_submit_wins(session):
    store = JudgmentStore()
    _submit(session, store, **GOOD)
    _submit(session, store, **{**GOOD, "assessment": "anomaly"})
    _submit(session, store, **{**GOOD, "assessment": "danger"})
    assert store.judgment["assessment"] == "anomaly"


# --- 3.3 도구 구성 ---

def test_agent_tool_names(session, tmp_path):
    from test_runner import FINISH

    agent = build_agent(session, TestLLM.from_messages([FINISH]), JudgmentStore())
    conv = Conversation(agent=agent, workspace=str(tmp_path), visualizer=None)
    conv.send_message("q")
    conv.run()  # 도구는 첫 실행 때 초기화된다
    assert set(conv.agent.tools_map) == {"session_overview", "view_segments", "find_segments",
                                         "zone_trend", "submit_judgment", "finish", "think"}


# --- 4.1 프롬프트 ---

def test_prompt_names_tools_without_triggers():
    for name in ("session_overview", "view_segments", "find_segments", "zone_trend",
                 "submit_judgment", "finish", "think"):
        assert name in SYSTEM_PROMPT
    for word in ("trigger", "트리거", "surge", "stagnation", "hotspot", "conflict"):
        assert word not in SYSTEM_PROMPT
