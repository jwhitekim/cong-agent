# 검증

바꾼 곳에 따라 아래를 돌린다. 마지막에는 항상 전체(`.venv/bin/pytest -q`)를 돌린다. 통과하면 로컬 커밋까지 하고, 원격 푸시는 사람 확인을 받는다.

| 바꾼 곳 | 검증 |
|---|---|
| 폴더·파일 이름, 경로 | `pytest tests/test_layout.py` |
| `cong_agent/environment/` | `pytest tests/environment` |
| `cong_agent/tools/<도구>/` | `pytest tests/tools/<도구>`, 그다음 `pytest tests/tools` |
| `cong_agent/agent/`, `run/`, `config/` | `pytest tests/agent tests/run` |

## 테스트 작성 규칙

- 네트워크 없이 돌린다. LLM은 `openhands.sdk.testing.TestLLM.from_messages([...])`로 대신하고, 실제 `Conversation`을 돌린다. 도구 호출 응답을 만드는 도우미(`call(name, args)`, `FINISH`)는 `tests/conftest.py`에 한 벌만 둔다.
- 최종 상태 5가지(`submitted`, `no_judgment`, `step_limit`, `stuck`, `error`)는 각각 테스트가 있어야 한다. 단계 초과 테스트는 서로 다른 호출을 써서 반복 감지에 먼저 걸리지 않게 한다.
- 실행 기록은 이벤트 파일을 JSON으로 읽어 확인한다. 문자열 일부 일치로 확인하지 않는다.
- 픽스처 `tests/fixtures/session_small/`은 30세그먼트 합성 세션이다. 실제 세션과 키 구성이 같고, 차단 확인용으로 기존 판정(`LEAK_` 문구)·트랙·트리거를 일부러 담고 있다. 이 필드들을 지우지 않는다.
- 조회 도구 출력과 설명에 판정 어휘·`LEAK_` 문구·트리거 이름·트리거 근거가 없는지 fixture 전체를 훑는 테스트(`tests/tools/test_no_leak.py`)를 유지한다. 도구를 추가하면 여기에도 넣는다.
- 실제 세션 테스트는 `../congestion-llm-gating/outputs/20260726_210025`가 없으면 건너뛴다.
- 실제 API 실행은 자동 테스트에 넣지 않는다. 비용이 들고 결과가 실행마다 다르다.
