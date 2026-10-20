# cong-agent

저장된 혼잡도 세션을 도구로 조회하고 판정하는 LLM 에이전트입니다. [OpenHands software-agent-sdk](https://github.com/OpenHands/software-agent-sdk) 위에 만들었습니다.

`congestion-llm-gating`은 규칙 트리거가 고른 구간마다 LLM을 한 번씩 부릅니다. 이 프로젝트는 그 판정 구조를 쓰지 않습니다. 에이전트가 관측값만 보고 볼 구간을 스스로 찾고, 여러 번 조회한 뒤 판정을 제출합니다. 영상·GPU·검출 모델은 쓰지 않고, 그 프로젝트가 남긴 세션 폴더(`session.json`, `results.jsonl`)의 perception 관측값만 읽습니다.

## 설치

Python 3.12 이상이 필요합니다.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
```

## 실행

`ANTHROPIC_API_KEY`가 필요합니다. 모델·최대 단계·system prompt는 `config/default.yaml`에 있습니다. 기본 모델은 `anthropic/claude-opus-5-5`(LiteLLM 형식)이고, 환경변수 `CONG_AGENT_MODEL`로 바꿀 수 있습니다.

```bash
.venv/bin/python -m cong_agent run \
  --session ../congestion-llm-gating/outputs/20260726_210025 \
  --question "이 세션에서 혼잡이 가장 심했던 구간과 권고 수준은?"
```

- `--config`(기본 `config/default.yaml`): 실행 설정 파일입니다.
- `--max-steps`: LLM 호출 횟수 상한입니다. 주면 설정 파일 값(15)을 덮어씁니다.
- `--output-dir`(기본 `trajectories`): 실행마다 `trajectories/<시각>/`이 생깁니다. `conversation/` 아래에는 SDK가 이벤트(LLM 응답, 도구 호출, 관측)를 하나씩 저장합니다. `run.json`에는 질문·모델·최종 상태·판정·토큰이 들어갑니다.
- 최종 상태는 다섯 가지입니다.

| 상태 | 뜻 |
|---|---|
| `submitted` | 판정을 제출하고 `finish`로 끝남 |
| `no_judgment` | 유효한 판정 없이 `finish`로 끝남 |
| `step_limit` | 최대 단계 수에 닿음 |
| `stuck` | 같은 호출·관측이 4번 반복돼 SDK가 멈춤 |
| `error` | API 실패 등 |

- 종료 코드는 `submitted`면 0, 다른 상태면 1, 세션이나 설정 파일을 읽지 못하면 2입니다.

## 도구 (에이전트-컴퓨터 인터페이스)

| 도구 | 하는 일 |
|---|---|
| `session_overview` | 세그먼트 수·길이·시간 범위, 구역, level별 개수, 인원·평균 속도 범위 |
| `view_segments(start, end)` | 범위의 관측값 표 (한 번에 최대 20행, 남은 범위 안내) |
| `find_segments(level, min_total, max_avg_speed, min_density_slope)` | 조건(AND)에 맞는 세그먼트 번호와 일치 개수 (번호는 최대 50개 표시) |
| `zone_trend(zone, start, end)` | 한 구역의 인원 최소·최대·평균과 최대 세그먼트 |
| `submit_judgment(...)` | 판정 제출. 검증을 통과하면 저장만 하고, 실행은 `finish`가 끝냅니다 |
| `think`, `finish` | SDK 기본 도구 (생각 정리, 실행 종료) |

판정 어휘는 `congestion-llm-gating`과 같습니다. `assessment`는 normal/caution/anomaly, `action`은 none/monitor/alert입니다. `action`은 권고일 뿐이며 시스템이 실행하지 않습니다.

## 지키는 경계

- LLM은 텍스트만 받습니다. 이미지 보기·터미널·파일 편집·브라우저 도구는 등록하지 않습니다.
- 세션에 기록된 기존 LLM 판정(`agent`), 원시 트랙(`tracks`), 처리 시간, 규칙 트리거 정보(`trigger`, `trigger_reason`, `co_triggered`, `dynamic_thresholds`)는 읽을 때 버립니다. 그래서 도구가 노출할 수 없습니다.
- 조회 도구는 관측값과 단순 집계만 돌려주고 판정을 만들지 않습니다.
- LLM이 판정에 넣은 인원 수 필드는 지웁니다. 근거 세그먼트의 인원 수(`evidence_totals`)는 코드가 세션 값으로 넣습니다. 단, `reasoning` 자유 텍스트 안의 숫자는 막지 못합니다.
- temperature를 지정하지 않으므로 같은 질문도 실행마다 결과가 다를 수 있습니다.

## 참고한 설계

- **OpenHands software-agent-sdk** (`openhands-sdk==1.56.0`): Agent·Tool(Action → Observation)·Conversation. 루프·재시도·이벤트 저장·반복 감지를 SDK에 맡깁니다.
- **congestion-llm-gating**: perception = observations, LLM = judgment. 숫자 카운트 필드 제거와 판정 어휘를 가져왔습니다. 규칙 트리거 + 1회 판정 구조는 쓰지 않습니다.
- **ddi-aci**: 도메인 규약은 도구 안에 담고, 에이전트에게는 해석이 끝난 결과만 줍니다.
- **SWE-agent**: 도구 수를 적게 하고, 출력은 짧고 일정하게 하며, 잘못된 입력에는 바로 고칠 수 있는 오류를 줍니다.

## 구조

OpenHands SDK·SWE-agent처럼 `src/` 없이 최상위에 패키지를 둡니다. 전체 구조와 규칙은 `.claude/rules/layout.md`에 있습니다.

```
cong_agent/
├── environment/session.py   세션 폴더 → Segment 목록 (판정 입력·트리거 차단)
├── tools/<도구 이름>/        도구마다 definition.py(스키마·등록) + impl.py(실행 로직)
├── tools/utils/             출력 형식, 입력 오류, 공용 도구 기반
├── agent/                   LLM·Agent 구성, 최종 상태 판정
└── run/run_single.py        설정·세션 적재 → 실행 → run.json, CLI
config/default.yaml          모델, 최대 단계, system prompt
tests/                       패키지 구조를 그대로 따라감
trajectories/                실행 기록 (git 제외)
```

## 남은 일

- 실제 API로 한 번 실행해 보기: 실제 세션에 질문 하나를 돌려 `submitted` 상태와 2단계 이상 진행을 확인하고, 단계 수·토큰을 여기에 기록한다.

개발 규칙은 `.claude/rules/`에 있습니다.
