# Design

## Context

- 빈 저장소다. 동기는 proposal.md의 Why를 본다.
- 입력은 `congestion-llm-gating` 세션 폴더다. `results.jsonl` 한 행은 `timestamp`, `perception`(total, density, avg_speed, zone_counts, zone_density, concentration, tracks, cv_elapsed_sec), `trigger`, `trigger_reason`, `co_triggered`, `aggregated`(density_delta_ratio, speed_trend, density_slope, level), `dynamic_thresholds`, `agent`(기존 LLM 판정 또는 null)로 이뤄진다. 확인한 세션 `20260726_210025`는 400행, 트리거 101행이다.
- 참고한 설계:
  - `congestion-llm-gating`: perception = observations, LLM = judgment. 이미지 금지, 숫자 카운트 필드 제거, action은 권고일 뿐.
  - `ddi-aci`: 도메인 규약을 도구 안에 담아 에이전트가 원자료를 해석하지 않게 한다. 결과적으로 턴 수와 토큰이 줄었다.
  - SWE-agent: ACI는 명령 수가 적고, 출력이 짧고 일정하며, 잘못된 입력에 즉시 알려 주는 오류를 준다. 파일 뷰어는 창 단위로 잘라 보여 준다.
  - OpenHands software-agent-sdk: Agent(LLM+도구 묶음) / Tool(Action 입력 → Observation 출력, 스키마 선언) / Conversation(이벤트 기록과 실행 루프)을 분리한다.
  - 외부 두 저장소는 이번에 코드를 다시 확인하지 않았다. 위 내용은 개념 수준 참고이며 API를 그대로 따르지 않는다.

## Goals / Non-Goals

**Goals:**
- 의존성 최소(anthropic SDK 하나)로 끝까지 한 번 도는 에이전트.
- 가짜 LLM으로 네트워크 없이 루프 전체를 테스트할 수 있는 구조.

**Non-Goals:**
- OpenHands·SWE-agent 패키지 사용, 샌드박스·컨테이너, 코드 실행(CodeAct).
- 프롬프트 튜닝, 정확도 평가, 여러 질문 일괄 실행.

## Decisions

1. **도구 호출 방식: LLM 네이티브 tool use.** ddi-aci는 CodeAct(IPython에서 파이썬 실행)를 썼다. 여기서는 도구가 전부 읽기 전용 조회라 코드 실행 샌드박스가 필요 없고, 네이티브 tool use가 인자 검증과 기록을 단순하게 만든다. 대안 CodeAct는 유연하지만 이미지 금지·카운트 금지 경계를 코드로 우회할 수 있어 제외.
2. **Tool = 스키마 + 순수 함수.** 각 도구는 이름, 설명, JSON 입력 스키마, `run(session, **args) -> str`을 가진다(OpenHands의 Action/Observation 분리를 단순화). 관측은 사람이 읽는 짧은 텍스트이고, 형식 규칙(최대 20행, 소수 둘째 자리, 잘림 안내)은 공용 포매터 한 곳에 둔다(SWE-agent의 창 보기). 도구는 registry dict에 명시적으로 등록한다.
3. **판정 제출도 도구다.** `submit_judgment`를 도구로 두면 "언제 끝내는가"가 LLM 응답 텍스트 파싱이 아니라 스키마 검증 문제가 된다(SWE-agent의 `submit`). 검증 실패는 오류 관측으로 돌려 스스로 고치게 한다.
4. **판정 입력 차단은 적재 단계에서.** 세션을 읽을 때 `agent`, `tracks`, `cv_elapsed_sec`를 아예 버린 `Segment` 데이터클래스로 바꾼다. 도구가 실수로 노출할 경로 자체를 없앤다(gating의 노출 레지스트리를 더 강하게 적용).
5. **LLM 경계는 작은 Protocol.** `LLMClient.complete(system, messages, tools) -> LLMResponse(text, tool_calls, usage)`. 구현은 `AnthropicClient`(기본 `claude-opus-5-5`, `CONG_AGENT_MODEL`로 변경)와 테스트용 `ScriptedClient` 둘. 재시도는 `AnthropicClient` 안에서만 한다(SDK 자체 재시도는 끈다). 현재 모델은 temperature를 받지 않고 thinking이 항상 켜져 있으므로, 응답 content 블록을 바꾸지 않고 그대로 대화 기록에 붙인다. 안전 분류기 거절(`stop_reason=refusal`)은 서버 측 `fallbacks: "default"`로 다른 모델이 이어받게 하고, 그래도 거절되면 재시도 없이 `error`로 끝낸다.
6. **Conversation = 메시지 목록 + 이벤트 기록.** 루프는 `step → tool 실행 → 관측 추가`를 반복하고, 매 단계 이벤트를 `outputs/<timestamp>/trajectory.jsonl`에 append한다. 최종 상태는 `submitted | step_limit | error`.
7. **패키지 구조**

   ```
   src/cong_agent/
   ├── session.py     세션 적재 → list[Segment]
   ├── tools/         registry, format, overview, view, find, zone, submit
   ├── llm.py         LLMClient Protocol, AnthropicClient, ScriptedClient
   ├── prompt.py      system prompt (도구 사용 원칙, 판정 어휘)
   ├── agent.py       루프, 단계 제한, 판정 후처리
   ├── trajectory.py  JSONL 기록
   └── __main__.py    CLI
   ```

## Risks / Trade-offs

- [트리거 정보가 판정을 끌고 감] 도구가 `trigger`를 보여 주므로 LLM이 트리거=이상으로 단순 추종할 수 있다 → 이번 범위에선 허용하고, `reasoning`에 트리거 외 근거를 쓰라고 프롬프트에 적는다.
- [reasoning 속 숫자 오류] 자유 텍스트의 틀린 인원 수는 막지 못한다 → gating과 같은 알려진 한계로 둔다. 구조화 필드만 방어한다.
- [질문이 모호] "가장 혼잡한 때"처럼 기준이 여러 개일 수 있다 → 프롬프트에 근거 세그먼트를 반드시 명시하게 해 사후 확인을 가능하게 한다.
- [모델 이름] `claude-opus-5-5`가 계정에서 안 열릴 수 있다 → 환경변수로 바꿀 수 있게 한다.
- [재현성] temperature를 고정할 수 없어 같은 질문도 실행마다 궤적이 달라질 수 있다 → 궤적 기록에 모델 이름을 남기고, 재현성은 주장하지 않는다.

## Open Questions

- 기본 최대 단계 수 15가 적당한지는 실제 실행 몇 번을 보고 조정한다.
