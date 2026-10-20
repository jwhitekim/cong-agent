# Spec Delta

## MODIFIED Requirements

### Requirement: 판정 입력에서 기존 LLM 출력과 원시 트랙 제외
도구 출력은 세션에 기록된 기존 LLM 판정(`agent`), 원시 트랙(`tracks`), 처리 시간(`cv_elapsed_sec`), 규칙 트리거 정보(`trigger`, `trigger_reason`, `co_triggered`), 동적 임계값(`dynamic_thresholds`)을 어떤 형태로도 포함해서는 안 된다(MUST). 에이전트는 perception 관측값과 집계값만 보고 어느 구간을 볼지 스스로 정한다.

#### Scenario: 기존 판정이 있는 세그먼트 조회
- **WHEN** 에이전트가 기존 `agent.assessment`가 `anomaly`인 세그먼트를 조회한다
- **THEN** 도구 출력에는 `assessment`, `action`, `reasoning`, `tracks` 값이 나타나지 않는다

#### Scenario: 트리거가 붙은 세그먼트 조회
- **WHEN** 에이전트가 원본에서 `trigger="hotspot"`, `trigger_reason="hotspot: A구역 14명 > 임계 8.0"`인 세그먼트를 조회한다
- **THEN** 도구 출력에는 트리거 이름(surge/stagnation/hotspot/conflict)과 트리거 근거 문장이 나타나지 않는다

### Requirement: 세션 개요 도구
시스템은 세그먼트 수, 세그먼트 길이(초), 전체 시간 범위, 구역 목록, 혼잡 등급(`level`)별 세그먼트 수, 인원·평균 속도의 최솟값과 최댓값을 돌려주는 개요 도구를 제공해야 한다(SHALL).

#### Scenario: 개요 조회
- **WHEN** 에이전트가 세그먼트 400개 세션의 개요를 요청한다
- **THEN** 출력은 세그먼트 수 400과 `level`별 개수를 보여 주고, 그 개수의 합은 400이다

### Requirement: 세그먼트 검색 도구
시스템은 혼잡 등급, 최소 인원, 최대 평균 속도, 최소 밀도 추세(`density_slope`) 조건을 AND로 묶어 세그먼트를 찾고, 번호 목록과 일치 개수를 돌려주는 도구를 제공해야 한다(SHALL). 조건이 하나도 없으면 오류 관측을 돌려준다. 번호 목록은 최대 50개까지만 보이고 전체 일치 개수는 항상 표시해야 한다(MUST).

#### Scenario: 트리거로 검색
- **WHEN** 에이전트가 `trigger` 조건으로 세그먼트를 찾으려 한다
- **THEN** 도구는 지원하지 않는 인자라는 오류 관측을 돌려주고, 트리거 정보는 보여 주지 않는다

#### Scenario: 느린 구간 검색
- **WHEN** 에이전트가 평균 속도 0.5 이하인 세그먼트를 찾는다
- **THEN** 출력은 일치 개수와 해당 세그먼트 번호를 오름차순으로 보여 준다

#### Scenario: 조건 결합
- **WHEN** 에이전트가 `level=high`이면서 `density_slope` 0.4 이상인 세그먼트를 찾는다
- **THEN** 출력에는 두 조건을 모두 만족하는 세그먼트만 있다

#### Scenario: 일치 없음
- **WHEN** 어떤 세그먼트도 조건을 만족하지 않는다
- **THEN** 출력은 "일치 0개"를 명시하고 오류로 처리하지 않는다
