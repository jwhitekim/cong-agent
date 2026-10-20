import itertools
import json
from pathlib import Path

import pytest
from openhands.sdk.llm import Message, MessageToolCall, TextContent

from cong_agent.environment import load_session
from cong_agent.run.run_single import DEFAULT_CONFIG, load_config

TESTS = Path(__file__).parent
REPO_ROOT = TESTS.parent
FIXTURE = TESTS / "fixtures" / "session_small"
REAL_SESSION = REPO_ROOT.parent / "congestion-llm-gating" / "outputs" / "20260726_210025"

QUERY_TOOLS = ("session_overview", "view_segments", "find_segments", "zone_trend")
AGENT_TOOLS = (*QUERY_TOOLS, "submit_judgment", "finish", "think")

GOOD = {"assessment": "caution", "action": "monitor", "evidence_segments": [20, 21],
        "summary": "A구역 쏠림", "reasoning": "A구역 인원이 다른 구역보다 많다"}

_ids = itertools.count()


def call(name: str, args: dict | None = None) -> Message:
    """TestLLM에 넣을 도구 호출 응답 하나."""
    return Message(role="assistant", content=[TextContent(text="")], tool_calls=[
        MessageToolCall(id=f"c{next(_ids)}", name=name, arguments=json.dumps(args or {}, ensure_ascii=False),
                        origin="completion")])


FINISH = call("finish", {"message": "끝"})


def events(run_dir: Path) -> list[dict]:
    """SDK가 저장한 이벤트 파일을 순서대로 읽는다."""
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(Path(run_dir).glob("conversation/*/events/event-*.json"))]


def run_json(run_dir: Path) -> dict:
    return json.loads((Path(run_dir) / "run.json").read_text(encoding="utf-8"))


@pytest.fixture
def session():
    return load_session(FIXTURE)


@pytest.fixture
def config():
    return load_config(DEFAULT_CONFIG)
