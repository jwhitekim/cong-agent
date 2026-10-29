# agent-run spec

Agent·LLM 구성, 설정, 실행 상태, 기록과 CLI를 정의한다.
의존 capability: session-loading, query-tools, judgment-submission.

### Requirement: Agent Tool Boundary
Agent 구성기는 SHALL 조회 도구 4개와 `submit_judgment`를 등록하고 SDK 기본 도구를 `finish`, `think`로 제한하여 이 7개 도구만 제공한다.

#### Scenario: 실제 대화의 도구 구성
- GIVEN 적재된 세션과 Agent
- WHEN 대화를 처음 실행해 도구가 초기화된다
- THEN 도구 목록은 session_overview·view_segments·find_segments·zone_trend·submit_judgment·finish·think와 정확히 일치한다

### Requirement: Agent Prompt Configuration
Agent 구성기는 SHALL 설정의 `system_prompt`로 SDK 기본 프롬프트를 대체하고, 기본 설정 프롬프트는 도구 7개를 모두 안내하며 트리거 이름과 정보를 언급하지 않는다.

#### Scenario: 기본 프롬프트 확인
- GIVEN `config/default.yaml`에서 읽은 프롬프트
- WHEN 도구 이름과 트리거 관련 표현을 확인한다
- THEN 도구 7개 이름이 모두 있고 trigger·트리거·surge·stagnation·hotspot·conflict는 없다

### Requirement: Agent Llm Configuration
LLM 구성기는 SHALL 지정 모델에 재시도 횟수 3과 usage_id `cong-agent`를 적용하고, 환경변수 `ANTHROPIC_API_KEY`가 있으면 API 키로 전달하며 temperature를 명시하지 않는다.

#### Scenario: API 키가 있는 LLM 구성
- GIVEN 모델 이름과 `ANTHROPIC_API_KEY` 환경변수
- WHEN LLM을 구성한다
- THEN 지정 모델·API 키·재시도 횟수 3·usage_id가 설정된다

### Requirement: Run Configuration Precedence
설정 로더는 SHALL `agent.model`, `agent.max_steps`, `agent.system_prompt`를 읽고 모델에 명시적 함수 인자 > `CONG_AGENT_MODEL` > 파일 순서를 적용하며, 최대 단계에는 None이 아닌 함수 인자 > 파일 순서를 적용한다.

#### Scenario: 기본 설정
- GIVEN 기본 설정 파일과 모델 덮어쓰기가 없는 환경
- WHEN 설정을 적재한다
- THEN 모델은 `anthropic/claude-opus-5-5`이고 최대 단계는 15이다

#### Scenario: 모델과 단계 덮어쓰기
- GIVEN 모델 환경변수가 설정된 상태
- WHEN 모델 함수 인자 `x/arg`와 최대 단계 3을 지정해 설정을 적재한다
- THEN 모델은 `x/arg`이고 최대 단계는 3이다

#### Scenario: 함수 단계 인자 0
- GIVEN 유효한 설정 파일
- WHEN 설정 로더에 최대 단계 0을 직접 전달한다
- THEN 설정값 0을 그대로 반환한다

### Requirement: Run Input Error Handling
설정 로더는 SHALL 파일 읽기·YAML 해석·필수 키·형 변환 오류를 `ConfigError`로 알리고, CLI는 `ConfigError` 또는 `SessionError` 발생 시 대화 실행 전에 입력 오류를 표준 오류로 출력하고 종료 코드 2를 반환한다.

#### Scenario: 설정 필수 키 누락
- GIVEN max_steps가 없는 설정 파일
- WHEN 설정을 적재한다
- THEN max_steps를 명시한 `ConfigError`가 발생한다

#### Scenario: 세션 입력 오류
- GIVEN 필수 세션 파일이 없는 폴더
- WHEN CLI로 실행한다
- THEN 파일 이름을 담은 입력 오류가 출력되고 종료 코드는 2이다

### Requirement: Run Final State Classification
실행기는 SHALL SDK의 FINISHED와 저장 판정 유무를 submitted·no_judgment로, STUCK을 stuck으로, 그 밖의 종료에서 마지막 대화 오류 코드가 `MaxIterationsReached`이면 step_limit으로, 나머지 오류 종료와 대화 전송·실행 예외를 error로 분류한다.

#### Scenario: 판정 제출 후 정상 종료
- GIVEN 유효한 판정을 저장한 대화
- WHEN finish로 종료한다
- THEN 최종 상태는 submitted이다

#### Scenario: 유효 판정 없이 종료
- GIVEN 제출이 없거나 첫 제출의 검증이 실패한 대화
- WHEN finish로 종료한다
- THEN 최종 상태는 no_judgment이다

