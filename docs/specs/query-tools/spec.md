# query-tools spec

조회 도구 4개의 관측 출력, 입력 검증, 오류 관측을 정의한다.
의존 capability: session-loading.

### Requirement: Session Overview Output
`session_overview`는 SHALL 세션 식별자, 세그먼트 수와 번호 범위, 간격과 시간 범위, 구역 목록, low·medium·high별 개수, 인원과 평균 속도의 최소·최대를 텍스트로 제공한다.

#### Scenario: 전체 세션 요약
- GIVEN 적재된 30개 세그먼트 세션
- WHEN `session_overview`를 호출한다
- THEN 세그먼트 수는 30개이고 level별 개수의 합은 30이며 인원·평균 속도의 범위가 표시된다

### Requirement: Segment Observation Table
`view_segments`는 SHALL 시작·끝 번호를 포함한 구간의 번호, 시각, 인원, 밀도, 평균 속도, 이름순 구역 인원, 집중도, 밀도 변화율과 기울기, 속도 추세, level을 표로 제공한다.

#### Scenario: 연속 구간 조회
- GIVEN 유효한 세그먼트 번호 0–2
- WHEN `view_segments(start=0, end=2)`를 호출한다
- THEN `idx`로 시작하는 헤더와 해당 세그먼트의 관측 행이 반환된다

### Requirement: Query Output Bounds
조회 도구는 SHALL 관측 실수를 소수 둘째 자리로, 정수를 정수로 표시하고, 세그먼트 표를 최대 20행으로 제한하며 잘린 표의 남은 범위를 안내하고, 번호 목록을 최대 50개로 제한하며 초과 시 생략을 안내한다.

#### Scenario: 표 범위가 표시 한도를 초과함
- GIVEN 세그먼트 번호 0–29가 있는 세션
- WHEN `view_segments(start=0, end=29)`를 호출한다
- THEN 0–19의 20행만 표시하고 남은 범위 20–29를 안내한다

#### Scenario: 수치 표시
- GIVEN 실수 3.14159와 정수 7
- WHEN 관측 수치 표시를 적용한다
- THEN 각각 `3.14`와 `7`로 표시된다

#### Scenario: 긴 번호 목록
- GIVEN 일치 번호 60개
- WHEN 번호 목록을 표시한다
- THEN 처음 50개만 표시하고 생략 안내를 붙인다

### Requirement: Segment Search Conditions
`find_segments`는 SHALL level, 최소 인원, 최대 평균 속도, 최소 밀도 기울기 중 하나 이상의 조건을 받아 AND로 결합하고, 지정한 경계값을 포함해 일치 번호와 전체 일치 개수를 반환한다.

#### Scenario: 여러 조건 결합
- GIVEN low 등급이면서 밀도 기울기가 0.4 이상인 세그먼트가 25번뿐인 세션
- WHEN `find_segments(level="low", min_density_slope=0.4)`를 호출한다
- THEN 일치 1개와 세그먼트 번호 25가 반환된다

#### Scenario: 느린 구간 검색
- GIVEN 평균 속도가 0.5 이하인 구간이 12·13·14번인 세션
- WHEN `find_segments(max_avg_speed=0.5)`를 호출한다
- THEN 일치 3개와 번호 12·13·14가 반환된다

### Requirement: Empty Search Result
`find_segments`는 SHALL 조건에 맞는 세그먼트가 없으면 오류 대신 `일치 0개`를 반환한다.

#### Scenario: 일치하는 인원 조건 없음
- GIVEN 인원이 999 이상인 세그먼트가 없는 세션
- WHEN `find_segments(min_total=999)`를 호출한다
- THEN `일치 0개`가 반환된다

### Requirement: Zone Population Trend
`zone_trend`는 SHALL 지정 구역의 시작·끝을 포함한 범위에서 인원의 최소·최대·평균과 최대 인원 세그먼트 번호를 제공하고, 범위를 생략하면 전체 세션을 사용하며, 해당 구간에 구역 인원이 없으면 0으로 계산한다.

