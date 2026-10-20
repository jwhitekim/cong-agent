"""LLM과 Agent 구성. 루프·재시도·이벤트 저장·반복 감지는 OpenHands SDK가 맡는다."""
import os

from openhands.sdk import LLM, Agent, Tool
from pydantic import SecretStr

from cong_agent.environment import Session
from cong_agent.tools import JudgmentStore, register_tools

MAX_RETRIES = 3


def build_llm(model: str) -> LLM:
    # 현재 모델은 temperature를 받지 않으므로 지정하지 않는다
    key = os.environ.get("ANTHROPIC_API_KEY")
    return LLM(model=model, api_key=SecretStr(key) if key else None,
               num_retries=MAX_RETRIES, usage_id="cong-agent")


def build_agent(session: Session, llm: LLM, store: JudgmentStore, system_prompt: str) -> Agent:
    names = register_tools(session, store)
    # 기본 도구는 FinishTool·ThinkTool만 켠다. 터미널·파일·브라우저 도구는 넣지 않는다.
    return Agent(llm=llm, tools=[Tool(name=n) for n in names],
                 include_default_tools=["FinishTool", "ThinkTool"], system_prompt=system_prompt)
