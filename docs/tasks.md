# 전체 구현 체크리스트

capability 의존 순서로 정리한다. `[x]`는 구현과 테스트가 있는 항목, `[ ]`는 남은 항목이다. 테스트 파일 표기는 관련 검증의 위치이며, 요구사항의 모든 경계 사례를 검사한다는 뜻은 아니다.

## 1. session-loading

- [x] 세션 폴더 적재와 연속 번호·구역 목록 제공 (근거: Session Folder Loading) — `tests/environment/test_session.py`
- [x] 세그먼트에서 판정·원시 데이터·트리거 필드 차단 (근거: Session Field Isolation) — `tests/environment/test_session.py`
- [x] 식별자·간격 누락 시 기본값 적용 (근거: Session Metadata Defaults) — `tests/environment/test_session.py`
- [x] 필수 파일 누락과 결과 행 오류 보고 (근거: Session Input Error Reporting) — `tests/environment/test_session.py`
- [x] 빈 줄 건너뛰기와 빈 세션 거부 (근거: Empty Session Rejection) — `tests/environment/test_session.py`

## 2. query-tools

- [x] 세션 전체 요약 제공 (근거: Session Overview Output) — `tests/tools/session_overview/test_session_overview.py`
- [x] 지정 구간의 관측 표 제공 (근거: Segment Observation Table) — `tests/tools/view_segments/test_view_segments.py`
- [x] 관측 수치·표·번호 목록 형식과 길이 제한 (근거: Query Output Bounds) — `tests/tools/utils/test_format.py`, `tests/tools/view_segments/test_view_segments.py`
- [x] 검색 조건을 AND로 결합하고 일치 개수·번호 제공 (근거: Segment Search Conditions) — `tests/tools/find_segments/test_find_segments.py`
- [x] 검색 결과 0개를 정상 응답으로 처리 (근거: Empty Search Result) — `tests/tools/find_segments/test_find_segments.py`
- [x] 구역 인원 통계와 최대 구간 제공 (근거: Zone Population Trend) — `tests/tools/zone_trend/test_zone_trend.py`
- [x] 조회 번호·범위·조건·구역 검증 (근거: Query Argument Validation) — `tests/tools/view_segments/test_view_segments.py`, `tests/tools/find_segments/test_find_segments.py`, `tests/tools/zone_trend/test_zone_trend.py`
- [x] ToolError를 오류 관측으로 변환 (근거: Query Error Observation) — `tests/tools/view_segments/test_view_segments.py`
- [x] 알 수 없는 조회 인자 거부와 생략 인자 제외 (근거: Query Schema Isolation) — `tests/tools/view_segments/test_view_segments.py`, `tests/tools/find_segments/test_find_segments.py`
- [x] 조회 출력·설명에서 판정과 트리거 비노출 확인 (근거: Query Judgment Isolation) — `tests/tools/test_no_leak.py`

## 3. judgment-submission

- [x] 제출 필수 필드·허용 값·근거 검증 (근거: Judgment Payload Validation) — `tests/tools/submit_judgment/test_submit_judgment.py`
- [x] 제출 인원 필드 제거와 evidence_totals 보정 (근거: Judgment Count Correction) — `tests/tools/submit_judgment/test_submit_judgment.py`
- [x] 마지막 유효 판정 저장과 실패 시 기존 판정 유지 (근거: Judgment Store Replacement) — `tests/tools/submit_judgment/test_submit_judgment.py`
- [x] 제출 결과를 관측으로 반환하고 종료 분리 (근거: Judgment Submission Observation) — `tests/tools/submit_judgment/test_submit_judgment.py`, `tests/run/test_run_single.py`

## 4. agent-run

- [x] Agent 도구를 조회 4개·제출·finish·think로 제한 (근거: Agent Tool Boundary) — `tests/agent/test_agent.py`
- [x] 설정 프롬프트 적용과 기본 도구 안내·트리거 비언급 (근거: Agent Prompt Configuration) — `tests/agent/test_agent.py`
- [x] 모델·API 키·재시도·usage_id로 LLM 구성 (근거: Agent Llm Configuration) — `tests/agent/test_agent.py`
- [x] 모델과 최대 단계의 설정 우선순위 적용 (근거: Run Configuration Precedence) — `tests/run/test_run_single.py`
- [x] 세션·설정 오류를 실행 전에 보고 (근거: Run Input Error Handling) — `tests/run/test_run_single.py`
- [x] 최종 상태 5종 판정 (근거: Run Final State Classification) — `tests/run/test_run_single.py`
- [x] 도구 오류 뒤 후속 호출과 제출 처리 (근거: Run Tool Error Recovery) — `tests/run/test_run_single.py`
- [x] LLM에 이미지 없이 텍스트 전달 (근거: Run Text Only Input) — `tests/run/test_run_single.py`
- [x] SDK 이벤트와 실행 요약 보존 (근거: Run Record Persistence) — `tests/run/test_run_single.py`
- [x] CLI 필수·선택 인자와 출력 폴더 처리 (근거: Run Cli Interface) — `tests/run/test_run_single.py`
- [x] CLI 상태·판정·종료 코드 출력 (근거: Run Cli Result Reporting) — `tests/run/test_run_single.py`
- [x] .env 적재 시 셸 환경변수 우선 유지 (근거: Run Environment Loading) — `tests/run/test_run_single.py`
