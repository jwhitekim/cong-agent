"""CLI: python -m cong_agent run --session <dir> --question "<질문>" """
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from cong_agent.agent import DEFAULT_MAX_STEPS, run_agent
from cong_agent.llm import AnthropicClient, LLMClient
from cong_agent.session import SessionError, load_session
from cong_agent.trajectory import Trajectory


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cong_agent")
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="세션 하나에 질문 하나로 에이전트 실행")
    run.add_argument("--session", required=True, help="session.json과 results.jsonl이 있는 폴더")
    run.add_argument("--question", required=True)
    run.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    run.add_argument("--out", default="outputs", help="실행 기록을 둘 상위 폴더")
    return p


def main(argv: list[str] | None = None, llm: LLMClient | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        session = load_session(args.session)
    except SessionError as e:
        print(f"세션 오류: {e}", file=sys.stderr)
        return 2

    run_dir = Path(args.out) / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    trajectory = Trajectory(run_dir / "trajectory.jsonl")
    result = run_agent(session, args.question, llm or AnthropicClient(), trajectory, args.max_steps)

    print(f"상태: {result.status} ({result.steps}단계, 입력 토큰 {result.usage.get('input_tokens', 0)}, "
          f"출력 토큰 {result.usage.get('output_tokens', 0)})")
    if result.judgment:
        print(json.dumps(result.judgment, ensure_ascii=False, indent=2))
    if result.error:
        print(f"오류: {result.error}", file=sys.stderr)
    print(f"기록: {trajectory.path}")
    return 0 if result.status == "submitted" else 1


if __name__ == "__main__":
    sys.exit(main())
