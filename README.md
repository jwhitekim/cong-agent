# cong-agent

저장된 혼잡도 세션을 도구로 조회하고 판정하는 LLM 에이전트입니다. 처음 만들어 본 최소 버전입니다.

`congestion-llm-gating`은 규칙이 고른 구간마다 LLM을 한 번씩만 부릅니다. 이 프로젝트에서는 LLM이 도구를 골라 여러 번 조회한 뒤 판정을 제출합니다. 영상·GPU·검출 모델은 쓰지 않고, 그 프로젝트가 남긴 세션 폴더(`session.json`, `results.jsonl`)만 읽습니다.

## 설치

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
```

## 실행

`ANTHROPIC_API_KEY`가 필요합니다. 기본 모델은 `claude-opus-5-5`이고 `CONG_AGENT_MODEL`로 바꿀 수 있습니다.

```bash
.venv/bin/python -m cong_agent run \
  --session ../congestion-llm-gating/outputs/20260726_210025 \
  --question "이 세션에서 혼잡이 가장 심했던 구간과 권고 수준은?"
```

- `--max-steps`(기본 15): LLM 호출 횟수 상한. 넘으면 판정 없이 `step_limit`으로 끝납니다.
- `--out`(기본 `outputs`): 실행마다 `outputs/<시각>/trajectory.jsonl`이 생깁니다. 여기에는 질문·모델·단계별 도구 호출과 관측·토큰·최종 판정이 순서대로 남습니다.
- 종료 코드는 판정 제출이면 0, 단계 초과나 오류면 1, 세션을 읽지 못하면 2입니다.

## 도구 (에이전트-컴퓨터 인터페이스)

| 도구 | 하는 일 |
|---|---|
| `session_overview` | 세그먼트 수·길이·시간 범위, 구역, 트리거별·혼잡 등급별 개수 |
| `view_segments(start, end)` | 범위의 관측값 표 (한 번에 최대 20행, 남은 범위 안내) |
| `find_segments(trigger, level, min_total)` | 조건에 맞는 세그먼트 번호와 일치 개수 (번호는 최대 50개 표시) |
| `zone_trend(zone, start, end)` | 한 구역의 인원 최소·최대·평균과 최대 세그먼트 |
| `submit_judgment(...)` | 최종 판정 제출. 실행이 끝납니다 |

판정 어휘는 `congestion-llm-gating`과 같습니다. `assessment`는 normal/caution/anomaly, `action`은 none/monitor/alert입니다. `action`은 권고일 뿐이며 시스템이 실행하지 않습니다.

## 지키는 경계

- LLM은 텍스트만 받습니다. 이미지나 픽셀은 보내지 않습니다.
- 세션에 기록된 기존 LLM 판정(`agent`), 원시 트랙(`tracks`), 처리 시간은 읽을 때 버립니다. 그래서 도구가 노출할 수 없습니다.
- 조회 도구는 관측값과 단순 집계만 돌려주고 판정을 만들지 않습니다.
- LLM이 판정에 넣은 인원 수 필드는 지웁니다. 근거 세그먼트의 인원 수(`evidence_totals`)는 코드가 세션 값으로 넣습니다. 단, `reasoning` 자유 텍스트 안의 숫자는 막지 못합니다.

## 참고한 설계

- **congestion-llm-gating**: perception = observations, LLM = judgment. 숫자 카운트 필드 제거와 판정 어휘를 가져왔습니다.
- **ddi-aci**: 도메인 규약은 도구 안에 담고, 에이전트에게는 해석이 끝난 결과만 줍니다.
- **SWE-agent**: 도구 수를 적게 하고, 출력은 짧고 일정하게 하며, 잘못된 입력에는 바로 고칠 수 있는 오류를 줍니다. 판정 제출도 도구로 둡니다.
- **OpenHands software-agent-sdk**: LLM·도구·대화 기록(이벤트)을 분리하는 구조를 단순화해 따랐습니다. 두 외부 저장소의 패키지는 쓰지 않습니다.

## 구조

```
src/cong_agent/
├── session.py     세션 폴더 → Segment 목록 (판정 입력 차단)
├── tools/         조회 도구 4개 + submit_judgment, 출력 형식 규칙
├── llm.py         LLMClient Protocol, AnthropicClient, 테스트용 ScriptedClient
├── prompt.py      system prompt
├── agent.py       에이전트 루프 (단계 제한, 오류 관측, 최종 상태)
├── trajectory.py  궤적 JSONL 기록
└── __main__.py    CLI
```
