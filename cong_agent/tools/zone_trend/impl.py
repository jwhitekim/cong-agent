"""zone_trend 실행 로직."""
from cong_agent.environment import Session
from cong_agent.tools.utils.errors import ToolError, check_range
from cong_agent.tools.utils.format import index_list, num


def zone_trend(session: Session, zone: str, start: int | None = None, end: int | None = None) -> str:
    if zone not in session.zones:
        raise ToolError(f"구역 {zone!r}가 없습니다. 사용 가능한 구역: {', '.join(session.zones)}")
    start, end = check_range(session, start, end)
    segs = session.segments[start : end + 1]
    counts = [s.zone_counts.get(zone, 0) for s in segs]
    peak = max(counts)
    peak_idx = [s.index for s, c in zip(segs, counts) if c == peak]
    return (f"구역 {zone}, 세그먼트 {start}–{end} ({len(segs)}개)\n"
            f"인원 최소 {min(counts)}, 최대 {peak}, 평균 {num(sum(counts) / len(counts))}\n"
            f"최대 인원 세그먼트: {index_list(peak_idx)}")
