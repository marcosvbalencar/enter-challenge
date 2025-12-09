"""
Pydantic models for structured data extraction and validation.

This module defines all data models used throughout the advisory workflow.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Market Data Models (from CSV)
# =============================================================================

class MarketPrice(BaseModel):
    """Price data from profitability CSV."""
    
    asset_class: str = Field(description="Asset class (Stocks, etc.)")
    ticker: str = Field(description="Stock ticker symbol")
    current_price: float = Field(description="Current market price")
    last_month_price: float = Field(description="Price at end of last month")


class CalculatedReturn(BaseModel):
    """Calculated monthly return for an asset."""
    
    ticker: str = Field(description="Stock ticker symbol")
    current_price: float = Field(description="Current market price")
    last_month_price: float = Field(description="Price at end of last month")
    monthly_return_pct: float = Field(description="Monthly return percentage")
    position_value: float = Field(default=0.0, description="Position value in BRL")


# =============================================================================
# Portfolio Models
# =============================================================================

class Asset(BaseModel):
    """Represents a single asset in the portfolio."""
    
    ticker: str = Field(description="Stock ticker symbol (e.g., PETR4, VALE3)")
    value: float = Field(description="Current market value in BRL")
    asset_class: str = Field(description="Asset class: Stocks, Fixed_Income, Funds")
    return_pct: Optional[float] = Field(
        default=None,
        description="All-time return percentage from portfolio document"
    )
    monthly_return_pct: Optional[float] = Field(
        default=None,
        description="Monthly return percentage (calculated from CSV)"
    )


class ParsedPortfolio(BaseModel):
    """Structured representation of the client's portfolio."""
    
    assets: list[Asset] = Field(description="List of all assets in the portfolio")
    total_value: float = Field(description="Total portfolio value in BRL")
    equity_value: float = Field(description="Total value in equities (stocks)")
    equity_pct: float = Field(description="Percentage allocated to equities")
    fixed_income_value: float = Field(default=0.0, description="Total value in fixed income")
    fixed_income_pct: float = Field(default=0.0, description="Percentage in fixed income")


class PortfolioValidation(BaseModel):
    """Result of portfolio validation checks."""
    
    is_valid: bool = Field(description="Whether the portfolio passes validation")
    allocation_sum: float = Field(description="Sum of all allocation percentages")
    issues: list[str] = Field(default_factory=list, description="List of validation issues")


# =============================================================================
# Macro Context Models
# =============================================================================

class MacroContext(BaseModel):
    """Structured macro-economic context from research report."""
    
    ipca_2025: float = Field(description="IPCA inflation forecast for 2025 (%)")
    ipca_2026: float = Field(description="IPCA inflation forecast for 2026 (%)")
    house_view: Literal["Bullish", "Bearish", "Neutral"] = Field(
        description="Overall market outlook"
    )
    selic_terminal: float = Field(description="Projected terminal SELIC rate (%)")
    gdp_growth_2025: Optional[float] = Field(
        default=None,
        description="GDP growth forecast for 2025 (%)"
    )
    exchange_rate_eoy: Optional[float] = Field(
        default=None,
        description="Expected BRL/USD exchange rate at end of year"
    )


# =============================================================================
# Risk Profile Models
# =============================================================================

class RiskProfile(BaseModel):
    """Client's risk profile and investment constraints."""
    
    profile_type: Literal["Conservative", "Moderate", "Aggressive"] = Field(
        description="Client's risk profile classification"
    )
    max_equity_pct: float = Field(
        description="Maximum percentage allowed in equities"
    )
    drift_tolerance: float = Field(
        default=5.0,
        description="Allowed drift from target allocation before rebalancing (%)"
    )


# =============================================================================
# Rebalancing Models
# =============================================================================

ActionType = Literal["HARD_SELL", "SOFT_SELL", "TRIM", "HOLD"]


class RebalancingAction(BaseModel):
    """A single rebalancing action recommendation."""
    
    ticker: str = Field(description="Stock ticker to act on")
    action: ActionType = Field(description="Recommended action type")
    size_pct: float = Field(description="Percentage of position to sell (0-100)")
    current_value: float = Field(description="Current position value in BRL")
    suggested_sell_value: float = Field(description="Suggested value to sell in BRL")
    rationale: str = Field(description="Justification for the action")


class RebalancingPlan(BaseModel):
    """Complete rebalancing plan with all actions."""
    
    rebalance_needed: bool = Field(description="Whether rebalancing is required")
    current_equity_pct: float = Field(description="Current equity allocation %")
    target_equity_pct: float = Field(description="Target equity allocation %")
    actions: list[RebalancingAction] = Field(
        default_factory=list,
        description="List of recommended actions"
    )
    total_sell_value: float = Field(
        default=0.0,
        description="Total value to be sold in BRL"
    )
    summary: str = Field(
        default="",
        description="Brief summary of the rebalancing plan"
    )


# =============================================================================
# Compliance Models
# =============================================================================

IssueType = Literal["FORBIDDEN_TERM", "HALLUCINATION", "VALUE_MISMATCH"]


class ComplianceIssue(BaseModel):
    """A single compliance issue found in the draft letter."""
    
    issue_type: IssueType = Field(description="Type of compliance issue")
    description: str = Field(description="Description of the issue")
    original_text: Optional[str] = Field(
        default=None,
        description="The problematic text from the draft"
    )
    suggested_fix: Optional[str] = Field(
        default=None,
        description="Suggested correction"
    )


class ComplianceReport(BaseModel):
    """Report from compliance audit of the draft letter."""
    
    passed: bool = Field(description="Whether the letter passed compliance check")
    issues: list[ComplianceIssue] = Field(
        default_factory=list,
        description="List of issues found"
    )
    corrections_made: int = Field(
        default=0,
        description="Number of corrections applied"
    )


# =============================================================================
# LLM Extraction Models (for structured output)
# =============================================================================

class PortfolioExtraction(BaseModel):
    """Schema for portfolio extraction from raw text."""
    
    assets: list[Asset] = Field(description="List of assets found in the portfolio")
    total_value: float = Field(
        description="Total portfolio value in BRL (convert from R$ format)"
    )


class MacroExtraction(BaseModel):
    """Schema for macro context extraction from research report."""
    
    ipca_2025: float = Field(description="IPCA forecast for 2025 in percentage")
    ipca_2026: float = Field(description="IPCA forecast for 2026 in percentage")
    house_view: str = Field(description="Overall market outlook: Bullish/Bearish/Neutral")
    selic_terminal: float = Field(description="Terminal SELIC rate projection (%)")
    gdp_growth_2025: Optional[float] = Field(
        default=None,
        description="GDP growth forecast for 2025"
    )
    exchange_rate_eoy: Optional[float] = Field(
        default=None,
        description="BRL/USD exchange rate forecast for end of year"
    )


class RiskExtraction(BaseModel):
    """Schema for risk profile extraction."""
    
    profile_type: str = Field(
        description="Risk profile: Conservative, Moderate, or Aggressive"
    )
    max_equity_pct: float = Field(
        description="Maximum equity allocation % (infer from profile if not explicit)"
    )
    drift_tolerance: float = Field(
        default=5.0,
        description="Allowed drift before rebalancing (default 5%)"
    )
