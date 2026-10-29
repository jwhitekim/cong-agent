from openhands.sdk import Conversation
from openhands.sdk.testing import TestLLM

from cong_agent.agent.agent import build_agent, build_llm
from cong_agent.tools import JudgmentStore
from conftest import AGENT_TOOLS, FINISH


def test_agent_tools_are_only_domain_tools_plus_finish_think(session, config, tmp_path):
    agent = build_agent(session, TestLLM.from_messages([FINISH]), JudgmentStore(), config.system_prompt)
    conv = Conversation(agent=agent, workspace=str(tmp_path), visualizer=None)
    conv.send_message("q")
    conv.run()  # 도구는 첫 실행 때 초기화된다
    assert set(conv.agent.tools_map) == set(AGENT_TOOLS)


def test_system_prompt_names_tools_without_triggers(config):
    for name in AGENT_TOOLS:
        assert name in config.system_prompt
    for word in ("trigger", "트리거", "surge", "stagnation", "hotspot", "conflict"):
        assert word not in config.system_prompt


def test_build_llm(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    llm = build_llm("anthropic/test-model")
    assert llm.model == "anthropic/test-model"
    assert llm.api_key.get_secret_value() == "sk-test"
    assert llm.num_retries == 3 and llm.usage_id == "cong-agent"
    assert "temperature" not in llm.model_fields_set
