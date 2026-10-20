# 저장소 구조

`src/` 없이 최상위에 패키지 `cong_agent/`를 둔다(OpenHands SDK, SWE-agent와 같은 방식).

```
cong-agent/
├── cong_agent/
│   ├── __main__.py            python -m cong_agent run ... → run/run_single.py
│   ├── environment/
│   │   └── session.py         세션 폴더 → Segment 목록 (숨길 필드 차단)
│   ├── tools/
│   │   ├── __init__.py        공개 목록: TOOL_CLASSES, register_tools
│   │   ├── utils/             format.py(출력 형식), errors.py(ToolError·번호 검사),
│   │   │                      base.py(공용 Observation·Executor·조회 도구 기반)
│   │   ├── session_overview/  __init__.py, definition.py, impl.py
│   │   ├── view_segments/
│   │   ├── find_segments/
│   │   ├── zone_trend/
│   │   └── submit_judgment/
│   ├── agent/
│   │   ├── agent.py           LLM·Agent 구성
│   │   └── status.py          실행 결과(RunResult)와 최종 상태 판정
│   └── run/
│       └── run_single.py      설정·세션 적재 → Conversation 실행 → run.json, CLI
├── config/
│   └── default.yaml           모델, 최대 단계, system prompt
├── tests/                     패키지 구조를 그대로 따라간다
│   ├── conftest.py
│   ├── fixtures/session_small/
│   ├── test_layout.py         이 문서의 구조와 실제 폴더가 같은지
│   ├── environment/
│   ├── tools/<도구 이름>/
│   ├── agent/
│   └── run/
├── trajectories/              실행 기록 (git 제외)
├── .dockerignore
├── .gitignore
├── pyproject.toml
└── README.md
```

## 규칙

- 도구 하나 = `cong_agent/tools/` 아래 폴더 하나. 폴더 이름이 곧 LLM이 보는 도구 이름이다.
- 각 도구 폴더는 `definition.py`(Action 스키마, 설명, ToolDefinition 클래스·`create`)와 `impl.py`(실행 로직)로 나눈다. 조회 도구는 `tools/utils/base.py`의 공용 `QueryTool`·`QueryExecutor`를 쓰고, 자기 Executor가 필요한 도구(`submit_judgment`)만 `impl.py`에 둔다. 여러 도구가 쓰는 코드는 `tools/utils/`에 둔다.
- 테스트는 패키지 경로를 따라간다. `cong_agent/tools/view_segments/`의 테스트는 `tests/tools/view_segments/`에 둔다.
- 실행 기록은 `trajectories/<시각>/`에 쓴다. 다른 곳(`outputs/` 등)에 쓰지 않는다.
- 프롬프트·모델·최대 단계 같은 실행 설정은 코드가 아니라 `config/*.yaml`에 둔다.
- 폴더를 추가·이동하면 이 문서와 `tests/test_layout.py`를 함께 고친다.
- `congestion-llm-gating`, OpenHands SDK 소스는 고치지 않는다.
