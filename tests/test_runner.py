import itertools
import json

from openhands.sdk.llm import Message, MessageToolCall, TextContent
from openhands.sdk.testing import TestLLM

from cong_agent.runner import run

GOOD = {"assessment": "caution", "action": "monitor", "evidence_segments": [20, 21],
        "summary": "A구역 쏠림", "reasoning": "A구역 인원이 다른 구역보다 많다"}
_ids = itertools.count()


def call(name, args=None):
    return Message(role="assistant", content=[TextContent(text="")], tool_calls=[
        MessageToolCall(id=f"c{next(_ids)}", name=name, arguments=json.dumps(args or {}, ensure_ascii=False),
                        origin="completion")])


FINISH = call("finish", {"message": "끝"})


def events(run_dir):
    """SDK가 저장한 이벤트 파일을 순서대로 읽는다."""
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(run_dir.glob("conversation/*/events/event-*.json"))]


def run_json(result):
    with open(f"{result.run_dir}/run.json", encoding="utf-8") as fh:
        return json.load(fh)


def test_submitted(session, tmp_path):
    llm = TestLLM.from_messages([call("session_overview"), call("view_segments", {"start": 18, "end": 22}),
                                 call("submit_judgment", GOOD), FINISH])
    r = run(session, "가장 혼잡한 구간은?", llm, tmp_path)
    assert r.status == "submitted"
    assert r.judgment["evidence_segments"] == [20, 21]
    rec = run_json(r)
    assert rec["status"] == "submitted" and rec["question"] == "가장 혼잡한 구간은?"
    assert rec["model"] == llm.model and rec["max_steps"] == 15
    assert rec["judgment"]["assessment"] == "caution"
    actions = [e["tool_name"] for e in events(tmp_path) if e["kind"] == "ActionEvent"]
    assert actions == ["session_overview", "view_segments", "submit_judgment", "finish"]


def test_no_judgment_when_finish_without_submit(session, tmp_path):
    r = run(session, "q", TestLLM.from_messages([call("session_overview"), FINISH]), tmp_path)
    assert r.status == "no_judgment" and r.judgment is None


def test_no_judgment_after_invalid_submit(session, tmp_path):
    llm = TestLLM.from_messages([call("submit_judgment", {**GOOD, "assessment": "danger"}), FINISH])
    assert run(session, "q", llm, tmp_path).status == "no_judgment"


def test_step_limit(session, tmp_path):
    # 서로 다른 호출이라 반복 감지에 걸리지 않게 한다
    llm = TestLLM.from_messages([call("view_segments", {"start": i, "end": i}) for i in range(20)])
    r = run(session, "q", llm, tmp_path, max_steps=5)
    assert r.status == "step_limit"
    assert run_json(r)["status"] == "step_limit"


def test_stuck(session, tmp_path):
    llm = TestLLM.from_messages([call("session_overview") for _ in range(10)])
    r = run(session, "q", llm, tmp_path)
    assert r.status == "stuck"
    assert run_json(r)["status"] == "stuck"


def test_unknown_tool_and_bad_args_keep_running(session, tmp_path):
    llm = TestLLM.from_messages([call("count_people"), call("view_segments", {"start": 0, "end": 99}),
                                 call("submit_judgment", GOOD), FINISH])
    r = run(session, "q", llm, tmp_path)
    assert r.status == "submitted"
    blob = json.dumps(events(tmp_path), ensure_ascii=False)
    assert "count_people" in blob and "not found" in blob and "session_overview" in blob
    assert "유효 범위: 0–29" in blob


def test_llm_error_keeps_earlier_events(session, tmp_path):
    llm = TestLLM.from_messages([call("view_segments", {"start": i, "end": i}) for i in range(3)]
                                + [RuntimeError("API 실패")])
    r = run(session, "q", llm, tmp_path)
    assert r.status == "error" and "API 실패" in r.error
    starts = [e["action"]["start"] for e in events(tmp_path) if e["kind"] == "ActionEvent"]
    assert starts == [0, 1, 2]
    assert run_json(r)["status"] == "error"


def test_no_image_content_sent(session, tmp_path):
    llm = TestLLM.from_messages([call("view_segments", {"start": 0, "end": 5}), call("submit_judgment", GOOD), FINISH])
    run(session, "q", llm, tmp_path)
    def content_types(x):
        if isinstance(x, dict):
            if "type" in x and ("text" in x or "image_urls" in x):
                yield x["type"]
            for v in x.values():
                yield from content_types(v)
        elif isinstance(x, list):
            for v in x:
                yield from content_types(v)

    types = set(content_types(events(tmp_path)))
    assert "text" in types and "image" not in types
