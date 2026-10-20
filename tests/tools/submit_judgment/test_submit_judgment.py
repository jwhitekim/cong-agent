import pytest

from cong_agent.tools.submit_judgment import SubmitJudgmentAction, SubmitJudgmentTool
from cong_agent.tools.submit_judgment.impl import JudgmentStore, validate_judgment
from cong_agent.tools.utils.errors import ToolError
from conftest import GOOD


def _submit(session, store, **kw):
    (tool,) = SubmitJudgmentTool.create(session=session, store=store)
    return tool.executor(SubmitJudgmentAction(**kw))


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


def test_counts_stripped_and_totals_injected(session):
    store = JudgmentStore()
    obs = _submit(session, store, **GOOD, total_people=99)
    assert not obs.is_error and "finish" in obs.content[0].text
    assert "total_people" not in store.judgment
    assert store.judgment["evidence_totals"] == {20: session.segments[20].total, 21: session.segments[21].total}


def test_invalid_submit_not_stored(session):
    store = JudgmentStore()
    obs = _submit(session, store, **{**GOOD, "assessment": "danger"})
    assert obs.is_error and store.judgment is None


def test_last_valid_submit_wins(session):
    store = JudgmentStore()
    _submit(session, store, **GOOD)
    _submit(session, store, **{**GOOD, "assessment": "anomaly"})
    _submit(session, store, **{**GOOD, "assessment": "danger"})
    assert store.judgment["assessment"] == "anomaly"


def test_tool_name(session):
    (tool,) = SubmitJudgmentTool.create(session=session, store=JudgmentStore())
    assert tool.name == "submit_judgment"
