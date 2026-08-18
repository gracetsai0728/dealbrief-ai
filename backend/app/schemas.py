from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CallBriefOutput(StrictModel):
    title: str
    summary: str
    customerSnapshot: str
    keyInsights: list[str] = Field(min_length=1, max_length=6)
    talkingPoints: list[str] = Field(min_length=1, max_length=8)
    suggestedQuestions: list[str] = Field(min_length=1, max_length=8)
    risksAndOpportunities: list[str] = Field(min_length=1, max_length=6)
    nextSteps: list[str] = Field(min_length=1, max_length=6)


class EmailContent(StrictModel):
    to: str
    subject: str
    greeting: str
    paragraphs: list[str] = Field(min_length=1, max_length=5)
    callToAction: str
    signature: str


class EmailDraftOutput(StrictModel):
    title: str
    summary: str
    email: EmailContent


class AgendaItem(StrictModel):
    time: str
    topic: str
    detail: str


class AgendaContent(StrictModel):
    objective: str
    desiredOutcome: str
    items: list[AgendaItem] = Field(min_length=1, max_length=8)
    preparation: list[str] = Field(min_length=1, max_length=6)


class MeetingAgendaOutput(StrictModel):
    title: str
    summary: str
    agenda: AgendaContent


class ActionRecommendation(StrictModel):
    action: str
    priority: Literal["high", "medium", "low"]
    reason: str
    dueDate: str | None


class RecommendedNextSteps(StrictModel):
    crossSell: list[ActionRecommendation] = Field(min_length=1, max_length=2)
    upsell: list[ActionRecommendation] = Field(min_length=1, max_length=2)
    renewal: list[ActionRecommendation] = Field(min_length=1, max_length=2)
    winback: list[ActionRecommendation] = Field(min_length=1, max_length=2)


class IndustryDynamic(StrictModel):
    headline: str
    summary: str
    impact: str


class CompanyNewsItem(StrictModel):
    headline: str
    summary: str
    sourceName: str
    sourceUrl: str | None
    publishedDate: str | None
    sourceType: Literal["web", "synthetic"]
    isMock: bool

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_news(cls, value):
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        source_name = str(normalized.get("sourceName") or "")
        inferred_mock = (
            bool(normalized.get("isMock"))
            or "mock" in source_name.lower()
            or "synthetic" in source_name.lower()
        )
        normalized.setdefault("sourceType", "synthetic" if inferred_mock else "web")
        normalized.setdefault("isMock", inferred_mock)
        if normalized["isMock"]:
            normalized["sourceUrl"] = None
        return normalized


class IntelligenceMetrics(StrictModel):
    accountHealthScore: int = Field(ge=0, le=100)
    totalLicensedSeats: int = Field(ge=0)
    activeSubscriptions: int = Field(ge=0)
    riskReasons: list[str] = Field(max_length=6)


class IntelligenceOutput(StrictModel):
    aiKeySignal: str
    industryDynamics: list[IndustryDynamic] = Field(min_length=2, max_length=2)
    companyNews: list[CompanyNewsItem] = Field(max_length=5)
    recommendedNextSteps: RecommendedNextSteps
    metrics: IntelligenceMetrics


BRIEF_OUTPUT_SCHEMAS = {
    "call_brief": CallBriefOutput,
    "email_draft": EmailDraftOutput,
    "meeting_agenda": MeetingAgendaOutput,
}
