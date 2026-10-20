"""session_overview 실행 로직."""
from collections import Counter

from cong_agent.environment import LEVELS, Session
from cong_agent.tools.utils.format import num


def session_overview(session: Session) -> str:
    segs = session.segments
    lev = Counter(s.level for s in segs)
    lines = [
        f"세션 {session.session_id}: 세그먼트 {len(segs)}개 (번호 0–{len(segs) - 1})",
        f"세그먼트 길이 {num(session.segment_interval)}초, 시간 범위 {num(segs[0].timestamp)}–{num(segs[-1].timestamp)}초",
        f"구역: {', '.join(session.zones)}",
        "혼잡 등급(level)별 세그먼트: " + ", ".join(f"{l} {lev.get(l, 0)}" for l in LEVELS),
        f"인원(total) 최소 {min(s.total for s in segs)}, 최대 {max(s.total for s in segs)}",
        f"평균 속도(avg_speed) 최소 {num(min(s.avg_speed for s in segs))}, 최대 {num(max(s.avg_speed for s in segs))}",
    ]
    return "\n".join(lines)
