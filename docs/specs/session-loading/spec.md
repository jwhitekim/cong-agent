# session-loading spec

세션 폴더의 관측값을 적재하고 기존 판정·트리거 필드를 차단한다.
의존 capability: 없음.

### Requirement: Session Folder Loading
세션 로더는 SHALL 세션 폴더의 `session.json`과 `results.jsonl`을 읽고 비어 있지 않은 결과 행 순서대로 0부터 세그먼트 번호를 부여한다.

#### Scenario: 합성 세션 적재
- GIVEN 30개 세그먼트가 있는 세션 폴더
- WHEN 세션을 적재한다
- THEN 세그먼트 번호는 0–29이고 구역 목록은 중복 없이 이름순으로 제공된다

### Requirement: Session Field Isolation
세션 로더는 SHALL 시간·인원·밀도·속도·구역별 인원과 밀도·집중도·변화 추세·level만 세그먼트에 옮기고 `agent`, `tracks`, `cv_elapsed_sec`, `trigger`, `trigger_reason`, `co_triggered`, `dynamic_thresholds`와 판정 필드 `assessment`, `action`, `reasoning`을 세그먼트 필드에서 제외한다.

#### Scenario: 기존 판정과 트리거가 포함된 입력
- GIVEN 기존 판정·원시 데이터·트리거 정보가 포함된 결과 행
- WHEN 세그먼트로 적재한다
- THEN 세그먼트에는 허용한 관측 필드만 있고 기존 판정·원시 데이터·트리거 필드는 없다

### Requirement: Session Metadata Defaults
세션 로더는 SHALL `session_id`를 문자열로 적재하되 누락 시 폴더 이름을 쓰고, `config_snapshot.SEGMENT_INTERVAL`을 실수로 적재하되 누락 시 5.0을 쓴다.

#### Scenario: 선택 메타데이터 생략
- GIVEN `session_id`와 `config_snapshot`이 없는 유효한 메타데이터
- WHEN 세션을 적재한다
- THEN 세션 식별자는 폴더 이름이고 세그먼트 간격은 5.0이다

### Requirement: Session Input Error Reporting
세션 로더는 SHALL 필수 파일 누락과 메타데이터 JSON 구문 오류를 `SessionError`로 알리고, 결과 행의 JSON·필수 키·자료형·수치 변환 오류에는 파일 이름과 1부터 센 행 번호를 포함한다.

#### Scenario: 결과 파일 누락
- GIVEN `session.json`만 있는 폴더
- WHEN 세션을 적재한다
- THEN `results.jsonl`을 명시한 `SessionError`가 발생한다

#### Scenario: 결과 행 해석 실패
- GIVEN `results.jsonl`의 12행이 잘못된 JSON인 폴더
- WHEN 세션을 적재한다
- THEN 12행을 명시한 `SessionError`가 발생한다

### Requirement: Empty Session Rejection
세션 로더는 SHALL 결과 파일의 빈 줄을 건너뛰고 적재할 세그먼트가 하나도 없으면 `SessionError`로 거부한다.

#### Scenario: 빈 줄만 있는 결과 파일
- GIVEN 유효한 메타데이터와 빈 줄만 있는 `results.jsonl`
- WHEN 세션을 적재한다
- THEN 세그먼트가 없다는 `SessionError`가 발생한다
