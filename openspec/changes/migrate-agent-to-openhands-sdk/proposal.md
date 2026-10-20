# Proposal

## Why

첫 버전(`add-congestion-agent-mvp`)은 루프·LLM 호출·궤적 기록을 직접 만들었고, 도구도 `congestion-llm-gating`의 규칙 트리거를 그대로 보여 줬다. 규칙이 고른 구간을 LLM이 한 번 판정하는 구조에서 벗어나려면, 판단 흐름은 검증된 에이전트 프레임워크에 맡기고 에이전트가 트리거 없이 관측값만으로 스스로 구간을 찾게 해야 한다.

## What Changes

- **BREAKING** 자체 에이전트 루프, LLM 클라이언트, 궤적 기록 코드를 지우고 OpenHands software-agent-sdk(`openhands-sdk`)의 `Agent`·`Conversation`·`LLM`으로 바꾼다.
- 세션 적재와 조회 도구 4개, 판정 검증 로직은 남기고 OpenHands `ToolDefinition`(Action → Observation)으로 감싼다.
- **BREAKING** `congestion-llm-gating`의 판정 구조를 버린다. 에이전트는 규칙 트리거(`trigger`, `trigger_reason`, `co_triggered`)와 동적 임계값을 보지 않는다. 대신 검색 도구에 속도·추세 조건을 더해 에이전트가 직접 이상 구간을 찾는다.
- 실행 종료는 OpenHands 내장 `finish` 도구가 맡는다. `submit_judgment`는 판정을 검증해 저장만 하고, 최종 상태(`submitted`, `no_judgment`, `step_limit`, `stuck`, `error`)는 실행 뒤 대화 상태와 저장된 판정으로 정한다.
- 실행 기록은 OpenHands 이벤트 저장(`persistence_dir`)과 실행 요약 파일 `run.json`으로 바꾼다.
- CLI 형태(`python -m cong_agent run --session --question`)는 유지한다.

유지하는 것: perception 관측값(`results.jsonl`)을 입력으로 쓰는 것, 판정 어휘(normal/caution/anomaly, none/monitor/alert), LLM 숫자 카운트 제거, 이미지 금지, 권고 미실행.

범위 밖: OpenHands 원격 작업 공간·샌드박스, 터미널·파일 편집 도구, 영상 직접 처리, 성능 평가.

## Capabilities

### New Capabilities
없음

### Modified Capabilities
- `congestion-aci`: 판정 입력 제외 목록에 트리거 정보를 추가하고, 개요·검색 도구에서 트리거 조건을 빼며, 검색에 속도·추세 조건을 더한다.
- `agent-loop`: 종료 방식(`finish` 도구), 최종 상태 종류, 실행 기록 형식, 재시도 기록 방식이 바뀐다.

두 능력은 `add-congestion-agent-mvp`가 처음 만든다. 그 변경은 아직 아카이브 전이라 `openspec/specs/`에 본 명세가 없으므로, 이 변경을 적용하기 전에 먼저 아카이브해야 한다.

## Impact

- 지우는 코드: `src/cong_agent/agent.py`, `llm.py`, `trajectory.py`와 해당 테스트.
- 바꾸는 코드: `tools/`(OpenHands 도구로 감쌈, 트리거 제거), `session.py`(트리거 필드 버림), `prompt.py`, `__main__.py`, `README.md`.
- 의존성: `openhands-sdk==1.56.0` 추가. 이 패키지가 LiteLLM을 통해 모델을 부르므로 `anthropic` 직접 의존은 뺀다. 모델 이름은 `anthropic/claude-opus-5-5` 형식이다.
- `congestion-llm-gating` 저장소는 계속 읽기만 한다.
