"""관측 출력 형식 규칙을 한 곳에 둔다 (SWE-agent의 창 단위 보기).

- 실수는 소수 둘째 자리
- 표는 한 번에 최대 WINDOW행, 잘리면 남은 범위 안내
- 번호 목록은 최대 LIST_MAX개, 전체 개수는 항상 표시
"""
WINDOW = 20
LIST_MAX = 50


def num(x: float | int) -> str:
    if isinstance(x, int):
        return str(x)
    return f"{x:.2f}"


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = [" | ".join(header)]
    lines += [" | ".join(r) for r in rows]
    return "\n".join(lines)


def window_note(shown_end: int, requested_end: int) -> str:
    if shown_end >= requested_end:
        return ""
    return f"\n(최대 {WINDOW}행만 표시. 남은 범위: {shown_end + 1}–{requested_end})"


def index_list(indices: list[int]) -> str:
    head = ", ".join(str(i) for i in indices[:LIST_MAX])
    if len(indices) > LIST_MAX:
        head += f" … (처음 {LIST_MAX}개만 표시)"
    return head
