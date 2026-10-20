# Design

## Context

- 동기는 proposal.md의 Why를 본다.
- 현재 코드(`add-congestion-agent-mvp` 구현, 자동 테스트 40개 통과): `session.py`(적재·판정 입력 차단), `tools/`(조회 4개 + `submit_judgment`, 순수 함수 `run(session, **args) -> str`, 입력 오류는 `ToolError`), `agent.py`·`llm.py`·`trajectory.py`(자체 루프·Anthropic 클라이언트·JSONL 기록), `__main__.py`(CLI).
- `openhands-sdk` 1.56.0 소스를 직접 확인한 사실:
  - 도구는 `ToolDefinition[ActionT, ObservationT]` 하위 클래스다. `Action`/`Observation`은 pydantic 모델이고, 실행은 `ToolExecutor.__call__(action, conversation)`가 한다. `Observation.from_text(text, is_error=...)`로 오류 관측을 만든다. 도구는 `register_tool(name, factory)`로 등록하고 `Agent(tools=[Tool(name=...)])`로 고른다. factory에는 클래스 대신 인스턴스도 넘길 수 있다.
  - `Agent`의 기본 도구는 `FinishTool`과 `ThinkTool`이다(`include_default_tools`로 조정).
  - 실행은 이름이 `finish`인 도구 호출이 있을 때만 `FINISHED`가 된다(`agent.py`의 `_truncate_at_finish`). `finish` 뒤에 온 같은 응답 속 호출은 버린다.
  - `Conversation(agent, workspace, persistence_dir, max_iteration_per_run, stuck_detection, ...)`. 반복 상한에 닿으면 `ERROR`, 반복 감지(같은 action-observation 4회)는 `STUCK`이다.
  - `LLM(model, api_key, num_retries=5, temperature=None, ...)`이고 LiteLLM을 거친다. `temperature` 기본값 None은 값을 보내지 않는다는 뜻이다.
  - 테스트용 `openhands.sdk.testing.TestLLM.from_messages([...])`가 있다. 미리 정한 응답을 순서대로 돌려준다.

## Goals / Non-Goals

**Goals:**
- 루프·재시도·이벤트 저장·반복 감지를 SDK에 맡기고, 우리 코드는 도메인 도구와 상태 판정만 갖는다.
- 기존 도구 로직과 테스트는 최대한 그대로 살린다.

**Non-Goals:**
- `openhands-tools` 패키지(터미널, 파일 편집, 브라우저), 원격 작업 공간, 에이전트 서버.
- SDK의 critic, condenser(문맥 압축), 보안 확인 모드.

## Decisions

1. **도구 로직은 그대로, 감싸는 층만 추가.** `tools/query.py`, `tools/submit.py`의 순수 함수는 유지하고, 새 `tools/openhands.py`가 도구마다 `Action` 모델(인자 스키마), 공용 `TextObservation`, `Executor`를 만든다. Executor는 `run_tool(session, name, args)`을 부르고, `ToolError`를 `Observation.from_text(..., is_error=True)`로 바꾼다. 대안은 도구를 처음부터 SDK 클래스로 다시 쓰는 것인데, 테스트를 다시 써야 해서 제외한다.
2. **세션은 Executor 인스턴스가 쥔다.** 실행마다 세션을 적재한 뒤 도구 인스턴스를 만들어 `register_tool(name, instance)`로 등록한다. SDK registry는 프로세스 전역이므로, 같은 프로세스에서 세션을 바꿔 돌리면 다시 등록해 덮어쓴다. 대안 `conv_state`에서 세션 경로를 읽는 방식은 작업 공간 개념을 끌어들여 제외한다.
3. **제출과 종료 분리.** `finish`만 실행을 끝낼 수 있으므로 `submit_judgment`를 `finish`로 이름 바꿔 덮어쓰는 방법도 있다. 하지만 그러면 검증에 실패한 제출도 실행을 끝내 버린다. 그래서 `submit_judgment`는 검증한 판정을 `JudgmentStore`(Executor가 가진 단순 객체)에 저장만 하고, 종료는 내장 `finish`가 맡는다. 프롬프트에 "제출이 받아들여지면 finish를 호출"이라고 적는다.
4. **최종 상태 대응.**

   | 대화 상태 | 저장된 판정 | 최종 상태 |
   |---|---|---|
   | FINISHED | 있음 | `submitted` |
   | FINISHED | 없음 | `no_judgment` |
   | STUCK | 상관없음 | `stuck` |
   | ERROR, 반복 상한 도달 | 상관없음 | `step_limit` |
   | ERROR, 그 외 / 예외 | 상관없음 | `error` |

   반복 상한 도달 여부는 SDK가 남기는 `ConversationErrorEvent`의 `code == "MaxIterationsReached"`로 판단한다. 사람이 읽는 메시지 문구와 달리 코드는 식별자라 버전이 바뀌어도 덜 흔들린다. (처음에는 LLM 응답 수를 세려 했으나, 구현 중 SDK 소스에서 이 코드를 확인해 바꿨다.)
