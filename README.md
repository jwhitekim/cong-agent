# cong-agent

저장된 혼잡도 관측값을 조회해 근거 구간과 함께 혼잡 판정과 대응 권고를 내는 LLM 에이전트입니다. OpenHands software-agent-sdk 위에서 동작합니다.

`congestion-llm-gating`이 저장한 세션 폴더(`session.json`, `results.jsonl`)를 입력으로 사용합니다. 영상·GPU·검출 모델 없이 관측값을 분석하며, 대응 권고는 자동으로 실행되지 않습니다.

## 시작하기

Python 3.12 이상과 Anthropic API 키가 필요합니다. 저장소 루트에서 API 키를 설정하고, 포함된 합성 세션에 질문 하나를 실행합니다.

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
export ANTHROPIC_API_KEY='<발급받은 API 키>'
.venv/bin/python -m cong_agent run \
  --session tests/fixtures/session_small \
  --question "이 세션에서 혼잡이 가장 심했던 구간과 권고 수준은?"
```

판정이 제출되면 터미널에 표시됩니다. 실행 기록은 `trajectories/<시각>/`에 저장됩니다.

## 관련 문서

- [입력 관측값과 판정 범위](.claude/rules/overview.md)
- [도구 출력과 판정 제출 규약](.claude/rules/tools.md)
- [설정·실행 기록·최종 상태·CLI 옵션](.claude/rules/agent.md)
- [테스트와 검증](.claude/rules/verification.md)

## 라이선스

LICENSE 파일이 없습니다. 라이선스는 확인이 필요합니다.
