from dataclasses import dataclass
from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..schemas import (
    CompanyNewsItem,
    IndustryDynamic,
    IntelligenceMetrics,
    RecommendedNextSteps,
)


class ToolOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CustomerProfileContext(ToolOutputModel):
    id: str
    name: str
    industry: str | None
    status: str


class ProductContext(ToolOutputModel):
    id: str
    name: str
    description: str | None
    status: str


class SubscriptionContext(ToolOutputModel):
    id: str
    productId: str
    product: str
    subscriptionStartDate: str
    subscriptionEndDate: str | None
    subscriptionStatus: str
    licensedSeats: int | None


class LatestSubscriptionContext(ToolOutputModel):
    found: bool
    subscription: SubscriptionContext | None


class LatestIntelligenceContext(ToolOutputModel):
    found: bool
    generatedAt: str | None
    aiKeySignal: str | None
    industryDynamics: list[IndustryDynamic]
    companyNews: list[CompanyNewsItem]
    recommendedNextSteps: RecommendedNextSteps | None
    metrics: IntelligenceMetrics | None


@dataclass(frozen=True)
class CustomerRunContext:
    customer_id: UUID


@dataclass(frozen=True)
class IntelligenceRunContext(CustomerRunContext):
    period_start: date
    period_end: date


@dataclass(frozen=True)
class MeetingBriefRunContext(CustomerRunContext):
    product_id: UUID
