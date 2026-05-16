from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RiskRuleCreate(BaseModel):
    rule_type: str = Field(..., min_length=1)
    account_id: Optional[str] = None
    symbol: Optional[str] = None
    threshold_value: float = Field(..., gt=0)
    comparison: str = Field(default="lte", pattern="^(lte|gte|eq)$")
    action: str = Field(default="block", pattern="^(block|warn|notify)$")


class RiskRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    account_id: Optional[str]
    rule_type: str
    symbol: Optional[str]
    threshold_value: float
    comparison: str
    action: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RiskCheckResult(BaseModel):
    passed: bool
    blocking_rules: list[str] = []
    warning_rules: list[str] = []
    current_exposure: Optional[float] = None
    current_position_size: Optional[float] = None
    message: Optional[str] = None
