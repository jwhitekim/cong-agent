"""조회 도구와 판정 제출을 OpenHands SDK 도구(ToolDefinition)로 감싼다.

도구 로직은 query.py / submit.py의 순수 함수 그대로다. 여기서는
- 도구별 Action(인자 스키마, pydantic)을 선언하고
- Executor가 run_tool을 불러 결과를 Observation으로 바꾸며
- ToolError를 is_error=True 관측으로 돌려준다.

Action은 기본적으로 모르는 인자를 거부한다(SDK Schema가 extra="forbid").
판정 제출만 예외로 모르는 인자를 받아 두고 validate_judgment가 숫자 카운트 필드를
걷어낸다 — LLM이 몰래 넣은 total_people을 거부가 아니라 제거하기 위해서다.
"""
from collections.abc import Sequence
from typing import Any, ClassVar, Self

from openhands.sdk import Action, Observation, ToolDefinition
from openhands.sdk.tool import ToolExecutor, register_tool
from pydantic import ConfigDict, Field

from cong_agent.session import Session
from cong_agent.tools import TOOLS, ToolError, run_tool, validate_judgment
from cong_agent.tools.query import LEVELS
from cong_agent.tools.submit import VALID_ACTION, VALID_ASSESSMENT


class JudgmentStore:
    """검증을 통과한 판정을 담는다. 유효한 제출이 여러 번이면 마지막 것이 남는다."""

    def __init__(self) -> None:
        self.judgment: dict[str, Any] | None = None


class CongestionObservation(Observation):
    """모든 혼잡도 도구가 쓰는 텍스트 관측."""


# --- Action (인자 스키마) ---

class SessionOverviewAction(Action):
    pass


class ViewSegmentsAction(Action):
    start: int = Field(description="시작 세그먼트 번호(포함)")
    end: int = Field(description="끝 세그먼트 번호(포함)")


class FindSegmentsAction(Action):
    level: str | None = Field(default=None, description=f"혼잡 등급: {', '.join(LEVELS)}")
    min_total: int | None = Field(default=None, description="이 인원 이상")
    max_avg_speed: float | None = Field(default=None, description="평균 속도(px/s)가 이 값 이하")
    min_density_slope: float | None = Field(default=None, description="density_slope가 이 값 이상")


class ZoneTrendAction(Action):
    zone: str = Field(description="구역 이름")
    start: int | None = Field(default=None, description="시작 세그먼트 번호(포함). 생략하면 0")
    end: int | None = Field(default=None, description="끝 세그먼트 번호(포함). 생략하면 마지막")


class SubmitJudgmentAction(Action):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow", frozen=True)

    assessment: str = Field(description=f"{', '.join(VALID_ASSESSMENT)} 중 하나")
    action: str = Field(description=f"{', '.join(VALID_ACTION)} 중 하나. 실행되지 않는 대응 권고 수준")
    evidence_segments: list[int] = Field(description="판정 근거로 직접 확인한 세그먼트 번호(1개 이상)")
    summary: str = Field(description="질문에 대한 한두 문장 답")
    reasoning: str = Field(description="도구로 확인한 관측값에 근거한 설명")


def _args(action: Action, names: Sequence[str]) -> dict[str, Any]:
    """Action에서 우리 도구 인자만 꺼낸다. None은 '지정 안 함'이라 뺀다."""
    return {n: getattr(action, n) for n in names if getattr(action, n) is not None}


# --- Executor ---

class QueryExecutor(ToolExecutor):
    def __init__(self, session: Session, name: str, arg_names: Sequence[str]):
        self.session = session
        self.name = name
        self.arg_names = tuple(arg_names)

    def __call__(self, action: Action, conversation: Any = None) -> CongestionObservation:
        try:
            text = run_tool(self.session, self.name, _args(action, self.arg_names))
        except ToolError as e:
            return CongestionObservation.from_text(text=str(e), is_error=True)
        return CongestionObservation.from_text(text=text)


class SubmitExecutor(ToolExecutor):
    _FIELDS = ("assessment", "action", "evidence_segments", "summary", "reasoning")

    def __init__(self, session: Session, store: JudgmentStore):
        self.session = session
        self.store = store

    def __call__(self, action: Action, conversation: Any = None) -> CongestionObservation:
        args = {n: getattr(action, n) for n in self._FIELDS}
        args.update(action.model_extra or {})
        try:
            judgment = validate_judgment(self.session, args)
        except ToolError as e:
            return CongestionObservation.from_text(text=str(e), is_error=True)
        self.store.judgment = judgment
        return CongestionObservation.from_text(
            text="판정을 받았습니다. 더 확인할 것이 없으면 finish를 호출해 실행을 끝내세요.")


# --- ToolDefinition ---
# 도구 이름은 SDK가 클래스 이름에서 만든다 (SessionOverviewTool → session_overview).

class _QueryTool(ToolDefinition[Action, CongestionObservation]):
    action_cls: ClassVar[type[Action]]
    arg_names: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def create(cls, conv_state: Any = None, *, session: Session, **_: Any) -> Sequence[Self]:
        return [cls(description=TOOLS[cls.name].description, action_type=cls.action_cls,
                    observation_type=CongestionObservation,
                    executor=QueryExecutor(session, cls.name, cls.arg_names))]


class SessionOverviewTool(_QueryTool):
    action_cls = SessionOverviewAction


class ViewSegmentsTool(_QueryTool):
    action_cls = ViewSegmentsAction
    arg_names = ("start", "end")


class FindSegmentsTool(_QueryTool):
    action_cls = FindSegmentsAction
    arg_names = ("level", "min_total", "max_avg_speed", "min_density_slope")


class ZoneTrendTool(_QueryTool):
    action_cls = ZoneTrendAction
    arg_names = ("zone", "start", "end")


class SubmitJudgmentTool(ToolDefinition[SubmitJudgmentAction, CongestionObservation]):
    @classmethod
    def create(cls, conv_state: Any = None, *, session: Session, store: JudgmentStore,
               **_: Any) -> Sequence[Self]:
        return [cls(description=TOOLS["submit_judgment"].description +
                    " 제출이 받아들여져도 실행은 끝나지 않으니, 이어서 finish를 호출한다.",
                    action_type=SubmitJudgmentAction, observation_type=CongestionObservation,
                    executor=SubmitExecutor(session, store))]


TOOL_CLASSES: tuple[type[ToolDefinition], ...] = (
    SessionOverviewTool, ViewSegmentsTool, FindSegmentsTool, ZoneTrendTool, SubmitJudgmentTool)


def register_tools(session: Session, store: JudgmentStore) -> list[str]:
    """세션과 store를 쥔 도구 인스턴스를 SDK registry에 등록하고 이름 목록을 돌려준다.

    SDK registry는 프로세스 전역이라, 같은 이름으로 다시 등록해 이전 세션을 덮어쓴다.
    """
    names = []
    for cls in TOOL_CLASSES:
        (tool,) = cls.create(session=session, store=store)
        register_tool(cls.name, tool)
        names.append(cls.name)
    return names
