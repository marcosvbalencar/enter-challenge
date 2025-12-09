"""
Portfolio Rebalancing & Advisory Agent - Entry Point

Run with: python -m portfolio_advisor.main
"""

import os
import sys

from dotenv import load_dotenv
from loguru import logger


def main() -> int:
    """
    Run the Portfolio Advisory workflow.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    load_dotenv()
    
    from .config import settings
    from .graph import app
    from .pdf_export import export_letter_to_pdf
    from .utils import read_text_file
    
    logger.info("=" * 60)
    logger.info("Portfolio Rebalancing & Advisory Agent")
    logger.info("=" * 60)
    
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not found in environment")
        logger.error("Set it in .env file or: export OPENAI_API_KEY='your-key'")
        return 1
    
    try:
        logger.info(f"Loading data from: {settings.paths.portfolio.parent}")
        
        portfolio_text = read_text_file(settings.paths.portfolio)
        logger.info(f"  [OK] Portfolio: {settings.paths.portfolio.name}")
        
        macro_text = read_text_file(settings.paths.macro)
        logger.info(f"  [OK] Macro: {settings.paths.macro.name}")
        
        risk_text = read_text_file(settings.paths.risk)
        logger.info(f"  [OK] Risk: {settings.paths.risk.name}")
        
        market_prices_csv = read_text_file(settings.paths.profitability_csv)
        logger.info(f"  [OK] Market Prices CSV: {settings.paths.profitability_csv.name}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except IOError as e:
        logger.error(f"Failed to read file: {e}")
        return 1
    
    logger.info("Running workflow...")
    
    inputs = {
        "portfolio_text": portfolio_text,
        "macro_text": macro_text,
        "risk_text": risk_text,
        "market_prices_csv": market_prices_csv,
    }
    
    try:
        result = app.invoke(inputs)
    except Exception as e:
        logger.exception(f"Workflow failed: {e}")
        return 1
    
    _print_results(result)
    
    # Export PDF
    pdf_path = export_letter_to_pdf(result["final_letter"])
    logger.info(f"✅ PDF exported: {pdf_path}")
    
    return 0


def _print_results(result: dict) -> None:
    """Print formatted results to console."""
    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    
    portfolio = result["parsed_data"]["portfolio"]
    print(f"""
PORTFOLIO SUMMARY
  Total Value:    R$ {portfolio['total_value']:,.2f}
  Equity Value:   R$ {portfolio['equity_value']:,.2f}
  Equity %:       {portfolio['equity_pct']:.1f}%
  Fixed Income %: {portfolio.get('fixed_income_pct', 0):.1f}%
  Assets:         {len(portfolio['assets'])}
""")
    
    calculated_returns = result.get("calculated_returns", [])
    if calculated_returns:
        print("MONTHLY RETURNS (from CSV):")
        for cr in calculated_returns:
            print(f"  {cr['ticker']}: {cr['monthly_return_pct']:+.2f}% "
                  f"(R$ {cr['last_month_price']:.2f} -> R$ {cr['current_price']:.2f})")
        print()
    
    risk = result["parsed_data"]["risk"]
    print(f"""RISK PROFILE
  Type:           {risk['profile_type']}
  Max Equity:     {risk['max_equity_pct']:.1f}%
  Drift Tolerance: {risk['drift_tolerance']:.1f}%
""")
    
    market = result["market_context"]
    print(f"""MARKET CONTEXT
  House View:     {market['house_view']}
  IPCA 2025:      {market['ipca_2025']:.1f}%
  IPCA 2026:      {market['ipca_2026']:.1f}%
  SELIC Terminal: {market['selic_terminal']:.1f}%
""")
    
    plan = result["rebalancing_plan"]
    print(f"""REBALANCING PLAN
  Needed:     {'Yes' if plan['rebalance_needed'] else 'No'}
  Current:    {plan['current_equity_pct']:.1f}%
  Target:     {plan['target_equity_pct']:.1f}%
  Total Sell: R$ {plan['total_sell_value']:,.2f}
  
  Summary: {plan['summary']}
""")
    
    actionable = [a for a in plan["actions"] if a["action"] != "HOLD"]
    if actionable:
        print("  Actions:")
        for action in actionable:
            print(f"    - {action['ticker']}: {action['action']} ({action['size_pct']:.0f}%)")
            print(f"      Sell: R$ {action['suggested_sell_value']:,.2f}")
    
    print("\n" + "=" * 60)
    print("FINAL ADVISORY LETTER")
    print("=" * 60 + "\n")
    print(result["final_letter"])


if __name__ == "__main__":
    sys.exit(main())
