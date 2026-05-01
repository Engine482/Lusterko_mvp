"""Pydantic schemas for `/api/v1/soldier/*` (API Contracts §5).

Validation rules come from PRD §8 + Risk Engine Spec §2:
- daily scales: 0..10
- PHQ-4 items: 0..3
- PSS-4 items: 0..4
- comment_text: optional, <=300 chars
- reaction time / go-no-go: non-negative integers
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import BaselineStep, ParseStatus, RiskStatus

ScoreField = Annotated[int, Field(ge=0, le=10)]
Phq4Item = Annotated[int, Field(ge=0, le=3)]
Pss4Item = Annotated[int, Field(ge=0, le=4)]
NonNegInt = Annotated[int, Field(ge=0)]


class Phq4Submission(BaseModel):
    answers: list[Phq4Item] = Field(..., min_length=4, max_length=4)


class Pss4Submission(BaseModel):
    answers: list[Pss4Item] = Field(..., min_length=4, max_length=4)


class SleepSubmission(BaseModel):
    sleep_score: ScoreField


class ReactionTestSubmission(BaseModel):
    median_reaction_time_ms: Annotated[int, Field(ge=50, le=10_000)]
    valid_trials: Annotated[int, Field(ge=5)]


class GoNoGoSubmission(BaseModel):
    commission_errors: NonNegInt
    omission_errors: NonNegInt
    valid_trials: Annotated[int, Field(ge=10)]


class DailyCheckinSubmission(BaseModel):
    sleep_score: ScoreField
    energy_score: ScoreField
    mood_score: ScoreField
    concentration_score: ScoreField
    comment_text: str | None = Field(default=None, max_length=300)


class BaselineStepStatus(BaseModel):
    step_code: BaselineStep
    completed: bool


class OnboardingStatusResponse(BaseModel):
    baseline_completed: bool
    completed_at: datetime | None
    steps: list[BaselineStepStatus]
    next_required_step: BaselineStep | None


class BaselineCompleteResponse(BaseModel):
    baseline_completed: bool
    completed_at: datetime


class DailyTodayResponse(BaseModel):
    already_submitted: bool
    checkin_date: date
    last_risk_status: RiskStatus | None = None


class DailySubmissionResponse(BaseModel):
    daily_checkin_id: uuid.UUID
    risk_status: RiskStatus
    explanation_text: str | None
    ai_parse_status: ParseStatus


class CompletionSummaryResponse(BaseModel):
    daily_due: bool
    weekly_due: bool
    cognitive_due: bool
    last_risk_status: RiskStatus | None


class BaselineSubmittedResponse(BaseModel):
    """Returned by every per-step baseline endpoint. Echoes computed totals
    so the client can render the next progress chip without re-fetching.
    """

    model_config = ConfigDict(extra="forbid")

    step_code: BaselineStep
    accepted: bool = True
    computed: dict[str, int] | None = None
