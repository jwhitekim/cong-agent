"""질문 하나를 세션 하나에 대해 실행한다 (SWE-agent의 run_single에 해당).

설정·세션 적재 → Conversation 실행 → 최종 상태 판정 → run.json.
"""
import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import yaml
from openhands.sdk import LLM, Conversation

from cong_agent.agent.agent import build_agent, build_llm
from cong_agent.agent.status import RunResult, final_status, token_usage
from cong_agent.environment import Session, SessionError, load_session
from cong_agent.tools import JudgmentStore

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "default.yaml"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "trajectories"


class ConfigError(Exception):
    pass


@dataclass
class RunConfig:
    model: str
    max_steps: int
    system_prompt: str
    path: str = ""


def load_config(path: str | Path = DEFAULT_CONFIG, *, model: str | None = None,
                max_steps: int | None = None) -> RunConfig:
    """설정 파일을 읽는다. 덮어쓰기 순서: 인자 > 환경변수 CONG_AGENT_MODEL > 파일."""
    path = Path(path)
    try:
        agent = (yaml.safe_load(path.read_text(encoding="utf-8")) or {})["agent"]
        cfg = RunConfig(model=str(agent["model"]), max_steps=int(agent["max_steps"]),
                        system_prompt=str(agent["system_prompt"]), path=str(path))
    except (OSError, yaml.YAMLError, KeyError, TypeError, ValueError) as e:
        raise ConfigError(f"설정 파일을 읽을 수 없습니다 ({path}): {type(e).__name__}: {e}") from e
    cfg.model = model or os.environ.get("CONG_AGENT_MODEL") or cfg.model
    cfg.max_steps = cfg.max_steps if max_steps is None else max_steps
    return cfg


def run(session: Session, question: str, llm: LLM, config: RunConfig, run_dir: str | Path) -> RunResult:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    store = JudgmentStore()
    # delete_on_close=False: 기본값 True는 실행 기록을 지운다
    conversation = Conversation(
        agent=build_agent(session, llm, store, config.system_prompt), workspace=str(run_dir),
        persistence_dir=str(run_dir / "conversation"), max_iteration_per_run=config.max_steps,
        visualizer=None, delete_on_close=False)

    error = None
    try:
        conversation.send_message(question)
        conversation.run()
        status, error = final_status(conversation, store)
    except Exception as e:
        status, error = "error", f"{type(e).__name__}: {e}"

    result = RunResult(status=status, judgment=store.judgment, error=error,
                       usage=token_usage(conversation), run_dir=str(run_dir))
    summary = {"question": question, "session": str(session.path), "session_id": session.session_id,
               "config": config.path, "model": llm.model, "max_steps": config.max_steps, **asdict(result)}
    (run_dir / "run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str),
                                     encoding="utf-8")
    return result


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("1 이상의 정수여야 합니다")
    return number


def add_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("--session", required=True, help="session.json과 results.jsonl이 있는 폴더")
    p.add_argument("--question", required=True)
    p.add_argument("--config", default=str(DEFAULT_CONFIG))
    p.add_argument("--max-steps", type=_positive_int, default=None, help="설정 파일 값을 덮어씀")
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="실행 기록을 둘 상위 폴더")


def main(args: argparse.Namespace, llm: LLM | None = None) -> int:
    try:
        config = load_config(args.config, max_steps=args.max_steps)
        session = load_session(args.session)
    except (ConfigError, SessionError) as e:
        print(f"입력 오류: {e}", file=sys.stderr)
        return 2

    run_dir = Path(args.output_dir) / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    result = run(session, args.question, llm or build_llm(config.model), config, run_dir)

    print(f"상태: {result.status} (입력 토큰 {result.usage.get('input_tokens', 0)}, "
          f"출력 토큰 {result.usage.get('output_tokens', 0)})")
    if result.judgment:
        print(json.dumps(result.judgment, ensure_ascii=False, indent=2))
    if result.error:
        print(f"오류: {result.error}", file=sys.stderr)
    print(f"기록: {run_dir}")
    return 0 if result.status == "submitted" else 1
