---
paths:
  - "src/cong_agent/session.py"
  - "src/cong_agent/tools/**"
---

# 세션 적재와 조회 도구 (에이전트-컴퓨터 인터페이스)

## 세션 적재 (`session.py`)

- `session.json`이나 `results.jsonl`이 없거나 JSONL 행을 해석할 수 없으면 LLM을 부르기 전에 `SessionError`로 멈춘다. 메시지에 파일 이름과 행 번호(1부터)를 넣는다.
- 세그먼트 번호는 0부터 매긴다.

## 도구 구조

- 도구 로직은 `tools/query.py`, `tools/submit.py`의 순수 함수 `fn(session, **args) -> str`이다. SDK를 모른다.
- `tools/openhands.py`가 이를 SDK `ToolDefinition`으로 감싼다. 도구를 추가하면 순수 함수 → `tools/__init__.py`의 `TOOLS` → `openhands.py`의 Action·Tool 클래스·`TOOL_CLASSES` 순으로 넣는다.
- 도구 이름은 SDK가 클래스 이름에서 만든다(`ViewSegmentsTool` → `view_segments`). `TOOLS`의 이름과 같아야 한다.

## 출력 규칙 (`tools/format.py` 한 곳에서)

- 짧고 일정한 텍스트. 실수는 소수 둘째 자리.
- 표는 한 번에 최대 20행. 잘리면 남은 범위를 알린다.
- 번호 목록은 최대 50개. 전체 일치 개수는 항상 보인다. 일치 0개는 오류가 아니라 "일치 0개"로 답한다.
- 출력에는 관측값과 단순 집계(개수, 최소, 최대, 평균)만 담는다.

## 입력 오류

- 잘못된 입력은 `ToolError`로 올리고, 래퍼가 `is_error=True` 관측으로 바꿔 루프를 계속한다. 메시지에는 고칠 방법(유효 범위, 허용 값, 사용 가능한 구역)을 넣는다.
- Action은 SDK 기본값대로 모르는 인자를 거부한다(`extra="forbid"`). 그래서 `trigger` 같은 옛 인자는 오류가 된다.
- 예외는 `SubmitJudgmentAction` 하나다. 모르는 인자를 받아 두고 `validate_judgment`가 숫자 카운트 필드를 걷어낸다. 거부가 아니라 제거가 요구사항이다.

## 판정 검증 (`validate_judgment`)

- 필수: `assessment`(normal/caution/anomaly), `action`(none/monitor/alert), `evidence_segments`(유효 번호 1개 이상), `summary`, `reasoning`(빈 문자열 불가).
- 실패하면 저장하지 않고 오류 관측을 돌려준다. 유효한 제출이 여러 번이면 마지막 것을 쓴다.
- `summary` 필드는 SDK가 모든 도구에 넣는 메타 필드와 이름이 같다. SDK는 도구 자체 필드를 우선하므로 그대로 둬도 된다.
