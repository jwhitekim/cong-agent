# Tasks

## 1. 프로젝트 뼈대

- [x] 1.1 `pyproject.toml`(Python 3.11+, 의존성 `anthropic`, 개발 의존성 `pytest`), `src/cong_agent/` 패키지, `tests/`, `.gitignore`(`outputs/`, `.venv/`)를 만들고 `pip install -e .[dev]` 후 `python -c "import cong_agent"`가 성공하는지 확인
- [x] 1.2 `tests/fixtures/session_small/`에 세그먼트 30개짜리 합성 세션(트리거 surge/stagnation/hotspot 포함, 기존 `agent` 판정·`tracks` 포함)을 만들고 파일이 `session.json`·`results.jsonl` 형식과 같은지 실제 세션 첫 행과 키 비교로 확인

## 2. 세션 적재

- [x] 2.1 `session.py`에 세션 폴더 → `Segment` 목록 적재를 구현하고, `agent`/`tracks`/`cv_elapsed_sec`가 `Segment`에 없음을 단위 테스트로 확인
- [x] 2.2 파일 누락·깨진 JSONL 행에서 파일명과 행 번호가 담긴 오류가 나는지 단위 테스트로 확인
- [x] 2.3 실제 세션 `../congestion-llm-gating/outputs/20260726_210025`를 적재해 세그먼트 400개, 트리거 101개가 나오는지 확인(폴더가 없으면 건너뛰는 테스트)

## 3. 혼잡도 도구(ACI)

- [x] 3.1 `tools/__init__.py` registry(이름→도구, 입력 스키마 목록 내보내기)와 `tools/format.py`(20행 창, 소수 둘째 자리, 잘림 안내)를 구현하고 포매터 단위 테스트 통과 확인
- [x] 3.2 `session_overview` 도구를 구현하고 트리거별 개수 합이 트리거 세그먼트 수와 같은지 테스트로 확인
- [x] 3.3 `view_segments` 도구를 구현하고 20행 초과 잘림·범위 밖 오류 시나리오를 테스트로 확인
- [x] 3.4 `find_segments` 도구를 구현하고 트리거 검색, 일치 0개, 50개 초과 목록 잘림을 테스트로 확인
- [x] 3.5 `zone_trend` 도구를 구현하고 최솟값·최댓값·평균·최댓값 세그먼트와 없는 구역 오류를 테스트로 확인
- [x] 3.6 모든 조회 도구 출력에 판정 어휘(normal/caution/anomaly/monitor/alert)와 기존 `reasoning` 문장이 나오지 않는지 fixture 전체를 훑는 테스트로 확인

## 4. 에이전트 루프

- [x] 4.1 `llm.py`에 `LLMClient` Protocol, `ScriptedClient`(미리 정한 응답 순서대로 반환), `AnthropicClient`(tool use 변환, 일시적 오류만 지수 백오프 3회)를 구현하고, 가짜 예외로 재시도 횟수와 비재시도 오류 즉시 실패를 테스트로 확인
- [x] 4.2 `submit_judgment` 도구와 판정 검증(허용 값, 근거 세그먼트 범위, 숫자 카운트 필드 제거, 근거 세그먼트 인원 수를 세션 값으로 주입)을 구현하고 spec의 판정 시나리오 4개를 테스트로 확인
- [x] 4.3 `prompt.py`에 system prompt(도구로만 사실 확인, 근거 세그먼트 명시, 트리거 외 근거도 서술, action은 권고)를 작성하고 프롬프트에 도구 이름이 모두 들어 있는지 테스트로 확인
- [x] 4.4 `trajectory.py`에 단계별 즉시 append 기록을 구현하고, 기록 도중 예외가 나도 앞 단계가 파일에 남는지 테스트로 확인
- [x] 4.5 `agent.py`에 루프(도구 실행, 없는 도구·잘못된 인자 오류 관측, 단계 제한 15, 최종 상태 submitted/step_limit/error)를 구현하고 `ScriptedClient`로 세 가지 최종 상태를 모두 테스트로 확인

## 5. CLI와 실제 실행

- [x] 5.1 `__main__.py`에 `run --session --question [--max-steps] [--out]` CLI를 구현하고, 결과 판정을 터미널에 출력하는지 `ScriptedClient` 주입 테스트로 확인
- [x] 5.2 `README.md`에 설치·실행 방법, 도구 목록, 참고 설계(congestion-llm-gating, ddi-aci, SWE-agent, OpenHands SDK)와의 관계를 쓰고 적힌 명령이 그대로 도는지 확인
- [ ] 5.3 `ANTHROPIC_API_KEY`로 실제 세션에 질문 하나("이 세션에서 혼잡이 가장 심했던 구간과 권고 수준은?")를 실행해 `submitted` 상태와 `trajectory.jsonl`이 생기는지 확인하고, 단계 수·토큰을 README에 한 줄로 기록
