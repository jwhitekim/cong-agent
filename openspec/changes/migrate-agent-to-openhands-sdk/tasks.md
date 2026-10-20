# Tasks

## 1. 준비

- [x] 1.1 현재 첫 버전 코드와 OpenSpec 파일을 git 커밋으로 남기고 `git log --oneline`에 커밋이 보이는지 확인
- [x] 1.2 `add-congestion-agent-mvp`를 아카이브하고(남은 실제 실행 작업은 이 변경 5.3으로 이월) `openspec/specs/congestion-aci/spec.md`, `openspec/specs/agent-loop/spec.md`가 생기는지 확인
- [ ] 1.3 `pyproject.toml` 의존성을 `openhands-sdk==1.56.0`으로 바꾸고 `anthropic`을 빼서 재설치한 뒤 `python -c "import openhands.sdk"`가 성공하는지 확인

## 2. 트리거 제거

- [ ] 2.1 `session.py`의 `Segment`에서 `trigger`, `trigger_reason`, `co_triggered`를 빼고, 필드 목록 테스트에 세 이름을 추가해 통과 확인
- [ ] 2.2 `session_overview`에서 트리거 개수를 빼고 `level`별 개수 합·인원·평균 속도 범위를 보이게 바꾼 뒤 개요 테스트 통과 확인
- [ ] 2.3 `view_segments`에서 트리거 열과 트리거 근거를 빼고, fixture 전체 조회 출력에 트리거 이름·근거 문장이 없음을 확인하는 테스트 추가
- [ ] 2.4 `find_segments`에서 `trigger` 조건을 빼고 `max_avg_speed`, `min_density_slope`를 추가해 느린 구간 검색·조건 결합·일치 0개·조건 없음 오류·`trigger` 인자 거부를 테스트로 확인

## 3. OpenHands 도구 감싸기

- [ ] 3.1 `tools/openhands.py`에 도구별 `Action` 모델, 공용 텍스트 `Observation`, `run_tool`을 부르는 `Executor`(`ToolError` → `is_error=True` 관측)를 만들고, Executor를 직접 호출해 정상·오류 관측을 단위 테스트로 확인
- [ ] 3.2 `submit_judgment` Executor가 검증된 판정을 `JudgmentStore`에 저장하고(마지막 유효 제출 우선) 실패 시 저장하지 않는지 테스트로 확인
- [ ] 3.3 세션과 store를 받아 도구 인스턴스를 만들고 `register_tool`로 등록하는 함수를 만들고, `Agent`가 받는 도구 이름이 5개 도메인 도구 + `finish` + `think`뿐인지 테스트로 확인

## 4. 에이전트 실행

- [ ] 4.1 `prompt.py`를 트리거 언급 없이 다시 쓰고(관측값으로 이상 구간 찾기, 제출 후 `finish` 호출) 프롬프트에 7개 도구 이름이 모두 있는지, 트리거 이름이 없는지 테스트로 확인
- [ ] 4.2 `runner.py`에 `Agent`·`LLM`·`Conversation` 구성, 실행, 설계의 상태 대응표에 따른 최종 상태 판정, `run.json` 쓰기를 구현하고 `TestLLM`으로 `submitted`·`no_judgment`·`step_limit` 상태를 테스트로 확인
- [ ] 4.3 같은 호출 4회 반복 시 `stuck`, LLM 예외 시 `error`와 앞 단계 이벤트 보존을 `TestLLM` 테스트로 확인
- [ ] 4.4 `agent.py`, `llm.py`, `trajectory.py`와 `tests/test_agent.py`, `tests/test_llm.py`를 지우고 남은 테스트 전체가 통과하는지 확인

## 5. CLI와 실제 실행

- [ ] 5.1 `__main__.py`를 `runner.py`로 연결하고(옵션 그대로), `TestLLM` 주입으로 판정 출력과 `run.json` 생성, 잘못된 세션의 종료 코드 2를 테스트로 확인
- [ ] 5.2 `README.md`의 실행·구조·참고 설계 절을 OpenHands 기준으로 고치고, 적힌 설치·테스트 명령이 그대로 도는지 확인
- [ ] 5.3 API 키로 실제 세션(`../congestion-llm-gating/outputs/20260726_210025`)에 질문 하나를 실행해 `submitted` 상태와 2단계 이상 진행을 확인하고, 단계 수·토큰을 README에 한 줄로 기록
