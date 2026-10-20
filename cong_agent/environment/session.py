"""congestion-llm-gating 세션 폴더 적재.

판정 입력 차단은 여기서 한다. 기존 LLM 판정(`agent`), 원시 트랙(`tracks`),
처리 시간(`cv_elapsed_sec`), 규칙 트리거 정보(`trigger`, `trigger_reason`,
`co_triggered`, `dynamic_thresholds`)는 Segment로 옮기지 않는다 — 도구가 실수로
노출할 경로 자체를 없애기 위해서다. 에이전트는 관측값만 보고 볼 구간을 스스로 정한다.
"""
import json
from dataclasses import dataclass
from pathlib import Path


LEVELS = ("low", "medium", "high")  # aggregated.level 값 (perception 쪽 집계)


class SessionError(Exception):
    pass


@dataclass(frozen=True)
class Segment:
    index: int
    timestamp: float
    total: int
    density: float
    avg_speed: float
    zone_counts: dict[str, int]
    zone_density: dict[str, float]
    concentration: float
    density_delta_ratio: float
    speed_trend: float
    density_slope: float
    level: str


@dataclass(frozen=True)
class Session:
    path: Path
    session_id: str
    segment_interval: float
    segments: tuple[Segment, ...]

    @property
    def zones(self) -> list[str]:
        names: set[str] = set()
        for s in self.segments:
            names.update(s.zone_counts)
        return sorted(names)


def _to_segment(index: int, row: dict) -> Segment:
    p = row["perception"]
    a = row["aggregated"]
    return Segment(
        index=index,
        timestamp=float(row["timestamp"]),
        total=int(p["total"]),
        density=float(p["density"]),
        avg_speed=float(p["avg_speed"]),
        zone_counts={k: int(v) for k, v in p["zone_counts"].items()},
        zone_density={k: float(v) for k, v in p["zone_density"].items()},
        concentration=float(p["concentration"]),
        density_delta_ratio=float(a["density_delta_ratio"]),
        speed_trend=float(a["speed_trend"]),
        density_slope=float(a["density_slope"]),
        level=a["level"],
    )


def load_session(path: str | Path) -> Session:
    path = Path(path)
    meta_path = path / "session.json"
    results_path = path / "results.jsonl"
    for f in (meta_path, results_path):
        if not f.is_file():
            raise SessionError(f"{f.name} 파일이 없습니다: {f}")

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SessionError(f"session.json을 해석할 수 없습니다: {e}") from e

    segments = []
    with results_path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                segments.append(_to_segment(len(segments), row))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                raise SessionError(f"results.jsonl {lineno}행을 해석할 수 없습니다: {e}") from e

    if not segments:
        raise SessionError("results.jsonl에 세그먼트가 없습니다")

    interval = meta.get("config_snapshot", {}).get("SEGMENT_INTERVAL", 5.0)
    return Session(
        path=path,
        session_id=str(meta.get("session_id", path.name)),
        segment_interval=float(interval),
        segments=tuple(segments),
    )
