"""
Node B: Strategy Engine (The Algo)

Pure Python deterministic logic for portfolio rebalancing.
No LLM calls - strict rule-based decisions.

CRITICAL: Uses MONTHLY returns from CSV, NOT all-time returns from portfolio text.
"""

from loguru import logger

from ..config import settings
from ..models import RebalancingAction, RebalancingPlan
from ..state import AgentState


_ACTION_PRIORITY = {"HARD_SELL": 0, "SOFT_SELL": 1, "TRIM": 2, "HOLD": 3}


def strategy_engine(state: AgentState) -> dict:
    """
    Node B: Apply deterministic rebalancing rules.
    
    Uses monthly returns from calculated_returns (CSV-based) for decisions.
    This is different from using all-time returns in the portfolio text.
    
    Args:
        state: Current agent state with parsed_data, market_context, calculated_returns
        
    Returns:
        Dict with rebalancing_plan
    """
    logger.info("Node B: Running strategy engine")
    
    parsed_data = state["parsed_data"]
    market_context = state["market_context"]
    calculated_returns = state.get("calculated_returns", [])
    
    portfolio = parsed_data["portfolio"]
    risk = parsed_data["risk"]
    
    assets = portfolio["assets"]
    current_equity_pct = portfolio["equity_pct"]
    max_equity_pct = risk["max_equity_pct"]
    drift_tolerance = risk["drift_tolerance"]
    house_view = market_context["house_view"]
    
    monthly_returns_map = {
        cr["ticker"]: cr["monthly_return_pct"] 
        for cr in calculated_returns
    }
    
    threshold = max_equity_pct + drift_tolerance
    rebalance_needed = current_equity_pct > threshold
    
    if rebalance_needed:
        logger.info(f"  Allocation breach: {current_equity_pct:.1f}% > {threshold:.1f}%")
    
    actions = _apply_security_rules(assets, house_view, monthly_returns_map)
    
    total_sell_value = sum(a.suggested_sell_value for a in actions if a.action != "HOLD")
    actions.sort(key=lambda x: (_ACTION_PRIORITY.get(x.action, 99), -abs(x.size_pct)))
    
    summary = _build_summary(
        actions, total_sell_value, rebalance_needed,
        current_equity_pct, max_equity_pct, drift_tolerance
    )
    
    plan = RebalancingPlan(
        rebalance_needed=rebalance_needed,
        current_equity_pct=current_equity_pct,
        target_equity_pct=max_equity_pct,
        actions=actions,
        total_sell_value=total_sell_value,
        summary=summary,
    )
    
    actionable_count = sum(1 for a in actions if a.action != "HOLD")
    logger.info(f"Node B: Generated {actionable_count} actionable recommendations")
    
    return {"rebalancing_plan": plan.model_dump()}


def _apply_security_rules(
    assets: list[dict],
    house_view: str,
    monthly_returns_map: dict[str, float],
) -> list[RebalancingAction]:
    """
    Apply rebalancing rules to each asset.
    
    CRITICAL: Uses MONTHLY returns from CSV (monthly_returns_map),
    not all-time returns from the portfolio text.
    
    Examples:
    - LREN3 with +8.9% monthly return = HOLD (not HARD_SELL)
    - MRFG3 with -16.4% monthly return = may trigger SOFT_SELL
    """
    actions: list[RebalancingAction] = []
    rules = settings.rebalancing
    
    for asset in assets:
        ticker = asset["ticker"]
        value = asset["value"]
        asset_class = asset["asset_class"]
        
        if asset_class != "Stocks":
            continue
        
        monthly_return = monthly_returns_map.get(ticker)
        
        if monthly_return is None:
            logger.debug(f"    {ticker}: No monthly return data, skipping")
            continue
        
        action, size_pct, rationale = _evaluate_asset(monthly_return, house_view, rules)
        
        suggested_sell = value * (size_pct / 100) if size_pct > 0 else 0.0
        
        actions.append(RebalancingAction(
            ticker=ticker,
            action=action,
            size_pct=size_pct,
            current_value=value,
            suggested_sell_value=suggested_sell,
            rationale=f"{rationale} (Retorno mensal: {monthly_return:+.1f}%)",
        ))
        
        if action != "HOLD":
            logger.info(f"    {ticker}: {action} - Monthly return {monthly_return:+.1f}%")
    
    return actions


def _evaluate_asset(
    return_pct: float,
    house_view: str,
    rules: "settings.rebalancing.__class__",
) -> tuple[str, float, str]:
    """Evaluate a single asset against rebalancing rules."""
    
    if return_pct < rules.hard_sell.threshold:
        return "HARD_SELL", rules.hard_sell.size_pct, rules.hard_sell.rationale
    
    if return_pct > rules.trim.threshold:
        return "TRIM", rules.trim.size_pct, rules.trim.rationale
    
    if house_view == "Bearish" and return_pct < rules.soft_sell.threshold:
        return "SOFT_SELL", rules.soft_sell.size_pct, rules.soft_sell.rationale
    
    return "HOLD", 0.0, "Position within parameters. Keep current allocation."


def _build_summary(
    actions: list[RebalancingAction],
    total_sell_value: float,
    rebalance_needed: bool,
    current_equity_pct: float,
    max_equity_pct: float,
    drift_tolerance: float,
) -> str:
    """Build a summary of the rebalancing plan."""
    actionable = [a for a in actions if a.action != "HOLD"]
    
    if not actionable:
        summary = "No rebalancing actions needed at the moment."
    else:
        action_counts: dict[str, int] = {}
        for a in actionable:
            action_counts[a.action] = action_counts.get(a.action, 0) + 1
        
        parts = []
        if "HARD_SELL" in action_counts:
            parts.append(f"{action_counts['HARD_SELL']} urgent sell(s)")
        if "SOFT_SELL" in action_counts:
            parts.append(f"{action_counts['SOFT_SELL']} macro scenario reduction(s)")
        if "TRIM" in action_counts:
            parts.append(f"{action_counts['TRIM']} profit realization(s)")
        
        summary = f"Recommended rebalancing: {', '.join(parts)}. "
        summary += f"Total suggested sell value: R$ {total_sell_value:,.2f}"
    
    if rebalance_needed:
        warning = (
            f"[ALERT] Equity allocation ({current_equity_pct:.1f}%) "
            f"exceeds limit ({max_equity_pct:.1f}% + {drift_tolerance:.1f}% tolerance). "
        )
        summary = warning + summary
    
    return summary
