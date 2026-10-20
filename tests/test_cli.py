import json

from openhands.sdk.testing import TestLLM

from cong_agent.__main__ import main
from conftest import FIXTURE
from test_runner import FINISH, call

GOOD = {"assessment": "anomaly", "action": "alert", "evidence_segments": [12, 13],
        "summary": "정체 구간", "reasoning": "평균 속도가 0.3px/s로 낮다"}


def test_cli_prints_judgment(tmp_path, capsys):
    llm = TestLLM.from_messages([call("submit_judgment", GOOD), FINISH])
    code = main(["run", "--session", str(FIXTURE), "--question", "정체 구간은?", "--out", str(tmp_path)], llm=llm)
    out = capsys.readouterr().out
    assert code == 0
    assert "상태: submitted" in out and '"assessment": "anomaly"' in out
    (run_json,) = tmp_path.glob("*/run.json")
    assert json.loads(run_json.read_text(encoding="utf-8"))["status"] == "submitted"


def test_cli_bad_session(tmp_path, capsys):
    code = main(["run", "--session", str(tmp_path), "--question", "q", "--out", str(tmp_path)],
                llm=TestLLM.from_messages([]))
    assert code == 2 and "session.json" in capsys.readouterr().err
