import dataclasses
import shutil

import pytest

from cong_agent.session import Segment, SessionError, load_session
from conftest import FIXTURE, REAL_SESSION


def test_loads_fixture(session):
    assert len(session.segments) == 30
    assert [s.index for s in session.segments] == list(range(30))
    assert session.zones == ["A", "B", "C"]
    assert session.segment_interval == 5.0


def test_segment_has_no_judgment_or_raw_fields():
    names = {f.name for f in dataclasses.fields(Segment)}
    assert not names & {"agent", "tracks", "cv_elapsed_sec", "assessment", "action", "reasoning"}


def test_missing_file(tmp_path):
    shutil.copy(FIXTURE / "session.json", tmp_path)
    with pytest.raises(SessionError, match="results.jsonl"):
        load_session(tmp_path)


def test_broken_line_reports_line_number(tmp_path):
    shutil.copy(FIXTURE / "session.json", tmp_path)
    lines = (FIXTURE / "results.jsonl").read_text(encoding="utf-8").splitlines()
    lines[11] = "{not json"
    (tmp_path / "results.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(SessionError, match="12행"):
        load_session(tmp_path)


@pytest.mark.skipif(not REAL_SESSION.is_dir(), reason="실제 세션 폴더 없음")
def test_real_session():
    s = load_session(REAL_SESSION)
    assert len(s.segments) == 400
    assert sum(1 for seg in s.segments if seg.trigger) == 101
