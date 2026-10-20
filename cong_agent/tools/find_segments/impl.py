"""find_segments 실행 로직."""
from cong_agent.environment import LEVELS, Session
from cong_agent.tools.utils.errors import ToolError
from cong_agent.tools.utils.format import index_list


def _check_number(name: str, v: object) -> None:
    if v is not None and (not isinstance(v, (int, float)) or isinstance(v, bool)):
        raise ToolError(f"{name}은 숫자여야 합니다: {v!r}")


def find_segments(session: Session, level: str | None = None, min_total: int | None = None,
                  max_avg_speed: float | None = None, min_density_slope: float | None = None) -> str:
    if level is not None and level not in LEVELS:
        raise ToolError(f"level은 {', '.join(LEVELS)} 중 하나여야 합니다: {level!r}")
    if min_total is not None and (not isinstance(min_total, int) or isinstance(min_total, bool)):
        raise ToolError(f"min_total은 정수여야 합니다: {min_total!r}")
    _check_number("max_avg_speed", max_avg_speed)
    _check_number("min_density_slope", min_density_slope)
    conds = (("level", level), ("min_total", min_total),
             ("max_avg_speed", max_avg_speed), ("min_density_slope", min_density_slope))
    if all(v is None for _, v in conds):
        raise ToolError("level, min_total, max_avg_speed, min_density_slope 중 하나 이상을 지정하세요")

    hits = [s.index for s in session.segments
            if (level is None or s.level == level)
            and (min_total is None or s.total >= min_total)
            and (max_avg_speed is None or s.avg_speed <= max_avg_speed)
            and (min_density_slope is None or s.density_slope >= min_density_slope)]
    cond = ", ".join(f"{k}={v}" for k, v in conds if v is not None)
    if not hits:
        return f"조건 {cond}: 일치 0개"
    return f"조건 {cond}: 일치 {len(hits)}개\n세그먼트: {index_list(hits)}"
