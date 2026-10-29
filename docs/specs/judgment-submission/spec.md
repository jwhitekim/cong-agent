# judgment-submission spec

판정 제출의 검증, 인원 필드 보정, 저장과 오류 관측을 정의한다.
의존 capability: session-loading, query-tools.

### Requirement: Judgment Payload Validation
판정 검증기는 SHALL `assessment`, `action`, `evidence_segments`, `summary`, `reasoning`을 필수로 요구하고, assessment는 normal·caution·anomaly, action은 none·monitor·alert, 근거는 유효한 정수 번호가 하나 이상인 목록, 두 텍스트는 공백뿐이지 않은 문자열로 제한하며 위반 시 `ToolError`를 발생시킨다.

#### Scenario: 허용되지 않은 판정
- GIVEN 나머지 필수 필드가 유효한 제출
- WHEN assessment가 `danger`인 판정을 검증한다
- THEN 허용 값 normal·caution·anomaly를 안내하는 `ToolError`가 발생한다

#### Scenario: 근거 범위 초과
- GIVEN 마지막 세그먼트 번호가 29인 세션
- WHEN 근거 번호 512를 제출한다
- THEN 유효 범위 0–29를 안내하는 `ToolError`가 발생한다

#### Scenario: 필수 필드 누락
- GIVEN reasoning이 빠진 제출 데이터
- WHEN 판정을 검증한다
- THEN reasoning 누락을 알리는 `ToolError`가 발생한다

### Requirement: Judgment Count Correction
제출 Action은 SHALL 추가 인자를 허용하고, 판정 검증기는 `total_people`, `total`, `count`, `num_people`, `people_count`를 값과 관계없이 제거한 뒤 `evidence_totals`를 근거 번호별 세션 인원으로 채워 제출값을 대체한다.

#### Scenario: LLM 인원 필드 제거
- GIVEN 근거 번호가 20·21이고 `total_people=99`가 추가된 유효한 제출
- WHEN `submit_judgment`를 실행한다
- THEN 저장된 판정에 `total_people`은 없고 `evidence_totals`는 20·21번의 실제 세션 인원이다

### Requirement: Judgment Store Replacement
`JudgmentStore`는 SHALL 검증에 성공한 마지막 판정만 저장하고, 검증 실패 시 기존 저장값을 유지한다.

#### Scenario: 유효 제출 뒤 실패
- GIVEN caution 판정과 anomaly 판정을 차례로 유효하게 제출한 저장소
- WHEN assessment가 `danger`인 판정을 제출한다
- THEN 저장소에는 마지막 유효 판정인 anomaly가 남는다

### Requirement: Judgment Submission Observation
판정 Executor는 SHALL 검증 실패를 `is_error=True` 관측으로 반환하고, 성공 시 판정을 저장한 뒤 실행을 끝내지 않고 `finish` 호출을 안내하는 관측을 반환한다.

#### Scenario: 성공한 제출 뒤 종료
- GIVEN 유효한 판정과 실행 중인 에이전트
- WHEN `submit_judgment` 뒤 `finish`를 호출한다
- THEN 제출 수락 관측 뒤 별도 finish 호출이 기록되고 최종 상태는 submitted이다

#### Scenario: 실패한 첫 제출
- GIVEN 저장된 판정이 없는 상태
- WHEN assessment가 `danger`인 판정을 제출한다
- THEN 오류 관측이 반환되고 저장소는 비어 있다
