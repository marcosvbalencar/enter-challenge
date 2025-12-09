"""
LangGraph workflow assembly.

Defines the Portfolio Rebalancing & Advisory Agent workflow:
    START -> ingestion -> market_data -> strategy -> drafter -> compliance -> END

Matches the Rivet project flow:
- Node A: Ingestion (parse portfolio, macro, risk texts)
- Node A.5: Market Data (parse CSV, calculate monthly returns)
- Node B: Strategy (apply rebalancing rules using monthly returns)
- Node C: Drafter (generate advisory letter)
- Node D: Compliance (audit and fix letter)
"""

from langgraph.graph import StateGraph, START, END
from loguru import logger

from .state import AgentState
from .nodes import (
    ingestion_node,
    market_data_node,
    strategy_engine,
    advisory_drafter,
    compliance_gatekeeper,
)


def create_graph() -> StateGraph:
    """
    Create and compile the Portfolio Advisory graph.
    
    Returns:
        Compiled LangGraph application
    """
    logger.info("Building workflow graph...")
    
    graph = StateGraph(AgentState)
    
    graph.add_node("ingestion", ingestion_node)
    graph.add_node("market_data", market_data_node)
    graph.add_node("strategy", strategy_engine)
    graph.add_node("drafter", advisory_drafter)
    graph.add_node("compliance", compliance_gatekeeper)
    
    graph.add_edge(START, "ingestion")
    graph.add_edge("ingestion", "market_data")
    graph.add_edge("market_data", "strategy")
    graph.add_edge("strategy", "drafter")
    graph.add_edge("drafter", "compliance")
    graph.add_edge("compliance", END)
    
    compiled = graph.compile()
    
    logger.info("Workflow graph compiled successfully")
    
    return compiled


def run_advisory(
    portfolio_text: str,
    macro_text: str,
    risk_text: str,
    market_prices_csv: str = "",
) -> dict:
    """
    Run the complete advisory workflow.
    
    Args:
        portfolio_text: Raw text from client's portfolio document
        macro_text: Raw text from macro research report
        risk_text: Raw text from client's risk profile document
        market_prices_csv: CSV content with current/last month prices
    
    Returns:
        Complete state dict including 'final_letter'
    """
    inputs = {
        "portfolio_text": portfolio_text,
        "macro_text": macro_text,
        "risk_text": risk_text,
        "market_prices_csv": market_prices_csv,
    }
    
    return app.invoke(inputs)


app = create_graph()
