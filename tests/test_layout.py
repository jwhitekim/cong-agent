"""저장소 구조가 .claude/rules/layout.md와 같은지 점검한다. 폴더를 바꾸면 둘 다 고친다."""
import subprocess

from cong_agent.tools import TOOL_CLASSES
from conftest import REPO_ROOT

LAYOUT_RULE = REPO_ROOT / ".claude" / "rules" / "layout.md"

REQUIRED = [
    "cong_agent/__init__.py",
    "cong_agent/__main__.py",
    "cong_agent/environment/session.py",
    "cong_agent/tools/__init__.py",
    "cong_agent/tools/utils/format.py",
    "cong_agent/tools/utils/errors.py",
    "cong_agent/tools/utils/base.py",
    "cong_agent/agent/agent.py",
    "cong_agent/agent/status.py",
    "cong_agent/run/run_single.py",
    "config/default.yaml",
    "tests/conftest.py",
    "tests/fixtures/session_small/session.json",
    "tests/fixtures/session_small/results.jsonl",
    "tests/environment",
    "tests/agent",
    "tests/run",
    ".dockerignore",
    ".gitignore",
    "pyproject.toml",
    "README.md",
]
FORBIDDEN = ["src", "outputs"]


def _tool_dirs():
    return sorted(p.name for p in (REPO_ROOT / "cong_agent" / "tools").iterdir()
                  if p.is_dir() and p.name not in {"utils", "__pycache__"})


def test_required_paths_exist():
    missing = [p for p in REQUIRED if not (REPO_ROOT / p).exists()]
    assert not missing, missing


def test_forbidden_paths_absent():
    present = [p for p in FORBIDDEN if (REPO_ROOT / p).exists()]
    assert not present, present


def test_each_tool_folder_is_complete_and_registered():
    names = {cls.name for cls in TOOL_CLASSES}
    assert set(_tool_dirs()) == names  # 폴더 이름 = 도구 이름 = 등록된 도구
    for name in names:
        for f in ("__init__.py", "definition.py", "impl.py"):
            assert (REPO_ROOT / "cong_agent" / "tools" / name / f).is_file(), f"{name}/{f}"


def test_tests_mirror_tool_folders():
    for name in _tool_dirs():
        assert list((REPO_ROOT / "tests" / "tools" / name).glob("test_*.py")), name


def test_layout_rule_lists_every_tool_folder():
    rule = LAYOUT_RULE.read_text(encoding="utf-8")
    for name in _tool_dirs():
        assert f"{name}/" in rule, name


def test_trajectories_ignored_by_git():
    out = subprocess.run(["git", "check-ignore", "trajectories/x"], cwd=REPO_ROOT, capture_output=True)
    assert out.returncode == 0