#### Scenario: 지정 범위의 구역 통계
- GIVEN 구역 A와 세그먼트 번호 18–23이 있는 세션
- WHEN `zone_trend(zone="A", start=18, end=23)`을 호출한다
- THEN 해당 6개 세그먼트의 인원 통계와 최대 인원 번호가 반환된다

#### Scenario: 전체 범위 기본값
- GIVEN 30개 세그먼트와 구역 B가 있는 세션
- WHEN `zone_trend(zone="B")`를 호출한다
- THEN 0–29의 30개 세그먼트가 집계 대상이다

### Requirement: Query Argument Validation
조회 함수는 SHALL 정수인 유효 세그먼트 번호와 시작 이하가 아닌 끝 번호를 요구하고, 검색 조건 누락·허용되지 않은 level·잘못된 수치형·존재하지 않는 구역을 `ToolError`로 알린다.

#### Scenario: 범위를 벗어난 번호
- GIVEN 마지막 세그먼트 번호가 29인 세션
- WHEN `view_segments(start=0, end=45)`를 호출한다
- THEN 유효 범위 0–29를 안내하는 `ToolError`가 발생한다

#### Scenario: 시작보다 작은 끝 번호
- GIVEN 세그먼트 번호 2와 5가 있는 세션
- WHEN `view_segments(start=5, end=2)`를 호출한다
- THEN 끝 번호가 시작보다 작다는 `ToolError`가 발생한다

#### Scenario: 검색 조건 누락
- GIVEN 적재된 세션
- WHEN 아무 조건 없이 `find_segments`를 호출한다
- THEN 조건을 하나 이상 지정하라는 `ToolError`가 발생한다

#### Scenario: 잘못된 level
- GIVEN 적재된 세션
- WHEN `find_segments(level="very_high")`를 호출한다
- THEN low·medium·high를 안내하는 `ToolError`가 발생한다

#### Scenario: 없는 구역 조회
- GIVEN 구역 목록이 A·B·C인 세션
- WHEN `zone_trend(zone="D")`를 호출한다
- THEN 사용 가능한 구역 A·B·C를 안내하는 `ToolError`가 발생한다

### Requirement: Query Error Observation
조회 Executor는 SHALL `ToolError`를 `is_error=True`인 텍스트 관측으로 변환하고, 성공 결과는 오류가 아닌 텍스트 관측으로 반환한다.

#### Scenario: 잘못된 조회의 관측 변환
- GIVEN 마지막 번호가 29인 세션의 `view_segments` Executor
- WHEN 끝 번호 99를 담은 Action을 실행한다
- THEN `is_error=True`이고 유효 범위 0–29를 담은 관측이 반환된다

### Requirement: Query Schema Isolation
조회 Action은 SHALL 선언하지 않은 인자를 거부하고, Executor는 도구가 선언한 인자 중 값이 None이 아닌 것만 조회 함수에 전달한다.

#### Scenario: 옛 트리거 인자 거부
- GIVEN `find_segments` Action 스키마
- WHEN `trigger="hotspot"`을 인자로 구성한다
- THEN 스키마 검증 오류가 발생한다

#### Scenario: 생략한 조건 제외
- GIVEN 평균 속도 조건만 있는 `find_segments` Action
- WHEN Executor를 실행한다
- THEN 검색 조건 표시는 `max_avg_speed=0.5`만 포함한다

### Requirement: Query Judgment Isolation
조회 도구는 SHALL 기존 판정·트리거 필드를 읽거나 자체 판정을 만들지 않고 관측값과 단순 집계만 제공하며, 출력과 설명에 판정 어휘 `normal/caution/anomaly`, `none/monitor/alert`, 기존 판정의 `LEAK_` 문구, 트리거 이름과 근거를 추가하지 않는다.

#### Scenario: 차단용 합성 세션 전체 조회
- GIVEN 기존 판정의 `LEAK_` 문구와 트리거 이름·근거가 포함된 합성 세션
- WHEN 조회 4종의 출력과 도구 설명을 확인한다
- THEN 판정 어휘·`LEAK_`·트리거 이름·근거가 노출되지 않는다
