# SDD 문서

현재 코드와 테스트로 확인한 계약, 목적, 설계, 요구사항, 구현 상태를 기록한다.

## 읽는 순서

1. [contract.md](contract.md): 프로젝트의 상위 약속. v0.1 최초 작성 후 FROZEN으로 유지한다.
2. [proposal.md](proposal.md): 만드는 이유, 범위, 변경이력.
3. [design.md](design.md): capability를 가로지르는 기술 결정과 이유.
4. capability 명세: 앞 capability에 뒤 capability가 의존한다.
   - [session-loading](specs/session-loading/spec.md): 세션 적재와 숨김 필드 차단.
   - [query-tools](specs/query-tools/spec.md): 조회 도구 4개, 출력 형식, 입력 오류.
   - [judgment-submission](specs/judgment-submission/spec.md): 판정 검증과 저장, 근거 인원 보정.
   - [agent-run](specs/agent-run/spec.md): 실행 구성, 최종 상태, 기록, CLI.
5. [tasks.md](tasks.md): Requirement를 근거로 정리한 전체 구현·테스트 체크리스트.

[docs-rules.md](docs-rules.md)는 문서 배치와 작성·검증 규칙의 요약이다.

`.claude/rules/`는 개발 작업 지침이며, 이 문서는 코드·테스트로 확인한 동작을 명세한다. 서로 다르면 코드·테스트를 따른다.
