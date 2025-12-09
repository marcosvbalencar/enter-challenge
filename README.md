# PoC - AI Financial Advisor

An AI-powered agent built with **LangGraph** that analyzes investment portfolios, applies rebalancing rules based on risk profiles and market conditions, and generates compliance-checked advisory letters.

## Overview

This agent implements a multi-node workflow that:

1. **Ingests** portfolio data, risk profiles, and macro analysis documents
2. **Calculates** monthly returns from market price data
3. **Applies** deterministic rebalancing rules based on performance thresholds
4. **Drafts** personalized advisory letters in Portuguese
5. **Validates** regulatory compliance

```
START → Ingestion → Market Data → Strategy → Drafter → Compliance → END
```

## Features

- **LLM-powered extraction**: Uses GPT-4o to parse unstructured portfolio and risk profile documents
- **Deterministic strategy engine**: Rule-based rebalancing with configurable thresholds
- **Monthly return calculation**: Processes CSV data for performance-based decisions
- **Compliance gatekeeper**: Automatically removes forbidden terms and adds regulatory disclaimers
- **Type-safe configuration**: Pydantic-based settings management

## Requirements

- Python 3.11+
- OpenAI API key

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/enter-challenge.git
cd enter-challenge
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r portfolio_advisor/requirements.txt
# or install as package
pip install -e portfolio_advisor/
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Or set directly:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

### Run the agent

```bash
python -m portfolio_advisor.main
```

Or if installed as a package:
```bash
portfolio-advisor
```

### Programmatic usage

```python
from portfolio_advisor.graph import run_advisory

result = run_advisory(
    portfolio_text="...",  # Portfolio document content
    macro_text="...",       # Macro analysis content
    risk_text="...",        # Risk profile content
    market_prices_csv="..." # CSV with price data
)

print(result["final_letter"])
```

## Project Structure

```
portfolio_advisor/
├── __init__.py
├── main.py           # Entry point
├── graph.py          # LangGraph workflow assembly
├── state.py          # Agent state definition
├── config.py         # Pydantic settings
├── models.py         # Data models for LLM extraction
├── prompts.py        # System/user prompts for each node
├── utils.py          # Helper functions
├── nodes/
│   ├── __init__.py
│   ├── ingestion.py  # Node A: Parse documents
│   ├── market_data.py# Node A.5: Calculate returns
│   ├── strategy.py   # Node B: Rebalancing rules
│   ├── drafter.py    # Node C: Generate letter
│   └── compliance.py # Node D: Audit & fix
└── data/
    ├── XP - Albert_s portfolio.txt
    ├── XP - Albert_s risk profile.txt
    ├── XP - Macro analysis.txt
    └── profitability_calc_wip.csv
```

## Workflow Nodes

### Node A: Ingestion
Parses raw text documents using structured LLM extraction:
- Portfolio: asset holdings, values, allocations
- Risk Profile: investor type, equity limits, drift tolerance
- Macro: house view, inflation expectations, interest rate projections

### Node A.5: Market Data
Processes CSV with price data to calculate monthly returns per asset.

### Node B: Strategy Engine
Applies deterministic rebalancing rules:
| Rule | Threshold | Action |
|------|-----------|--------|
| Hard Sell | < -20% | Sell 50% |
| Trim | > +25% | Sell 25% |
| Soft Sell | < -10% (+ negative macro) | Sell 30% |

### Node C: Advisory Drafter
Generates personalized advisory letters using LLM with:
- Client context and risk profile
- Specific recommendations with rationale
- Portuguese language output

### Node D: Compliance Gatekeeper
- Removes forbidden terms ("guaranteed", "risk-free", etc.)
- Adds regulatory disclaimer
- Validates against regularoty guidelines

## Configuration

All settings can be customized via environment variables with `PORTFOLIO_` prefix:

```bash
PORTFOLIO_LOG_LEVEL=DEBUG
PORTFOLIO_LLM__MODEL=gpt-4o
PORTFOLIO_LLM__TEMPERATURE_EXTRACTION=0.0
```

Or modify `config.py` directly.

## Sample Output

```
PORTFOLIO SUMMARY
  Total Value:    R$ 1,234,567.89
  Equity Value:   R$ 456,789.00
  Equity %:       37.0%
  Assets:         12

REBALANCING PLAN
  Needed:     Yes
  Current:    37.0%
  Target:     35.0%
  Total Sell: R$ 24,567.00
  
  Actions:
    - PETR4: TRIM (25%)
      Sell: R$ 12,345.00

FINAL ADVISORY LETTER
============================================================
Prezado Albert,
...
```

## License

MIT
