import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PlanTier(str, enum.Enum):
    STARTER = "starter"
    STANDARD = "standard"
    ANALYTICS = "analytics"
    ELITE = "elite"


class BillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"
    BIANNUAL = "biannual"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tier: Mapped[PlanTier] = mapped_column(Enum(PlanTier), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    price_monthly: Mapped[float] = mapped_column(Float, nullable=False)
    price_semiannual: Mapped[float] = mapped_column(Float, nullable=False)
    price_annual: Mapped[float] = mapped_column(Float, nullable=False)
    price_biannual: Mapped[float] = mapped_column(Float, nullable=False)

    # Feature flags
    max_videos_per_month: Mapped[int] = mapped_column(Integer, default=5)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=50)
    can_download: Mapped[bool] = mapped_column(default=False)
    has_drawing_tools: Mapped[bool] = mapped_column(default=False)
    has_analytics: Mapped[bool] = mapped_column(default=False)
    has_coach_assist: Mapped[bool] = mapped_column(default=False)
    has_player_spotlight: Mapped[bool] = mapped_column(default=False)
    has_live_streaming: Mapped[bool] = mapped_column(default=False)
    max_cameras: Mapped[int] = mapped_column(Integer, default=1)
    has_multi_camera: Mapped[bool] = mapped_column(default=False)
    has_export_social: Mapped[bool] = mapped_column(default=False)
    has_api_access: Mapped[bool] = mapped_column(default=False)

    stripe_price_id_monthly: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_price_id_annual: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False
    )
    billing_cycle: Mapped[BillingCycle] = mapped_column(
        Enum(BillingCycle), default=BillingCycle.MONTHLY
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user = relationship("User", back_populates="subscription")
