import argparse
import json
import os

import pytest
from openhands.sdk.testing import TestLLM

from cong_agent.__main__ import main
from cong_agent.run import run_single
from cong_agent.run.run_single import ConfigError, add_arguments, load_config, run
from conftest import FINISH, FIXTURE, GOOD, call, events, run_json


# --- 설정 ---

def test_default_config(config):
    assert config.model == "anthropic/claude-opus-5-5" and config.max_steps == 15


def test_config_overrides(monkeypatch, config):
    monkeypatch.setenv("CONG_AGENT_MODEL", "anthropic/env-model")
    assert load_config(config.path).model == "anthropic/env-model"
    assert load_config(config.path, model="x/arg", max_steps=3).model == "x/arg"
    assert load_config(config.path, max_steps=3).max_steps == 3
    assert load_config(config.path, max_steps=None).max_steps == config.max_steps
    assert load_config(config.path, max_steps=0).max_steps == 0


def test_bad_config(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("agent: {model: m}\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="max_steps"):
        load_config(p)


# --- 최종 상태 5가지 ---

def test_submitted(session, config, tmp_path):
    llm = TestLLM.from_messages([call("session_overview"), call("view_segments", {"start": 18, "end": 22}),
                                 call("submit_judgment", GOOD), FINISH])
    r = run(session, "가장 혼잡한 구간은?", llm, config, tmp_path)
    assert r.status == "submitted" and r.judgment["evidence_segments"] == [20, 21]
    rec = run_json(tmp_path)
    assert rec["status"] == "submitted" and rec["question"] == "가장 혼잡한 구간은?"
    assert rec["model"] == llm.model and rec["max_steps"] == 15 and rec["config"] == config.path
    actions = [e["tool_name"] for e in events(tmp_path) if e["kind"] == "ActionEvent"]
    assert actions == ["session_overview", "view_segments", "submit_judgment", "finish"]


def test_no_judgment_when_finish_without_submit(session, config, tmp_path):
    r = run(session, "q", TestLLM.from_messages([call("session_overview"), FINISH]), config, tmp_path)
    assert r.status == "no_judgment" and r.judgment is None


def test_no_judgment_after_invalid_submit(session, config, tmp_path):
    llm = TestLLM.from_messages([call("submit_judgment", {**GOOD, "assessment": "danger"}), FINISH])
    assert run(session, "q", llm, config, tmp_path).status == "no_judgment"


def test_step_limit(session, config, tmp_path):
    # 서로 다른 호출이라 반복 감지에 먼저 걸리지 않는다
    llm = TestLLM.from_messages([call("view_segments", {"start": i, "end": i}) for i in range(20)])
    config.max_steps = 5
    r = run(session, "q", llm, config, tmp_path)
    assert r.status == "step_limit" and run_json(tmp_path)["status"] == "step_limit"


def test_stuck(session, config, tmp_path):
    r = run(session, "q", TestLLM.from_messages([call("session_overview") for _ in range(10)]), config, tmp_path)
    assert r.status == "stuck" and run_json(tmp_path)["status"] == "stuck"


def test_llm_error_keeps_earlier_events(session, config, tmp_path):
    llm = TestLLM.from_messages([call("view_segments", {"start": i, "end": i}) for i in range(3)]
                                + [RuntimeError("API 실패")])
    r = run(session, "q", llm, config, tmp_path)
    assert r.status == "error" and "API 실패" in r.error
    assert [e["action"]["start"] for e in events(tmp_path) if e["kind"] == "ActionEvent"] == [0, 1, 2]
    assert run_json(tmp_path)["status"] == "error"


# --- 오류 관측과 입력 ---

def test_unknown_tool_and_bad_args_keep_running(session, config, tmp_path):
    llm = TestLLM.from_messages([call("count_people"), call("view_segments", {"start": 0, "end": 99}),
                                 call("submit_judgment", GOOD), FINISH])
    assert run(session, "q", llm, config, tmp_path).status == "submitted"
    blob = json.dumps(events(tmp_path), ensure_ascii=False)
    assert "count_people" in blob and "not found" in blob and "session_overview" in blob
    assert "유효 범위: 0–29" in blob


def test_no_image_content_sent(session, config, tmp_path):
    llm = TestLLM.from_messages([call("view_segments", {"start": 0, "end": 5}), call("submit_judgment", GOOD), FINISH])
    run(session, "q", llm, config, tmp_path)

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


# --- CLI ---

@pytest.mark.parametrize("value", ["0", "-1", "1.5", "abc"])
def test_cli_rejects_invalid_max_steps(value, capsys):
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--session", str(FIXTURE), "--question", "q", "--max-steps", value])
    assert exc.value.code == 2
    assert "--max-steps" in capsys.readouterr().err


@pytest.mark.parametrize("value", [None, "1", "3"])
def test_cli_accepts_max_steps(value):
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    argv = ["--session", str(FIXTURE), "--question", "q"]
    if value is not None:
        argv.extend(["--max-steps", value])
    assert parser.parse_args(argv).max_steps == (None if value is None else int(value))


def test_cli_prints_judgment(tmp_path, capsys):
    llm = TestLLM.from_messages([call("submit_judgment", GOOD), FINISH])
    code = main(["run", "--session", str(FIXTURE), "--question", "q", "--output-dir", str(tmp_path)], llm=llm)
    out = capsys.readouterr().out
    assert code == 0 and "상태: submitted" in out and '"assessment": "caution"' in out
    (rec,) = tmp_path.glob("*/run.json")
    assert json.loads(rec.read_text(encoding="utf-8"))["status"] == "submitted"


def test_cli_input_errors_exit_2(tmp_path, capsys):
    assert main(["run", "--session", str(tmp_path), "--question", "q", "--output-dir", str(tmp_path)],
                llm=TestLLM.from_messages([])) == 2
    assert "session.json" in capsys.readouterr().err
    assert main(["run", "--session", str(FIXTURE), "--question", "q", "--config", str(tmp_path / "x.yaml"),
                 "--output-dir", str(tmp_path)], llm=TestLLM.from_messages([])) == 2


def test_cli_non_submitted_exits_1(tmp_path, capsys):
    code = main(["run", "--session", str(FIXTURE), "--question", "q", "--output-dir", str(tmp_path)],
                llm=TestLLM.from_messages([FINISH]))
    assert code == 1 and "상태: no_judgment" in capsys.readouterr().out
    (rec,) = tmp_path.glob("*/run.json")
    assert json.loads(rec.read_text(encoding="utf-8"))["status"] == "no_judgment"


def test_cli_dotenv_keeps_shell_values(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("CONG_TEST_SHELL=from-dotenv\nCONG_TEST_NEW=from-dotenv\n", encoding="utf-8")
    monkeypatch.setattr(run_single, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("CONG_TEST_SHELL", "from-shell")
    monkeypatch.delenv("CONG_TEST_NEW", raising=False)  # 끝나면 다시 지운다
    # 세션 폴더가 비어 있어 입력 오류(2)로 바로 끝난다. .env는 그 전에 읽힌다.
    assert main(["run", "--session", str(tmp_path), "--question", "q"], llm=TestLLM.from_messages([])) == 2
    assert os.environ["CONG_TEST_SHELL"] == "from-shell"
    assert os.environ["CONG_TEST_NEW"] == "from-dotenv"
