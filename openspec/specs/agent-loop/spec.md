# agent-loop Specification

## Purpose

사용자 질문 하나에 대해 LLM이 혼잡도 도구를 골라 반복 호출하고, 검증된 판정을 제출하거나 단계 제한에 걸려 끝나는 실행 루프와 그 기록을 정의한다.

## Requirements

### Requirement: 질문 하나당 실행 한 번
시스템은 세션 폴더와 자연어 질문 하나를 받아 실행 한 번을 시작해야 한다(SHALL). 각 단계에서 LLM이 고른 도구를 실행하고 그 관측을 다음 LLM 입력에 붙인다. LLM 입력은 텍스트뿐이며 이미지나 픽셀을 보내서는 안 된다(MUST).

#### Scenario: 도구 두 번 후 제출
- **WHEN** LLM이 개요 도구, 구간 보기 도구, 판정 제출 순서로 호출한다
- **THEN** 실행은 3단계로 끝나고 최종 상태는 `submitted`다

### Requirement: 단계 제한
실행은 설정된 최대 단계 수(기본 15)를 넘어서는 안 된다(MUST). 제한에 닿으면 판정 없이 최종 상태 `step_limit`으로 끝낸다.

#### Scenario: 제출하지 않는 LLM
- **WHEN** LLM이 15단계 동안 판정을 제출하지 않는다
- **THEN** 실행은 16번째 LLM 호출 없이 `step_limit` 상태와 빈 판정으로 끝난다

### Requirement: 잘못된 도구 호출은 오류 관측으로 돌려줌
없는 도구 이름이나 잘못된 인자로 호출하면 시스템은 실행을 멈추지 말고 무엇이 틀렸는지 알려 주는 오류 관측을 돌려줘야 한다(SHALL). 이 호출도 한 단계로 센다.

#### Scenario: 없는 도구
- **WHEN** LLM이 등록되지 않은 도구 `count_people`를 호출한다
- **THEN** 다음 관측은 사용 가능한 도구 이름 목록을 담은 오류이고 실행은 계속된다

### Requirement: 최종 판정 스키마
판정 제출은 `assessment`(normal/caution/anomaly), `action`(none/monitor/alert), `evidence_segments`(세그먼트 번호 1개 이상), `summary`, `reasoning`을 모두 담아야 한다(MUST). 값이 틀리거나 없는 세그먼트 번호를 가리키면 오류 관측을 돌려주고 루프를 계속한다.

#### Scenario: 잘못된 등급 값
- **WHEN** LLM이 `assessment="danger"`로 제출한다
- **THEN** 실행은 끝나지 않고, 허용 값을 알려 주는 오류 관측이 돌아간다

#### Scenario: 없는 근거 세그먼트
- **WHEN** 400개 세그먼트 세션에서 `evidence_segments=[512]`로 제출한다
- **THEN** 실행은 끝나지 않고 유효 범위를 알려 주는 오류 관측이 돌아간다

### Requirement: LLM이 만든 숫자 카운트 제거
최종 판정에서 LLM이 넣은 인원 수 필드(`total_people`, `total`, `count`, `num_people`, `people_count`)는 제거해야 한다(MUST). 근거 세그먼트의 인원 수가 필요하면 시스템이 세션 관측값에서 직접 넣는다.

#### Scenario: 몰래 넣은 인원 수
- **WHEN** LLM이 판정에 `total_people=99`를 함께 제출한다
- **THEN** 저장된 판정에는 LLM 값 99가 없고, 근거 세그먼트별 인원 수는 세션 관측값과 같다

### Requirement: 권고는 실행하지 않음
`action` 값은 대응 권고 수준이며 시스템은 이를 근거로 외부 알림, 파일 변경, 네트워크 호출 같은 부수효과를 일으켜서는 안 된다(MUST). 출력은 터미널 표시와 실행 기록 파일뿐이다.

#### Scenario: alert 판정
- **WHEN** 최종 판정의 `action`이 `alert`다
- **THEN** 시스템은 판정을 표시하고 기록할 뿐 다른 동작을 하지 않는다

### Requirement: 궤적 기록
실행마다 새 출력 폴더에 질문, 모델 이름, 최대 단계 수, 단계별 LLM 응답·도구 호출·관측, 토큰 사용량, 최종 상태와 판정을 순서대로 JSONL로 남겨야 한다(SHALL). 기록은 각 단계가 끝날 때마다 즉시 써서 도중에 실패해도 그때까지의 단계가 남아야 한다(MUST).

#### Scenario: 도중 API 실패
- **WHEN** 4번째 LLM 호출이 재시도 후에도 실패한다
- **THEN** 기록에는 1–3단계가 남고 마지막 행은 최종 상태 `error`와 오류 메시지다

### Requirement: 일시적 API 실패 재시도
네트워크 오류, 속도 제한, 서버 오류에 한해 LLM 호출을 지수 백오프로 최대 3회 다시 보내야 한다(SHALL). 재시도는 단계 수에 포함하지 않는다.

#### Scenario: 한 번 속도 제한
- **WHEN** 첫 LLM 호출이 속도 제한 오류를 받고 두 번째 시도는 성공한다
- **THEN** 실행은 1단계로 이어지고 기록에 재시도 1회가 남는다
