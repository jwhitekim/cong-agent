"""CLI: python -m cong_agent run --session <dir> --question "<질문>" """
import argparse
import os
import sys

os.environ.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")

from openhands.sdk import LLM  # noqa: E402

from cong_agent.run import run_single  # noqa: E402


def main(argv: list[str] | None = None, llm: LLM | None = None) -> int:
    p = argparse.ArgumentParser(prog="cong_agent")
    sub = p.add_subparsers(dest="command", required=True)
    run_single.add_arguments(sub.add_parser("run", help="세션 하나에 질문 하나로 에이전트 실행"))
    args = p.parse_args(argv)
    return run_single.main(args, llm=llm)


if __name__ == "__main__":
    sys.exit(main())
