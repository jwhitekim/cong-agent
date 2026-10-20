"""조회 도구 출력·설명에 판정 어휘, 기존 판정 문구, 트리거 정보가 없는지 fixture 전체를 훑는다."""
import re

from cong_agent.tools import TOOL_CLASSES
from cong_agent.tools.find_segments.impl import find_segments
from cong_agent.tools.session_overview.impl import session_overview
from cong_agent.tools.view_segments.impl import view_segments
from cong_agent.tools.zone_trend.impl import zone_trend
from conftest import QUERY_TOOLS

JUDGMENT_WORDS = re.compile(r"\b(normal|caution|anomaly|monitor|alert)\b|LEAK_")
# 원본 fixture의 트리거 이름과 trigger_reason 문장 조각
TRIGGER_WORDS = re.compile(r"\b(surge|stagnation|hotspot|conflict)\b|trigger|배 > 1\.4|임계 8\.0|지속")


def test_query_outputs_never_contain_judgment_or_triggers(session):
    n = len(session.segments)
    outputs = [session_overview(session)]
    outputs += [view_segments(session, i, min(i + 19, n - 1)) for i in range(0, n, 20)]
    outputs += [find_segments(session, max_avg_speed=1.0, min_total=0)]
    outputs += [find_segments(session, level=l) for l in ("low", "medium", "high")]
    outputs += [zone_trend(session, z) for z in session.zones]
    for out in outputs:
        assert not JUDGMENT_WORDS.search(out), out
        assert not TRIGGER_WORDS.search(out), out


def test_query_tool_descriptions_clean():
    query = [c for c in TOOL_CLASSES if c.name in QUERY_TOOLS]
    assert len(query) == len(QUERY_TOOLS)
    for cls in query:
        assert not JUDGMENT_WORDS.search(cls.tool_description), cls.name
        assert not TRIGGER_WORDS.search(cls.tool_description), cls.name
