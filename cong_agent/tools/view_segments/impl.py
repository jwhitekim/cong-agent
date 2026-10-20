"""view_segments 실행 로직."""
from cong_agent.environment import Segment, Session
from cong_agent.tools.utils.errors import check_range
from cong_agent.tools.utils.format import WINDOW, num, table, window_note

HEADER = ["idx", "t(s)", "total", "density", "avg_speed", "zones", "concentration",
          "delta_ratio", "density_slope", "speed_trend", "level"]


def _zones(seg: Segment) -> str:
    return " ".join(f"{k}={v}" for k, v in sorted(seg.zone_counts.items()))


def view_segments(session: Session, start: int, end: int) -> str:
    start, end = check_range(session, start, end)
    shown_end = min(end, start + WINDOW - 1)
    segs = session.segments[start : shown_end + 1]
    rows = [[str(s.index), num(s.timestamp), num(s.total), num(s.density), num(s.avg_speed), _zones(s),
             num(s.concentration), num(s.density_delta_ratio), num(s.density_slope), num(s.speed_trend),
             s.level] for s in segs]
    return table(HEADER, rows) + window_note(shown_end, end)
