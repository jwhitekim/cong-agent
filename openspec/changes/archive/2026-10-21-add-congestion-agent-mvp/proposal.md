# Proposal

## Why

`congestion-llm-gating`은 규칙이 고른 구간에서 LLM을 한 번만 부르는 워크플로우라서, LLM이 스스로 증거를 더 찾거나 여러 구간을 비교할 수 없다. 그 저장소가 "향후 확장"으로 미뤄 둔 에이전트형 혼잡도 분석(상태 유지·도구 선택·반복 판단)을, 이미 저장된 perception 결과 위에서 가장 작은 형태로 한 번 만들어 본다.

## What Changes

- 새 Python 프로젝트 `cong-agent`를 만든다. 입력은 `congestion-llm-gating`이 남긴 세션 폴더(`session.json`, `results.jsonl`)이며, 영상·GPU·YOLO는 쓰지 않는다.
- 혼잡도 전용 에이전트-컴퓨터 인터페이스(ACI, 에이전트가 쓰는 도구 묶음)를 만든다. 도구는 세션 관측값을 **읽기만** 하고, 출력은 짧고 고정된 형식의 텍스트다. (SWE-agent의 ACI 원칙, DDI-ACI의 "규약은 도구 안에 담는다" 원칙)
- 에이전트 루프를 만든다. LLM이 도구 하나를 고르면 실행하고 관측(observation)을 돌려주는 과정을 최대 단계 수 안에서 반복하며, `submit_judgment` 도구로 끝낸다. (OpenHands software-agent-sdk의 Agent / Tool(Action→Observation) / Conversation 이벤트 구조를 단순화해 따른다)
- 최종 판정은 `congestion-llm-gating`과 같은 어휘(`assessment`: normal/caution/anomaly, `action`: none/monitor/alert)를 쓰고, LLM이 만든 숫자 카운트 필드는 걷어낸다. `action`은 실행이 아니라 권고 수준이다.
- 실행 한 번마다 궤적(trajectory, LLM 호출·도구 호출·관측·최종 판정의 순서 기록)을 JSONL로 남긴다.
- CLI 하나: `python -m cong_agent run --session <dir> --question "<질문>"`.

범위 밖: 실시간 영상 처리, 실제 대응 행동 실행, 성능 평가·벤치마크, 여러 LLM 벤더 지원, OpenHands·SWE-agent 패키지 의존.

## Capabilities

### New Capabilities
- `congestion-aci`: 세션 관측값을 읽기 전용으로 조회하는 혼잡도 도구 묶음과, 그 도구들의 입력 검증·출력 형식·오류 메시지 계약
- `agent-loop`: LLM이 도구를 골라 반복 호출하고 판정을 제출하는 실행 루프, 단계 제한, 최종 판정 스키마 검증, 궤적 기록

### Modified Capabilities
없음 (새 프로젝트)

## Impact

- 새 코드: `cong-agent/src/cong_agent/` 패키지, `tests/`, `pyproject.toml`.
- 의존성: `anthropic` SDK(기본 모델 `claude-opus-5-5`, 환경변수로 변경), `pytest`. API 키 `ANTHROPIC_API_KEY` 필요.
- 외부 데이터: `../congestion-llm-gating/outputs/<timestamp>/` 세션 폴더를 읽기만 한다. 그 저장소의 코드는 import하지도 수정하지도 않는다.
