# 프로젝트 계약 v0.1 — FROZEN

최초 작성 후 동결한다. 이후 문서는 이 계약을 인용하며 본문을 수정하지 않는다.

- 분석 입력은 `congestion-llm-gating`이 남긴 세션 폴더 하나다. 그 저장소와 입력은 읽기만 하며, 코드를 가져오거나 수정하지 않는다.
- 이미 계산된 관측값으로 판단한다. 영상·이미지·GPU·검출 모델을 사용하지 않으며 LLM에는 텍스트만 보낸다.
- 에이전트에게 기존 판정 `agent`, 원시 트랙 `tracks`, 처리 시간 `cv_elapsed_sec`, 규칙 정보 `trigger`, `trigger_reason`, `co_triggered`, `dynamic_thresholds`를 보여 주지 않는다.
- 판정은 `submit_judgment`로만 만든다. 조회 도구는 판정 어휘 `normal/caution/anomaly`, `none/monitor/alert`를 출력하지 않는다.
- 판정의 `action`은 대응 권고 수준이다. 알림이나 외부 시스템 실행 같은 부수효과가 없다.
- 에이전트 도구는 `session_overview`, `view_segments`, `find_segments`, `zone_trend`, `submit_judgment`, `finish`, `think`로 제한한다. 터미널·파일 편집·브라우저·이미지 보기 도구는 제공하지 않는다.
- 실행 기록은 기본 `trajectories/` 아래 실행별 폴더에 남긴다. 출력 위치를 지정하면 그 위치를 사용한다. 대화 기록과 실행 요약을 보존한다.
