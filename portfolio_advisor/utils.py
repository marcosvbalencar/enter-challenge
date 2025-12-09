"""
Utility functions for the Portfolio Advisory Agent.
"""

import re
import sys
from pathlib import Path

from loguru import logger


# =============================================================================
# Logging Configuration
# =============================================================================

def configure_logger(level: str = "INFO") -> None:
    """
    Configure loguru logger for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}",
        level=level,
        colorize=True,
    )


# Configure on import
configure_logger()


# =============================================================================
# Currency Parsing
# =============================================================================

def parse_brl_currency(value_str: str) -> float:
    """
    Parse Brazilian currency format to float.
    
    Handles both Brazilian (1.000,50) and American (1,000.50) formats.
    
    Args:
        value_str: Currency string (e.g., "R$ 1.000,00")
        
    Returns:
        Parsed float value
        
    Examples:
        >>> parse_brl_currency("R$ 1.000,00")
        1000.0
        >>> parse_brl_currency("R$386,858.82")
        386858.82
    """
    if not value_str:
        return 0.0
    
    cleaned = re.sub(r"R\$\s*", "", str(value_str)).strip()
    
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def format_brl_currency(value: float) -> str:
    """
    Format a float as Brazilian currency.
    
    Args:
        value: Numeric value
        
    Returns:
        Formatted string (e.g., "R$ 1.000,00")
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =============================================================================
# File Operations
# =============================================================================

def read_text_file(file_path: Path) -> str:
    """
    Read a text file and return its contents.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File contents as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to read file {file_path}: {e}") from e


def get_text_context(text: str, term: str, context_size: int = 50) -> str:
    """
    Get surrounding context for a term in text.
    
    Args:
        text: Full text to search
        term: Term to find
        context_size: Characters before/after to include
        
    Returns:
        Context string or empty if not found
    """
    idx = text.upper().find(term.upper())
    if idx == -1:
        return ""
    
    start = max(0, idx - context_size)
    end = min(len(text), idx + len(term) + context_size)
    return text[start:end]


# =============================================================================
# Validation Helpers
# =============================================================================

def normalize_profile_type(profile: str) -> str:
    """
    Normalize risk profile type to standard format.
    
    Args:
        profile: Raw profile string (can be Portuguese)
        
    Returns:
        Normalized profile: "Conservative", "Moderate", or "Aggressive"
    """
    profile_map = {
        "conservative": "Conservative",
        "moderate": "Moderate",
        "aggressive": "Aggressive"
    }
    return profile_map.get(profile.lower().strip(), "Moderate")


def normalize_house_view(view: str, macro_text: str = "") -> str:
    """
    Normalize house view to standard format.
    
    Args:
        view: Raw view string
        macro_text: Original macro text for context clues
        
    Returns:
        Normalized view: "Bullish", "Bearish", or "Neutral"
    """
    view_clean = view.strip().title()
    
    if view_clean in ("Bullish", "Bearish", "Neutral"):
        return view_clean
    
    bearish_indicators = ("slipping", "thin ice", "worried", "risk", "uncertainty")
    if any(term in macro_text.lower() for term in bearish_indicators):
        return "Bearish"
    
    return "Neutral"
