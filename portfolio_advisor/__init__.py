"""
Portfolio Rebalancing & Advisory Agent

A LangGraph-based application for portfolio analysis and rebalancing recommendations.

Usage:
    from portfolio_advisor import run_advisory
    
    result = run_advisory(
        portfolio_text="...",
        macro_text="...",
        risk_text="..."
    )
    print(result["final_letter"])
"""

from .graph import app, run_advisory
from .models import (
    Asset,
    ParsedPortfolio,
    MacroContext,
    RiskProfile,
    RebalancingAction,
    RebalancingPlan,
)

__version__ = "1.0.0"

__all__ = [
    # Main exports
    "app",
    "run_advisory",
    # Models
    "Asset",
    "ParsedPortfolio",
    "MacroContext",
    "RiskProfile",
    "RebalancingAction",
    "RebalancingPlan",
]
