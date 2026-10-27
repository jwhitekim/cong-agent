# cong-agent

저장된 혼잡도 관측값을 스스로 조회해 혼잡 판정과 대응 권고를 내는 LLM 에이전트입니다. OpenHands software-agent-sdk 위에서 동작합니다.

입력은 [`congestion-llm-gating`](https://github.com/jwhitekim/congestion-agent)이 저장한 세션 폴더(`session.json`, `results.jsonl`)입니다. 에이전트는 전체 요약과 조건 검색으로 볼 구간을 고르고, 구간별 관측값과 구역별 추세를 확인한 뒤 근거 구간과 함께 판정을 제출합니다. 기존 LLM 판정과 규칙 트리거 정보는 에이전트에게 주지 않습니다. 영상, GPU, 검출 모델은 필요 없습니다.

지금은 에이전트, 조회 도구, 합성 세션 테스트까지 있습니다. 실제 API 실행 결과와 판정 정확도 평가 결과는 저장소에 없습니다.

## 시작하기

Python 3.12 이상이 필요합니다. 저장소 루트에서 실행합니다.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env   # ANTHROPIC_API_KEY 입력
```

저장소에 포함된 합성 세션으로 실행해 볼 수 있습니다. 실제 데이터는 `--session`에 세션 폴더를 넘깁니다.

```bash
.venv/bin/python -m cong_agent run \
  --session tests/fixtures/session_small \
  --question "이 세션에서 혼잡이 가장 심했던 구간과 권고 수준은?"
```

모델, 최대 단계, 시스템 프롬프트는 [`config/default.yaml`](config/default.yaml)에 있습니다. 모델은 `CONG_AGENT_MODEL` 환경변수로도 바꿀 수 있습니다.

실행 기록은 `trajectories/<시각>/`에 남습니다. `run.json`에 질문·모델·최종 상태·판정·토큰 사용량이, `conversation/`에 LLM 응답과 도구 호출이 저장됩니다. `action`은 사람에게 주는 권고이며 자동으로 실행되지 않습니다.

## 관련 문서

- [입력 관측값과 판정 범위](.claude/rules/overview.md)
- [도구 출력과 판정 제출 규약](.claude/rules/tools.md)
- [설정, 실행 기록, 최종 상태, CLI 옵션](.claude/rules/agent.md)
- [테스트와 검증](.claude/rules/verification.md)

## 라이선스

LICENSE 파일이 없습니다. 라이선스는 확인이 필요합니다.
