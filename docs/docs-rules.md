# 문서 배치 규칙

## 구조

```text
docs/
├── README.md
├── contract.md
├── proposal.md
├── design.md
├── tasks.md
├── docs-rules.md
└── specs/
    ├── session-loading/spec.md
    ├── query-tools/spec.md
    ├── judgment-submission/spec.md
    └── agent-run/spec.md
```

- capability 폴더에는 `spec.md`만 둔다. `design.md`와 `tasks.md`는 프로젝트에 하나씩 둔다.
- `openspec/`, `AGENTS.md`, `changes/` 같은 OpenSpec 이름을 문서 구조에 쓰지 않는다.
- 파일명에 버전을 붙이지 않는다. 버전은 문서 제목과 `proposal.md` 변경이력에서 관리한다.
- `contract.md`는 최초 작성 후 FROZEN이다. 다른 문서에서 인용만 한다.
- 요구사항은 코드·테스트로 확인한 동작만 적는다. 기존 규칙 문서와 다르면 코드·테스트를 따른다.

## 명세 형식

각 `spec.md`는 `# <capability> spec` 제목, 한두 줄의 범위 설명, 의존 capability로 시작한다. 그 아래에는 요구사항과 시나리오만 둔다.

Requirement 이름은 영문 Title Case이며 저장소 전체에서 고유해야 한다. 제목 바로 다음 줄에 빈 줄 없이 한국어 주어와 `SHALL`을 넣은 단정문을 쓴다.

```text
### Requirement: Unique English Name
시스템은 SHALL 확인된 동작을 수행한다.

#### Scenario: 동작을 확인하는 상황
- GIVEN 전제 상태
- WHEN 트리거 조건
- THEN 기대 결과
```

모든 Scenario는 제목 다음 6줄 안에 GIVEN·WHEN·THEN 세 줄을 모두 둔다. 볼드체를 쓰지 않는다.

## 작업 체크리스트

`tasks.md`는 capability 의존 순서로 나눈다. 모든 항목에 명세와 정확히 일치하는 Requirement 이름을 `(근거: <Requirement 이름>)`으로 적는다. 구현과 테스트가 모두 있으면 `[x]`, 그렇지 않으면 `[ ]`로 표시한다. 근거 Requirement가 없는 작업은 넣지 않는다.

## 검증

```bash
bash ~/.claude/skills/spec-docs/scripts/check-spec.sh docs/
```

검사 결과가 OK인지 확인하고, 별도로 Requirement 이름의 고유성, 작업 근거, 코드·테스트와의 일치를 검토한다.
