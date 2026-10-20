"""조회 도구 공통 기반: 공용 Observation, Executor, ToolDefinition.

각 도구 폴더는 impl.py에 순수 함수 `fn(session, **args) -> str`를 두고,
definition.py에서 이 기반 클래스에 Action·설명·함수만 채운다.
"""
from collections.abc import Callable, Sequence
from typing import Any, ClassVar, Self

from openhands.sdk import Action, Observation, ToolDefinition
from openhands.sdk.tool import ToolExecutor

from cong_agent.environment import Session
from cong_agent.tools.utils.errors import ToolError


class CongestionObservation(Observation):
    """모든 혼잡도 도구가 쓰는 텍스트 관측."""


def action_args(action: Action) -> dict[str, Any]:
    """Action에서 도구가 직접 선언한 인자만 꺼낸다. None은 '지정 안 함'이라 뺀다."""
    own = set(type(action).model_fields) - set(Action.model_fields)
    return {k: getattr(action, k) for k in own if getattr(action, k) is not None}


class QueryExecutor(ToolExecutor):
    """순수 함수를 불러 결과를 관측으로 바꾼다. ToolError는 is_error 관측이 된다."""

    def __init__(self, session: Session, fn: Callable[..., str]):
        self.session = session
        self.fn = fn

    def __call__(self, action: Action, conversation: Any = None) -> CongestionObservation:
        try:
            text = self.fn(self.session, **action_args(action))
        except ToolError as e:
            return CongestionObservation.from_text(text=str(e), is_error=True)
        return CongestionObservation.from_text(text=text)


class QueryTool(ToolDefinition[Action, CongestionObservation]):
    """조회 도구 기반. 하위 클래스는 action_cls, tool_description, fn만 채운다.

    도구 이름은 SDK가 클래스 이름에서 만든다 (ViewSegmentsTool → view_segments).
    """

    action_cls: ClassVar[type[Action]]
    tool_description: ClassVar[str]
    fn: ClassVar[Callable[..., str]]

    @classmethod
    def create(cls, conv_state: Any = None, *, session: Session, **_: Any) -> Sequence[Self]:
        return [cls(description=cls.tool_description, action_type=cls.action_cls,
                    observation_type=CongestionObservation,
                    executor=QueryExecutor(session, cls.fn))]
