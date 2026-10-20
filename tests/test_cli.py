from cong_agent.__main__ import main
from cong_agent.llm import LLMResponse, ScriptedClient, ToolCall
from conftest import FIXTURE

GOOD = {"assessment": "anomaly", "action": "alert", "evidence_segments": [12, 13],
        "summary": "정체 구간", "reasoning": "평균 속도가 0.3px/s로 낮다"}


def test_cli_prints_judgment(tmp_path, capsys):
    llm = ScriptedClient([LLMResponse("", [ToolCall("t1", "submit_judgment", GOOD)])])
    code = main(["run", "--session", str(FIXTURE), "--question", "정체 구간은?", "--out", str(tmp_path)], llm=llm)
    out = capsys.readouterr().out
    assert code == 0
    assert "상태: submitted (1단계" in out and '"assessment": "anomaly"' in out
    assert list(tmp_path.glob("*/trajectory.jsonl"))


def test_cli_bad_session(tmp_path, capsys):
    code = main(["run", "--session", str(tmp_path), "--question", "q", "--out", str(tmp_path)],
                llm=ScriptedClient([]))
    assert code == 2 and "session.json" in capsys.readouterr().err
