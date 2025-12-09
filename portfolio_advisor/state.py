"""
Agent state definition for the workflow.
"""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """
    Global state for the Portfolio Rebalancing & Advisory Agent.
    
    This state flows through all nodes:
        START -> ingestion -> market_data -> strategy -> drafter -> compliance -> END
    
    Attributes:
        portfolio_text: Raw text/OCR from client's portfolio document
        macro_text: Raw text from macro research report
        risk_text: Raw text from client risk profile document
        market_prices_csv: Raw CSV content with current/last month prices
        parsed_data: Structured data extracted from inputs (portfolio + risk)
        market_context: Structured macro sentiment and indicators
        market_prices: Parsed price data from CSV
        calculated_returns: Monthly returns calculated from CSV
        validation: Portfolio validation results
        rebalancing_plan: Deterministic logic output with recommendations
        draft_letter: Initial LLM-generated advisory letter
        final_letter: Compliance-checked final output
    """
    
    # Inputs (provided at runtime)
    portfolio_text: str
    macro_text: str
    risk_text: str
    market_prices_csv: str
    
    # Node A outputs (Ingestion)
    parsed_data: dict
    market_context: dict
    validation: dict
    
    # Node A.5 outputs (Market Data)
    market_prices: list[dict]
    calculated_returns: list[dict]
    
    # Node B output (Strategy)
    rebalancing_plan: dict
    
    # Node C output (Drafter)
    draft_letter: str
    
    # Node D output (Compliance)
    final_letter: str
