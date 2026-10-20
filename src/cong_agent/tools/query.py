"""세션 조회 도구. 모두 읽기 전용이며 관측값과 단순 집계만 돌려준다."""
from collections import Counter

from cong_agent.session import Segment, Session
from cong_agent.tools.base import Tool, ToolError, check_index
from cong_agent.tools.format import WINDOW, index_list, num, table, window_note

TRIGGERS = ("surge", "stagnation", "hotspot", "conflict")
LEVELS = ("low", "medium", "high")


def _zones(seg: Segment) -> str:
    return " ".join(f"{k}={v}" for k, v in sorted(seg.zone_counts.items()))


def _trigger(seg: Segment) -> str:
    if not seg.trigger:
        return "-"
    if seg.co_triggered:
        return f"{seg.trigger}(+{','.join(seg.co_triggered)})"
    return seg.trigger


def session_overview(session: Session) -> str:
    segs = session.segments
    trig = Counter(s.trigger for s in segs if s.trigger)
    lev = Counter(s.level for s in segs)
    lines = [
        f"세션 {session.session_id}: 세그먼트 {len(segs)}개 (번호 0–{len(segs) - 1})",
        f"세그먼트 길이 {num(session.segment_interval)}초, 시간 범위 {num(segs[0].timestamp)}–{num(segs[-1].timestamp)}초",
        f"구역: {', '.join(session.zones)}",
        f"트리거 있는 세그먼트 {sum(trig.values())}개: "
        + ", ".join(f"{t} {trig.get(t, 0)}" for t in TRIGGERS),
        "혼잡 등급(level)별 세그먼트: " + ", ".join(f"{l} {lev.get(l, 0)}" for l in LEVELS),
        f"인원(total) 최소 {min(s.total for s in segs)}, 최대 {max(s.total for s in segs)}",
    ]
    return "\n".join(lines)


def view_segments(session: Session, start: int, end: int) -> str:
    start = check_index(session, start, "start")
    end = check_index(session, end, "end")
    if end < start:
        raise ToolError(f"end({end})는 start({start})보다 작을 수 없습니다")
    shown_end = min(end, start + WINDOW - 1)
    segs = session.segments[start : shown_end + 1]
    header = ["idx", "t(s)", "total", "density", "avg_speed", "zones", "concentration",
              "delta_ratio", "density_slope", "speed_trend", "level", "trigger"]
    rows = [[str(s.index), num(s.timestamp), num(s.total), num(s.density), num(s.avg_speed), _zones(s),
             num(s.concentration), num(s.density_delta_ratio), num(s.density_slope), num(s.speed_trend),
             s.level, _trigger(s)] for s in segs]
    out = table(header, rows)
    reasons = [f"{s.index}: {s.trigger_reason}" for s in segs if s.trigger_reason]
    if reasons:
        out += "\n트리거 근거:\n" + "\n".join(reasons)
    return out + window_note(shown_end, end)


def find_segments(session: Session, trigger: str | None = None, level: str | None = None,
                  min_total: int | None = None) -> str:
    if trigger is not None and trigger not in TRIGGERS:
        raise ToolError(f"trigger는 {', '.join(TRIGGERS)} 중 하나여야 합니다: {trigger!r}")
    if level is not None and level not in LEVELS:
        raise ToolError(f"level은 {', '.join(LEVELS)} 중 하나여야 합니다: {level!r}")
    if min_total is not None and (not isinstance(min_total, int) or isinstance(min_total, bool)):
        raise ToolError(f"min_total은 정수여야 합니다: {min_total!r}")
    if trigger is None and level is None and min_total is None:
        raise ToolError("trigger, level, min_total 중 하나 이상을 지정하세요")

    hits = [s.index for s in session.segments
            if (trigger is None or s.trigger == trigger or trigger in s.co_triggered)
            and (level is None or s.level == level)
            and (min_total is None or s.total >= min_total)]
    cond = ", ".join(f"{k}={v}" for k, v in
                     (("trigger", trigger), ("level", level), ("min_total", min_total)) if v is not None)
    if not hits:
        return f"조건 {cond}: 일치 0개"
    return f"조건 {cond}: 일치 {len(hits)}개\n세그먼트: {index_list(hits)}"


def zone_trend(session: Session, zone: str, start: int | None = None, end: int | None = None) -> str:
    if zone not in session.zones:
        raise ToolError(f"구역 {zone!r}가 없습니다. 사용 가능한 구역: {', '.join(session.zones)}")
    start = 0 if start is None else check_index(session, start, "start")
    end = len(session.segments) - 1 if end is None else check_index(session, end, "end")
    if end < start:
        raise ToolError(f"end({end})는 start({start})보다 작을 수 없습니다")
    segs = session.segments[start : end + 1]
    counts = [s.zone_counts.get(zone, 0) for s in segs]
    peak = max(counts)
    peak_idx = [s.index for s, c in zip(segs, counts) if c == peak]
    return (f"구역 {zone}, 세그먼트 {start}–{end} ({len(segs)}개)\n"
            f"인원 최소 {min(counts)}, 최대 {peak}, 평균 {num(sum(counts) / len(counts))}\n"
            f"최대 인원 세그먼트: {index_list(peak_idx)}")


_RANGE = {"start": {"type": "integer", "description": "시작 세그먼트 번호(포함)"},
          "end": {"type": "integer", "description": "끝 세그먼트 번호(포함)"}}

QUERY_TOOLS = [
    Tool("session_overview",
         "세션 전체 요약: 세그먼트 수·길이·시간 범위, 구역 목록, 트리거 종류별 개수, level별 개수, 인원 범위.",
         {"type": "object", "properties": {}}, session_overview),
    Tool("view_segments",
         f"start–end 범위 세그먼트의 관측값 표. 한 번에 최대 {WINDOW}행. 트리거 근거 문장 포함.",
         {"type": "object", "properties": _RANGE, "required": ["start", "end"]}, view_segments),
    Tool("find_segments",
         "조건(트리거 종류, level, 최소 인원)에 맞는 세그먼트 번호와 일치 개수. 조건은 AND로 결합.",
         {"type": "object", "properties": {
             "trigger": {"type": "string", "enum": list(TRIGGERS)},
             "level": {"type": "string", "enum": list(LEVELS)},
             "min_total": {"type": "integer", "description": "이 인원 이상"}}},
         find_segments),
    Tool("zone_trend",
         "한 구역의 인원 최소·최대·평균과 최대 인원 세그먼트. 범위를 생략하면 전체.",
         {"type": "object", "properties": {"zone": {"type": "string"}, **_RANGE}, "required": ["zone"]},
         zone_trend),
]