5. **트리거 차단은 적재 단계에서.** `Segment`에서 `trigger`, `trigger_reason`, `co_triggered`를 뺀다. 검색 도구는 `trigger` 조건을 버리고 `max_avg_speed`, `min_density_slope`를 받는다. `level`은 perception 쪽 집계값이라 남긴다.
6. **LLM 설정.** `LLM(model="anthropic/claude-opus-5-5", api_key=ANTHROPIC_API_KEY, num_retries=3)`. 모델은 `CONG_AGENT_MODEL`로 바꿀 수 있다. temperature는 지정하지 않는다. 첫 버전에 있던 서버 측 대체 모델(fallback) 설정은 LiteLLM 경유로 넘기는 방법을 확인하지 못해 이번에는 뺀다.
7. **실행 기록.** `outputs/<시각>/` 아래 `persistence_dir`에 SDK가 이벤트를 저장하고, 실행 뒤 `run.json`을 우리가 쓴다. 토큰 사용량은 대화 통계(`conversation.conversation_stats`)에서 읽는다.
8. **테스트.** `TestLLM`에 도구 호출이 담긴 응답을 넣어 실제 `Conversation`을 돌린다. 네트워크 없이 다섯 가지 최종 상태를 모두 확인한다.

## Risks / Trade-offs

- [LiteLLM이 새 모델 이름을 모름] `anthropic/claude-opus-5-5`가 SDK에 묶인 LiteLLM 버전에서 거부될 수 있다 → 실제 실행 작업에서 먼저 확인하고, 안 되면 모델 이름을 환경변수로 바꿔 돌린다.
- [thinking 블록 왕복] 현재 Claude 모델은 thinking 블록을 바꾸지 않고 되돌려 받아야 한다. SDK가 이를 처리하는지는 소스로 확인하지 못했다 → 실제 실행에서 2단계 이상이 400 없이 도는지 본다.
- [SDK 업데이트로 깨짐] 이 SDK는 버전이 자주 오른다(1.0 → 1.56) → `==1.56.0`으로 고정한다.
- [trigger 제거로 탐색 단계 증가] 에이전트가 이상 구간을 직접 찾아야 해서 단계와 토큰이 늘 수 있다 → 기본 최대 단계 15는 유지하고, 실제 실행 결과를 README에 남겨 조정 근거로 삼는다.
- [registry 전역 상태] 테스트끼리 도구 등록이 섞일 수 있다 → 실행마다 다시 등록하고, 테스트는 세션별로 새로 등록한다.

## Migration Plan

1. `add-congestion-agent-mvp`를 아카이브해 `openspec/specs/`에 본 명세를 만든다. 남은 실제 실행 작업은 이 변경으로 넘긴다.
2. 이 변경을 적용한다. 되돌릴 때는 git으로 이전 커밋에 돌아간다. 아직 커밋이 없으므로 적용 전에 첫 버전을 커밋해 둔다.
