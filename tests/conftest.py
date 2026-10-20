from pathlib import Path

import pytest

from cong_agent.session import load_session

FIXTURE = Path(__file__).parent / "fixtures" / "session_small"
REAL_SESSION = Path(__file__).parents[2] / "congestion-llm-gating" / "outputs" / "20260726_210025"


@pytest.fixture
def session():
    return load_session(FIXTURE)
