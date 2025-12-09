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
    
    actions_text = _format_actions(plan["actions"])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ADVISORY_DRAFTER_SYSTEM),
        ("human", ADVISORY_DRAFTER_USER),
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
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
