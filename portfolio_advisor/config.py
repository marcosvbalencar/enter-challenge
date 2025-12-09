"""
Configuration and settings for the Portfolio Advisory Agent.

Uses Pydantic Settings for type-safe configuration management.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# =============================================================================
# Path Configuration
# =============================================================================

ROOT_DIR: Path = Path(__file__).parent
DATA_DIR: Path = ROOT_DIR / "data"


class DataPaths(BaseModel):
    """Data file paths configuration."""
    
    portfolio: Path = DATA_DIR / "XP - Albert_s portfolio.txt"
    macro: Path = DATA_DIR / "XP - Macro analysis.txt"
    risk: Path = DATA_DIR / "XP - Albert_s risk profile.txt"
    profitability_csv: Path = DATA_DIR / "profitability_calc_wip.csv"


# =============================================================================
# LLM Configuration
# =============================================================================

class LLMSettings(BaseModel):
    """LLM model and temperature settings."""
    
    model: str = "gpt-4o"
    temperature_extraction: float = 0.0
    temperature_generation: float = 0.3
    temperature_compliance: float = 0.2


# =============================================================================
# Risk Profile Configuration
# =============================================================================

class RiskDefaults(BaseModel):
    """Default values for risk profile settings."""
    
    equity_limits: dict[str, float] = Field(
        default={
            "Conservative": 20.0,
            "Moderate": 40.0,
            "Aggressive": 70.0,
        }
    )
    drift_tolerance: float = 5.0


# =============================================================================
# Rebalancing Rules Configuration
# =============================================================================

class RebalancingRule(BaseModel):
    """Configuration for a single rebalancing rule."""
    
    threshold: float
    size_pct: float
    rationale: str


class RebalancingRulesConfig(BaseModel):
    """Configuration for all rebalancing rules."""
    
    hard_sell: RebalancingRule = RebalancingRule(
        threshold=-20.0,
        size_pct=50.0,
        rationale=(
            "Ativo com perda superior a 20%. "
            "Recomendacao de venda parcial para protecao do capital."
        ),
    )
    trim: RebalancingRule = RebalancingRule(
        threshold=25.0,
        size_pct=25.0,
        rationale=(
            "Ativo com valorizacao expressiva (+25%). "
            "Recomendacao de realizacao parcial de lucros."
        ),
    )
    soft_sell: RebalancingRule = RebalancingRule(
        threshold=-10.0,
        size_pct=30.0,
        rationale=(
            "Cenario macro desfavoravel combinado com desempenho negativo. "
            "Recomendacao de reducao da posicao."
        ),
    )


# =============================================================================
# Compliance Configuration
# =============================================================================

class ComplianceConfig(BaseModel):
    """Compliance rules configuration."""
    
    forbidden_terms: tuple[str, ...] = (
        "garantido",
        "garantia",
        "sem risco",
        "risco zero",
        "retorno certo",
        "retorno garantido",
        "lucro certo",
        "investimento seguro",
        "rentabilidade garantida",
        "nao ha risco",
        "livre de risco",
    )



# =============================================================================
# Main Settings Class
# =============================================================================

class Settings(BaseSettings):
    """
    Main application settings.
    
    Loads configuration from environment variables with PORTFOLIO_ prefix.
    """
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # Sub-configurations
    paths: DataPaths = Field(default_factory=DataPaths)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    risk_defaults: RiskDefaults = Field(default_factory=RiskDefaults)
    rebalancing: RebalancingRulesConfig = Field(default_factory=RebalancingRulesConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)
    
    class Config:
        env_prefix = "PORTFOLIO_"
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()
