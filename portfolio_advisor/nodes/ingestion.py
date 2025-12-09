"""
Node A: Ingestion & Extraction (The Analyst)

Parses raw text inputs into structured data using GPT-4o with Pydantic models.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from ..config import settings
from ..models import (
    ParsedPortfolio,
    MacroContext,
    RiskProfile,
    PortfolioExtraction,
    MacroExtraction,
    RiskExtraction,
    PortfolioValidation,
)
from ..prompts import (
    PORTFOLIO_EXTRACTION_SYSTEM,
    PORTFOLIO_EXTRACTION_USER,
    MACRO_EXTRACTION_SYSTEM,
    MACRO_EXTRACTION_USER,
    RISK_EXTRACTION_SYSTEM,
    RISK_EXTRACTION_USER,
)
from ..state import AgentState
from ..utils import normalize_profile_type, normalize_house_view


def ingestion_node(state: AgentState) -> dict:
    """
    Node A: Parse raw texts into structured data.
    
    Args:
        state: Current agent state with portfolio_text, macro_text, risk_text
        
    Returns:
        Dict with parsed_data and market_context
    """
    logger.info("Node A: Starting ingestion & extraction")
    
    llm = ChatOpenAI(
        model=settings.llm.model,
        temperature=settings.llm.temperature_extraction,
    )
    
    logger.info("  Extracting portfolio data...")
    parsed_portfolio = _extract_portfolio(llm, state["portfolio_text"])
    
    logger.info("  Extracting macro context...")
    market_context = _extract_macro(llm, state["macro_text"])
    
    logger.info("  Extracting risk profile...")
    risk_profile = _extract_risk(llm, state["risk_text"])
    
    logger.info("  Validating portfolio data...")
    validation = _validate_portfolio(parsed_portfolio)
    
    if not validation.is_valid:
        for issue in validation.issues:
            logger.warning(f"    Validation issue: {issue}")
    else:
        logger.info("    Portfolio validation passed")
    
    logger.info("Node A: Extraction complete")
    
    return {
        "parsed_data": {
            "portfolio": parsed_portfolio.model_dump(),
            "risk": risk_profile.model_dump(),
        },
        "market_context": market_context.model_dump(),
        "validation": validation.model_dump(),
    }


def _extract_portfolio(llm: ChatOpenAI, portfolio_text: str) -> ParsedPortfolio:
    """Extract and structure portfolio data."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", PORTFOLIO_EXTRACTION_SYSTEM),
        ("human", PORTFOLIO_EXTRACTION_USER),
    ])
    
    chain = prompt | llm.with_structured_output(PortfolioExtraction)
    result: PortfolioExtraction = chain.invoke({"portfolio_text": portfolio_text})
    
    equity_assets = [a for a in result.assets if a.asset_class == "Stocks"]
    equity_value = sum(a.value for a in equity_assets)
    
    fixed_income_assets = [
        a for a in result.assets 
        if a.asset_class in ("Fixed_Income", "Fixed Income", "Renda Fixa", "CDB")
    ]
    fixed_income_value = sum(a.value for a in fixed_income_assets)
    
    total_value = result.total_value or sum(a.value for a in result.assets)
    equity_pct = (equity_value / total_value * 100) if total_value > 0 else 0.0
    fixed_income_pct = (fixed_income_value / total_value * 100) if total_value > 0 else 0.0
    
    return ParsedPortfolio(
        client_name=result.client_name,
        assets=result.assets,
        total_value=total_value,
        equity_value=equity_value,
        equity_pct=equity_pct,
        fixed_income_value=fixed_income_value,
        fixed_income_pct=fixed_income_pct,
    )


def _validate_portfolio(portfolio: ParsedPortfolio) -> PortfolioValidation:
    """
    Validate portfolio data.
    
    Replicates Rivet's Code node 6NEs6fO3Mn_ghaakcM0mP:
    - Check if allocation sum is approximately 100% (95-105% tolerance)
    - Check for null/missing values in critical fields
    """
    issues: list[str] = []
    
    total_allocation = sum(
        (a.value / portfolio.total_value * 100) if portfolio.total_value > 0 else 0
        for a in portfolio.assets
    )
    
    if total_allocation < 95 or total_allocation > 105:
        issues.append(
            f"Total allocation is {total_allocation:.1f}%, expected approximately 100%"
        )
    
    for asset in portfolio.assets:
        if asset.value is None or asset.value == 0:
            issues.append(f"Asset {asset.ticker} has missing or zero value")
    
    return PortfolioValidation(
        is_valid=len(issues) == 0,
        allocation_sum=total_allocation,
        issues=issues,
    )


def _extract_macro(llm: ChatOpenAI, macro_text: str) -> MacroContext:
    """Extract and structure macro context."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", MACRO_EXTRACTION_SYSTEM),
        ("human", MACRO_EXTRACTION_USER),
    ])
    
    chain = prompt | llm.with_structured_output(MacroExtraction)
    result: MacroExtraction = chain.invoke({"macro_text": macro_text})
    
    house_view = normalize_house_view(result.house_view, macro_text)
    
    return MacroContext(
        ipca_2025=result.ipca_2025,
        ipca_2026=result.ipca_2026,
        house_view=house_view,  # type: ignore[arg-type]
        selic_terminal=result.selic_terminal,
        gdp_growth_2025=result.gdp_growth_2025,
        exchange_rate_eoy=result.exchange_rate_eoy,
    )


def _extract_risk(llm: ChatOpenAI, risk_text: str) -> RiskProfile:
    """Extract and structure risk profile."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", RISK_EXTRACTION_SYSTEM),
        ("human", RISK_EXTRACTION_USER),
    ])
    
    chain = prompt | llm.with_structured_output(RiskExtraction)
    result: RiskExtraction = chain.invoke({"risk_text": risk_text})
    
    profile_type = normalize_profile_type(result.profile_type)
    
    max_equity = result.max_equity_pct
    if max_equity <= 0 or max_equity > 100:
        max_equity = settings.risk_defaults.equity_limits.get(profile_type, 40.0)
    
    drift_tolerance = result.drift_tolerance or settings.risk_defaults.drift_tolerance
    
    return RiskProfile(
        client_name=result.client_name,
        profile_type=profile_type,  # type: ignore[arg-type]
        max_equity_pct=max_equity,
        drift_tolerance=drift_tolerance,
    )