#### Scenario: 단계 한도 초과
- GIVEN 최대 단계 5와 서로 다른 조회 호출이 이어지는 대화
- WHEN SDK가 `MaxIterationsReached` 오류를 기록한다
- THEN 최종 상태는 step_limit이다

#### Scenario: 반복 호출로 정체
- GIVEN 같은 session_overview 호출과 관측이 반복되는 대화
- WHEN SDK가 STUCK으로 종료한다
- THEN 최종 상태는 stuck이다

#### Scenario: 실행 중 LLM 오류
- GIVEN 조회 이벤트가 이미 저장된 대화
- WHEN LLM 호출이 예외로 실패한다
- THEN 최종 상태는 error이며 오류 설명과 앞선 이벤트가 보존된다

### Requirement: Run Tool Error Recovery
실행기는 SHALL 존재하지 않는 도구나 잘못된 조회 인자를 오류 관측으로 받은 뒤에도 대화를 계속해 후속 제출과 종료를 처리한다.

#### Scenario: 오류 뒤 판정 제출
- GIVEN 없는 도구 호출과 범위를 벗어난 조회를 차례로 반환하는 LLM
- WHEN 이후 유효한 submit_judgment와 finish를 호출한다
- THEN 오류 관측을 남기고 최종 상태는 submitted이다

### Requirement: Run Text Only Input
실행기는 SHALL 세션 관측과 질문을 텍스트로 처리하며 LLM 대화에 이미지 콘텐츠를 추가하지 않는다.

#### Scenario: 조회와 제출 대화
- GIVEN 세션 조회·판정 제출·finish를 수행하는 대화
- WHEN 저장된 대화 이벤트의 콘텐츠 유형을 확인한다
- THEN text가 있고 image는 없다

### Requirement: Run Record Persistence
실행기는 SHALL 실행 폴더의 `conversation/<id>/events/event-*.json`에 SDK 이벤트를 보존하고 `run.json`에 질문, 세션 경로와 식별자, 설정 경로, 모델, 최대 단계, 최종 상태, 판정, 오류, 입력·출력 토큰 집계와 실행 폴더를 기록한다.

#### Scenario: 성공 실행 기록
- GIVEN 조회·유효 제출·finish로 종료하는 실행
- WHEN 실행 결과 파일을 읽는다
- THEN run.json의 상태·질문·모델·설정·단계가 실행값과 일치하고 각 도구 호출 이벤트가 순서대로 남는다

### Requirement: Run Cli Interface
CLI는 SHALL `python -m cong_agent run`에서 `--session`, `--question`을 필수로 받고 `--config`, `--max-steps`, `--output-dir`을 선택적으로 받으며, 최대 단계는 1 이상의 정수만 허용하고 기본 출력 폴더 `trajectories/` 또는 지정 폴더 아래 시각별 실행 폴더를 만든다.

#### Scenario: 최대 단계 인자 거부
- GIVEN CLI 실행 인자
- WHEN `--max-steps`에 0·음수·소수·숫자가 아닌 값을 전달한다
- THEN 인자 해석 오류로 종료 코드 2가 발생한다

#### Scenario: 출력 위치 지정
- GIVEN 유효한 세션과 지정 출력 폴더
- WHEN `--output-dir`을 지정해 유효 제출과 finish를 실행한다
- THEN 지정 폴더 아래 실행별 하위 폴더에 run.json이 생긴다

### Requirement: Run Cli Result Reporting
CLI는 SHALL 실행 뒤 상태·입력 및 출력 토큰·기록 위치를 출력하고 판정이 있으면 JSON을, 오류가 있으면 표준 오류를 출력하며, submitted이면 종료 코드 0을, 나머지 실행 상태이면 1을 반환한다.

#### Scenario: 판정 출력과 성공 코드
- GIVEN 유효 제출 후 finish로 끝나는 대화
- WHEN CLI로 실행한다
- THEN submitted 상태와 판정 JSON이 출력되고 종료 코드는 0이다

#### Scenario: 판정 없는 실행의 종료 코드
- GIVEN 유효 제출 없이 finish로 끝나는 대화
- WHEN CLI로 실행한다
- THEN no_judgment 상태가 출력되고 종료 코드는 1이다

### Requirement: Run Environment Loading
CLI는 SHALL 저장소 루트의 `.env`를 읽되 이미 존재하는 셸 환경변수를 덮어쓰지 않는다.

#### Scenario: 셸 환경변수 우선
- GIVEN 셸과 `.env`에 같은 이름의 환경변수가 서로 다른 값으로 정의된 상태
- WHEN CLI가 환경을 적재한다
- THEN 셸에 있던 값이 유지된다
