"""
Node C: Advisory Drafter (The Manager)

Generates a professional advisory letter in Portuguese using LLM.
"""

from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from ..config import settings
from ..prompts import ADVISORY_DRAFTER_SYSTEM, ADVISORY_DRAFTER_USER
from ..state import AgentState


_ACTION_LABELS = {
    "HARD_SELL": "[URGENTE] VENDA",
    "SOFT_SELL": "[MODERADO] REDUCAO",
    "TRIM": "[LUCRO] REALIZACAO",
}

_TABLE_ACTION_LABELS = {
    "HARD_SELL": "Venda Urgente",
    "SOFT_SELL": "Redução Moderada",
    "TRIM": "Realização de Lucro",
    "HOLD": "Manter",
}


def advisory_drafter(state: AgentState) -> dict:
    """
    Node C: Generate the advisory letter in Portuguese.
    
    Args:
        state: Current agent state with parsed_data, market_context, rebalancing_plan
        
    Returns:
        Dict with draft_letter
    """
    logger.info("Node C: Generating advisory letter")
    
    llm = ChatOpenAI(
        model=settings.llm.model,
        temperature=settings.llm.temperature_generation,
    )
    
    portfolio = state["parsed_data"]["portfolio"]
    risk = state["parsed_data"]["risk"]
    market = state["market_context"]
    plan = state["rebalancing_plan"]
    
    calculated_returns = state.get("calculated_returns", [])
    
    actions_text = _format_actions(plan["actions"])
    portfolio_table = _format_portfolio_table(
        portfolio["assets"], plan["actions"], calculated_returns
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ADVISORY_DRAFTER_SYSTEM),
        ("human", ADVISORY_DRAFTER_USER),
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "client_name": portfolio.get("client_name") or risk.get("client_name", "Cliente"),
        "profile_type": risk["profile_type"],
        "max_equity_pct": risk["max_equity_pct"],
        "drift_tolerance": risk["drift_tolerance"],
        "total_value": portfolio["total_value"],
        "equity_value": portfolio["equity_value"],
        "current_equity_pct": portfolio["equity_pct"],
        "house_view": market["house_view"],
        "ipca_2025": market["ipca_2025"],
        "ipca_2026": market["ipca_2026"],
        "selic_terminal": market["selic_terminal"],
        "gdp_growth": market.get("gdp_growth_2025") or "N/A",
        "exchange_rate": market.get("exchange_rate_eoy") or "N/A",
        "rebalance_needed": "Sim" if plan["rebalance_needed"] else "Nao",
        "summary": plan["summary"],
        "total_sell_value": plan["total_sell_value"],
        "actions_text": actions_text,
        "portfolio_table": portfolio_table,
        "current_date": datetime.now().strftime("%d de %B de %Y"),
    })
    
    logger.info("Node C: Letter generated")
    
    return {"draft_letter": response.content}


def _format_actions(actions: list[dict]) -> str:
    """Format rebalancing actions as text for the prompt."""
    if not actions:
        return "Nenhuma acao recomendada."
    
    lines = []
    counter = 0
    
    for action in actions:
        if action["action"] == "HOLD":
            continue
        
        counter += 1
        label = _ACTION_LABELS.get(action["action"], action["action"])
        
        lines.append(f"""
{counter}. **{action['ticker']}** - {label}
   - Valor Atual: R$ {action['current_value']:,.2f}
   - Vender: {action['size_pct']:.0f}% (R$ {action['suggested_sell_value']:,.2f})
   - Justificativa: {action['rationale']}
""")
    
    if not lines:
        return "Todas as posicoes dentro dos parametros. Manter alocacao atual."
    
    return "\n".join(lines)


def _format_portfolio_table(
    assets: list[dict],
    actions: list[dict],
    calculated_returns: list[dict],
) -> str:
    """
    Format a markdown table with all portfolio assets.

    Columns: Asset | Previous Price | Current Price | Value (BRL) | Performance (%) | Suggested Action

    Uses monthly returns from calculated_returns (CSV-based) when available,
    falls back to all-time return_pct from portfolio document.
    """
    # Build lookup maps
    action_map = {a["ticker"]: a["action"] for a in actions}
    returns_map = {cr["ticker"]: cr for cr in calculated_returns}

    lines = [
        "| Asset | Previous Price | Current Price | Value (BRL) | Performance (%) | Suggested Action |",
        "|:------|---------------:|-------------:|------------:|----------------:|:-----------------|",
    ]
    
    for asset in assets:
        ticker = asset.get("ticker", "N/A")
        value = asset.get("value", 0)
        
        # Get price data and return from calculated_returns
        calc_data = returns_map.get(ticker, {})
        last_price = calc_data.get("last_month_price")
        current_price = calc_data.get("current_price")
        return_pct = calc_data.get("monthly_return_pct")
        
        # Fallback to all-time return from document if no monthly data
        if return_pct is None:
            return_pct = asset.get("return_pct")
        
        # Format price strings
        last_price_str = f"R$ {last_price:,.2f}" if last_price is not None else "N/A"
        current_price_str = f"R$ {current_price:,.2f}" if current_price is not None else "N/A"
        perf_str = f"{return_pct:+.1f}%" if return_pct is not None else "N/A"
        
        action = action_map.get(ticker, "HOLD")
        action_label = _TABLE_ACTION_LABELS.get(action, "Manter")
        
        lines.append(
            f"| {ticker} | {last_price_str} | {current_price_str} | R$ {value:,.2f} | {perf_str} | {action_label} |"
        )
    
    return "\n".join(lines)
