"""실행 궤적 JSONL 기록. 이벤트마다 즉시 append + flush해서 도중에 실패해도 남긴다."""
import json
from pathlib import Path
from typing import Any


class Trajectory:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch()

    def write(self, event: dict[str, Any]) -> None:
        # 직렬화를 먼저 해서 실패해도 반쯤 쓴 줄이 남지 않게 한다
        line = json.dumps(event, ensure_ascii=False, default=str) + "\n"
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()

    def read(self) -> list[dict[str, Any]]:
        return [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
