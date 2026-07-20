"""Pydantic models for API requests and responses."""

from typing import Any

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    full_name: str | None = None


class LoginRequest(BaseModel):
    """User login request."""

    username: str
    password: str


class UserResponse(BaseModel):
    """User data response."""

    id: int
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_verified: bool


class AuthResponse(BaseModel):
    """Authentication response with token and user data."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str


class UserSettingsResponse(BaseModel):
    """User settings response."""

    user_id: int
    theme: str = "system"
    language: str = "en"
    timezone: str = "UTC"
    log_verbosity: str = "info"
    performance_mode: str = "balanced"
    broker_credentials: dict[str, Any] | list[Any] | None = {}
    trading_preferences: dict[str, Any] | list[Any] | None = {}
    notifications: dict[str, Any] | list[Any] | None = {}
    alert_triggers: dict[str, Any] | list[Any] | None = {}


class UpdateUserSettingsRequest(BaseModel):
    """Update user settings request."""

    theme: str | None = None
    language: str | None = None
    timezone: str | None = None
    log_verbosity: str | None = None
    performance_mode: str | None = None
    broker_credentials: dict[str, Any] | list[Any] | str | None = None
    trading_preferences: dict[str, Any] | list[Any] | str | None = None
    notifications: dict[str, Any] | list[Any] | str | None = None
    alert_triggers: dict[str, Any] | list[Any] | str | None = None


class BrokerStatusResponse(BaseModel):
    """Broker status response."""

    status: str
    broker_name: str
    equity: float
    balance: float
    margin_level: float
    free_margin: float


class DashboardEquityPoint(BaseModel):
    """Single dashboard equity point."""

    timestamp: str
    equity: float


class DashboardEquityCurveResponse(BaseModel):
    """Dashboard equity curve response."""

    points: list[DashboardEquityPoint]
    history_span_seconds: float = 0.0
    point_count: int = 0


class DashboardDailyPnlPoint(BaseModel):
    """Single daily PnL point for the dashboard."""

    day: str
    pnl: float


class DashboardActiveStrategyItem(BaseModel):
    """Active strategy row for the dashboard."""

    name: str
    market: str
    status: str
    timeframe: str
    session_name: str


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary response."""

    daily_pnl: list[DashboardDailyPnlPoint]
    weekly_pnl_total: float = 0.0
    weekly_best_day: float = 0.0
    weekly_worst_day: float = 0.0
    win_rate: float = 0.0
    closed_trade_count: int = 0
    winning_trade_count: int = 0
    active_strategy_count: int = 0
    active_strategies: list[DashboardActiveStrategyItem]


class MarketStatus(BaseModel):
    """Market status details."""

    name: str
    status: str
    message: str  # e.g. "Opening in 2h 15m" or "Closing in 30m"
    open: str
    close: str
    local_time: str


class MarketHoursResponse(BaseModel):
    """Response model for market hours."""

    markets: list[MarketStatus]


class SystemStatusResponse(BaseModel):
    """System status response."""

    backend: str
    database: str
    message: str


class ResourceUsageResponse(BaseModel):
    """Resource usage response."""

    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
