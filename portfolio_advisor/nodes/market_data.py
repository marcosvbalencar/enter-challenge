"""
Node A.5: Market Data Processing

Parses the profitability CSV and calculates monthly returns.
Cross-references with portfolio assets to get position-weighted returns.

This replicates the Rivet project logic:
- Code node 4m2DBSh1nKLPG7xue7-Ek: Return calculation
- Cross-references market_data with portfolio_text
"""

import csv
from io import StringIO

from loguru import logger

from ..models import MarketPrice, CalculatedReturn
from ..state import AgentState


def market_data_node(state: AgentState) -> dict:
    """
    Node A.5: Parse CSV and calculate monthly returns.
    
    Replicates Rivet's Code node logic:
    - Parse CSV with current_price and last_month_price
    - Cross-reference with portfolio assets
    - Calculate: ((current - last) / last) * 100
    
    Args:
        state: Current agent state with market_prices_csv and parsed_data
        
    Returns:
        Dict with market_prices and calculated_returns
    """
    logger.info("Node A.5: Processing market data")
    
    csv_content = state.get("market_prices_csv", "")
    parsed_data = state.get("parsed_data", {})
    portfolio = parsed_data.get("portfolio", {})
    assets = portfolio.get("assets", [])
    
    market_prices = _parse_csv(csv_content)
    logger.info(f"  Parsed {len(market_prices)} price records from CSV")
    
    calculated_returns = _calculate_returns(market_prices, assets)
    logger.info(f"  Calculated returns for {len(calculated_returns)} portfolio assets")
    
    logger.info("Node A.5: Market data processing complete")
    
    return {
        "market_prices": [mp.model_dump() for mp in market_prices],
        "calculated_returns": [cr.model_dump() for cr in calculated_returns],
    }


def _parse_csv(csv_content: str) -> list[MarketPrice]:
    """
    Parse the profitability CSV content.
    
    Expected columns: Asset class, Asset, Current price, Last month price
    """
    if not csv_content or not csv_content.strip():
        logger.warning("  Empty CSV content, returning empty list")
        return []
    
    prices: list[MarketPrice] = []
    
    reader = csv.DictReader(StringIO(csv_content))
    
    for row in reader:
        try:
            asset_class = row.get("Asset class", "").strip()
            ticker = row.get("Asset", "").strip()
            current_str = row.get("Current price", "0").strip()
            last_str = row.get("Last month price", "0").strip()
            
            if not ticker:
                continue
            
            current_price = float(current_str) if current_str else 0.0
            last_month_price = float(last_str) if last_str else 0.0
            
            prices.append(MarketPrice(
                asset_class=asset_class,
                ticker=ticker,
                current_price=current_price,
                last_month_price=last_month_price,
            ))
            
        except (ValueError, KeyError) as e:
            logger.warning(f"  Skipping invalid CSV row: {e}")
            continue
    
    return prices


def _calculate_returns(
    market_prices: list[MarketPrice],
    portfolio_assets: list[dict],
) -> list[CalculatedReturn]:
    """
    Calculate monthly returns by cross-referencing market prices with portfolio.
    
    This replicates the Rivet Code node logic:
    monthly_return = ((current_price - last_month_price) / last_month_price) * 100
    """
    price_lookup = {mp.ticker: mp for mp in market_prices}
    
    returns: list[CalculatedReturn] = []
    
    for asset in portfolio_assets:
        ticker = asset.get("ticker", "")
        position_value = asset.get("value", 0.0)
        
        if ticker not in price_lookup:
            continue
        
        mp = price_lookup[ticker]
        
        if mp.last_month_price and mp.last_month_price != 0:
            monthly_return = (
                (mp.current_price - mp.last_month_price) / mp.last_month_price
            ) * 100
        else:
            monthly_return = 0.0
        
        returns.append(CalculatedReturn(
            ticker=ticker,
            current_price=mp.current_price,
            last_month_price=mp.last_month_price,
            monthly_return_pct=round(monthly_return, 2),
            position_value=position_value,
        ))
        
        logger.debug(
            f"    {ticker}: {mp.last_month_price:.2f} -> {mp.current_price:.2f} "
            f"= {monthly_return:+.2f}%"
        )
    
    return returns

