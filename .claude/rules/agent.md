---
paths:
  - "cong_agent/agent/**"
  - "cong_agent/run/**"
  - "cong_agent/__main__.py"
  - "cong_agent/tools/__init__.py"
  - "config/**"
  - "tests/agent/**"
  - "tests/run/**"
  - "pyproject.toml"
---

# 에이전트 구성과 실행

`openhands-sdk==1.56.0`으로 고정한다. 버전을 올리면 아래 SDK 동작이 그대로인지 소스로 다시 확인한다.

## 루프는 SDK에 맡긴다

- 루프·LLM 재시도·이벤트 저장·반복 감지는 직접 만들지 않는다. 우리 코드는 구성(`agent/agent.py`), 최종 상태 판정(`agent/status.py`), 실행과 `run.json` 쓰기(`run/run_single.py`)만 한다.
- `LLM(model=..., num_retries=3)`. 현재 모델은 temperature를 받지 않으므로 지정하지 않는다. API 키는 `ANTHROPIC_API_KEY`에서 읽는다.
- Agent의 기본 도구는 `FinishTool`, `ThinkTool`만 켠다.

## 설정 (`config/default.yaml`)

- 키: `agent.model`(기본 `anthropic/claude-opus-5-5`), `agent.max_steps`(기본 15), `agent.system_prompt`.
- `system_prompt`는 SDK 기본(코딩용) 프롬프트를 대신한다. 트리거를 언급하지 않는다. 도구 이름 7개(조회 4, `submit_judgment`, `finish`, `think`)를 모두 적는다.
- 덮어쓰기 순서: CLI 옵션 > 환경변수 `CONG_AGENT_MODEL` > 설정 파일.

## 종료와 최종 상태

- SDK는 이름이 `finish`인 도구 호출로만 실행을 끝낸다. `submit_judgment`는 저장만 하고, 프롬프트와 관측으로 `finish` 호출을 안내한다. `submit_judgment`를 `finish`로 바꾸지 않는다. 그러면 검증에 실패한 제출도 실행을 끝낸다.

| 대화 상태 | 저장된 판정 | 최종 상태 |
|---|---|---|
| FINISHED | 있음 | `submitted` |
| FINISHED | 없음 | `no_judgment` |
| STUCK (같은 호출·관측 4회) | - | `stuck` |
| ERROR, `ConversationErrorEvent.code == "MaxIterationsReached"` | - | `step_limit` |
| 그 외 ERROR, `run()` 예외 | - | `error` |

- 단계 초과는 사람이 읽는 메시지가 아니라 오류 코드로 판단한다.

## 실행 기록

- 실행마다 `trajectories/<시각>/`을 만든다. SDK 이벤트는 `conversation/<id>/events/event-*.json`에 하나씩 저장된다.
- `Conversation(delete_on_close=False)`를 유지한다. 기본값 True는 기록을 지운다.
- `visualizer=None`으로 터미널 출력을 끈다.
- `run.json`에는 질문, 세션 경로, 설정 파일 경로, 모델, 최대 단계, 최종 상태, 판정, 오류, 토큰(`conversation_stats`)을 쓴다.

## SDK registry

- `register_tool`은 프로세스 전역이다. 실행마다 세션을 쥔 도구 인스턴스를 다시 등록해 덮어쓴다.
- Agent의 도구는 첫 `run()` 때 초기화된다. `tools_map`은 그 뒤에만 읽을 수 있다.

## CLI

- `python -m cong_agent run --session <dir> --question "<질문>" [--config config/default.yaml] [--max-steps N] [--output-dir trajectories]`.
- 종료 코드: `submitted` 0, 다른 상태 1, 세션·설정 오류 2.
