# Spec Delta

## MODIFIED Requirements

### Requirement: 질문 하나당 실행 한 번
시스템은 세션 폴더와 자연어 질문 하나를 받아 실행 한 번을 시작해야 한다(SHALL). 각 단계에서 LLM이 고른 도구를 실행하고 그 관측을 다음 LLM 입력에 붙인다. LLM 입력은 텍스트뿐이며 이미지나 픽셀을 보내서는 안 된다(MUST).

#### Scenario: 도구 두 번 후 제출하고 종료
- **WHEN** LLM이 개요 도구, 구간 보기 도구, 판정 제출, 종료(`finish`) 순서로 호출한다
- **THEN** 실행은 끝나고 최종 상태는 `submitted`이며 저장된 판정은 제출한 판정과 같다

### Requirement: 단계 제한
실행은 설정된 최대 단계 수(기본 15)를 넘어서는 안 된다(MUST). 제한에 닿으면 더 이상 LLM을 부르지 않고 최종 상태 `step_limit`으로 끝낸다. 그때까지 유효한 판정이 제출됐더라도 상태는 `step_limit`이며 판정은 기록에 함께 남긴다.

#### Scenario: 끝내지 않는 LLM
- **WHEN** LLM이 15단계 동안 `finish`를 호출하지 않는다
- **THEN** 실행은 추가 LLM 호출 없이 `step_limit` 상태로 끝난다

### Requirement: 잘못된 도구 호출은 오류 관측으로 돌려줌
없는 도구 이름이나 잘못된 인자로 호출하면 시스템은 실행을 멈추지 말고 무엇이 틀렸는지 알려 주는 오류 관측을 LLM에 돌려줘야 한다(SHALL). 이 호출도 한 단계로 센다.

#### Scenario: 잘못된 인자
- **WHEN** LLM이 `view_segments`를 범위 밖 번호로 호출한다
- **THEN** 다음 LLM 입력에는 유효 범위를 알려 주는 오류 관측이 있고 실행은 계속된다

### Requirement: 최종 판정 스키마
판정 제출은 `assessment`(normal/caution/anomaly), `action`(none/monitor/alert), `evidence_segments`(세그먼트 번호 1개 이상), `summary`, `reasoning`을 모두 담아야 한다(MUST). 값이 틀리거나 없는 세그먼트 번호를 가리키면 판정을 저장하지 않고 오류 관측을 돌려준다. 유효한 제출이 여러 번이면 마지막 것을 판정으로 쓴다.

#### Scenario: 잘못된 등급 값
- **WHEN** LLM이 `assessment="danger"`로 제출한다
- **THEN** 판정은 저장되지 않고, 허용 값을 알려 주는 오류 관측이 돌아간다

#### Scenario: 없는 근거 세그먼트
- **WHEN** 400개 세그먼트 세션에서 `evidence_segments=[512]`로 제출한다
- **THEN** 판정은 저장되지 않고 유효 범위를 알려 주는 오류 관측이 돌아간다

### Requirement: 궤적 기록
실행마다 새 출력 폴더를 만들고, 대화 이벤트(LLM 응답, 도구 호출, 관측)를 이벤트가 생길 때마다 그 폴더에 저장해야 한다(SHALL). 실행이 끝나면 같은 폴더에 질문, 세션 경로, 모델 이름, 최대 단계 수, 최종 상태, 판정, 토큰 사용량을 담은 `run.json`을 써야 한다(MUST).

#### Scenario: 정상 종료
- **WHEN** 실행이 `submitted`로 끝난다
- **THEN** 출력 폴더에 이벤트 기록과 `run.json`이 있고, `run.json`의 판정은 저장된 판정과 같다

#### Scenario: 도중 API 실패
- **WHEN** 4번째 LLM 호출이 재시도 후에도 실패한다
- **THEN** 출력 폴더에는 1–3단계 이벤트가 남고 `run.json`의 최종 상태는 `error`이며 오류 메시지를 담는다

### Requirement: 일시적 API 실패 재시도
네트워크 오류, 속도 제한, 서버 오류에 한해 LLM 호출을 최대 3회 다시 보내야 한다(SHALL). 재시도는 단계 수에 포함하지 않는다.

#### Scenario: 한 번 속도 제한
- **WHEN** 첫 LLM 호출이 속도 제한 오류를 받고 두 번째 시도는 성공한다
- **THEN** 실행은 실패하지 않고 다음 단계로 이어진다

## ADDED Requirements

### Requirement: 종료 도구로만 실행 종료
실행은 LLM이 종료 도구(`finish`)를 호출할 때 끝나야 한다(SHALL). 판정 제출만으로는 끝나지 않는다. 종료 시점에 유효한 판정이 저장돼 있으면 최종 상태는 `submitted`, 없으면 `no_judgment`다.

#### Scenario: 제출 없이 종료
- **WHEN** LLM이 판정 제출 없이 `finish`를 호출한다
- **THEN** 실행은 `no_judgment` 상태로 끝나고 판정은 비어 있다

#### Scenario: 잘못된 제출 후 종료
- **WHEN** LLM이 잘못된 판정을 한 번 제출한 뒤 바로 `finish`를 호출한다
- **THEN** 실행은 `no_judgment` 상태로 끝난다

### Requirement: 반복 감지
같은 도구 호출과 같은 관측이 연속 4번 반복되면 실행을 멈추고 최종 상태 `stuck`으로 끝내야 한다(SHALL).

#### Scenario: 같은 호출 반복
- **WHEN** LLM이 같은 인자로 `session_overview`를 연속 4번 호출한다
- **THEN** 실행은 최대 단계 전에 `stuck` 상태로 끝나고, 그 상태가 `run.json`에 남는다

### Requirement: 에이전트 도구 구성 제한
에이전트가 쓸 수 있는 도구는 혼잡도 조회 도구 4개, 판정 제출 도구, 종료 도구, 생각 정리 도구(`think`)뿐이어야 한다(MUST). 터미널, 파일 편집, 브라우저, 이미지 보기 도구는 등록하지 않는다.

#### Scenario: 도구 목록 확인
- **WHEN** 실행을 시작한다
- **THEN** LLM에 전달되는 도구 이름은 `session_overview`, `view_segments`, `find_segments`, `zone_trend`, `submit_judgment`, `finish`, `think`뿐이다
