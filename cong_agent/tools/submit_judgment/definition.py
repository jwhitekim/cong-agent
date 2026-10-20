"""submit_judgment 스키마와 등록.

Action은 SDK 기본값(extra="forbid")과 달리 모르는 인자를 받아 둔다. LLM이 몰래 넣은
total_people 같은 숫자 필드를 거부가 아니라 제거하기 위해서다(impl.validate_judgment).
"""
from collections.abc import Sequence
from typing import Any, ClassVar, Self

from openhands.sdk import Action, ToolDefinition
from pydantic import ConfigDict, Field

from cong_agent.environment import Session
from cong_agent.tools.submit_judgment.impl import (VALID_ACTION, VALID_ASSESSMENT, JudgmentStore,
                                                   SubmitJudgmentExecutor)
from cong_agent.tools.utils.base import CongestionObservation

DESCRIPTION = ("최종 판정 제출. action은 실행되지 않는 대응 권고 수준이다. "
               "제출이 받아들여져도 실행은 끝나지 않으니, 이어서 finish를 호출한다.")


class SubmitJudgmentAction(Action):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow", frozen=True)

    assessment: str = Field(description=f"{', '.join(VALID_ASSESSMENT)} 중 하나")
    action: str = Field(description=f"{', '.join(VALID_ACTION)} 중 하나. 실행되지 않는 대응 권고 수준")
    evidence_segments: list[int] = Field(description="판정 근거로 직접 확인한 세그먼트 번호(1개 이상)")
    summary: str = Field(description="질문에 대한 한두 문장 답")
    reasoning: str = Field(description="도구로 확인한 관측값에 근거한 설명")


class SubmitJudgmentTool(ToolDefinition[SubmitJudgmentAction, CongestionObservation]):
    @classmethod
    def create(cls, conv_state: Any = None, *, session: Session, store: JudgmentStore,
               **_: Any) -> Sequence[Self]:
        return [cls(description=DESCRIPTION, action_type=SubmitJudgmentAction,
                    observation_type=CongestionObservation,
                    executor=SubmitJudgmentExecutor(session, store))]
