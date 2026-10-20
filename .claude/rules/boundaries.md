# 에이전트가 볼 수 있는 것과 없는 것

이 프로젝트의 전제다. 어떤 파일을 고치든 지킨다.

## 입력

- 입력은 `congestion-llm-gating`이 남긴 세션 폴더(`session.json`, `results.jsonl`) 하나다. 그 저장소는 읽기만 하고, 코드를 import하거나 고치지 않는다.
- 영상·GPU·검출 모델은 쓰지 않는다. 관측값(인원, 밀도, 속도, 구역 인원, 집중도, 추세, `level`)은 이미 계산된 사실로 받는다.

## 에이전트에게 보이면 안 되는 필드

`session.py`가 적재할 때 버린다. `Segment`에 다시 넣지 않는다.

| 필드 | 이유 |
|---|---|
| `agent` (기존 LLM 판정) | 정답을 미리 보여 주는 것과 같다 |
| `tracks`, `cv_elapsed_sec` | 원시 데이터·처리 시간. 판단 입력이 아니다 |
| `trigger`, `trigger_reason`, `co_triggered`, `dynamic_thresholds` | 규칙 트리거 + 1회 판정 구조는 버렸다. 에이전트가 관측값만으로 볼 구간을 찾는다 |

## 판정

- 판정은 에이전트의 `submit_judgment` 제출로만 만든다. 조회 도구는 판정 어휘(normal/caution/anomaly, none/monitor/alert)를 출력하지 않는다.
- `action`은 대응 권고 수준일 뿐이다. 알림·파일 변경·네트워크 호출 같은 부수효과를 일으키지 않는다. 출력은 터미널과 실행 기록뿐이다.
- LLM이 넣은 인원 수 필드(`total_people`, `total`, `count`, `num_people`, `people_count`)는 지운다. 근거 세그먼트 인원(`evidence_totals`)은 코드가 세션 값으로 넣는다. `reasoning` 자유 텍스트 속 숫자는 막지 못하는 알려진 한계다.

## LLM 입력

- 텍스트만 보낸다. 이미지·픽셀은 보내지 않는다.
- 에이전트 도구는 조회 4개(`session_overview`, `view_segments`, `find_segments`, `zone_trend`), `submit_judgment`, SDK 기본 `finish`·`think`뿐이다. 터미널·파일 편집·브라우저·이미지 보기 도구를 추가하지 않는다.
