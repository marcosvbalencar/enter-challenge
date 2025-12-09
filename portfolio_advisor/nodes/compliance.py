"""
Node D: Compliance Gatekeeper (The Auditor)

Audits the draft letter for regulatory compliance and accuracy.
"""

import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from ..config import settings
from ..models import ComplianceIssue, ComplianceReport
from ..prompts import COMPLIANCE_REWRITE_SYSTEM, COMPLIANCE_REWRITE_USER
from ..state import AgentState
from ..utils import get_text_context


_SUSPICIOUS_PATTERNS = (
    r"we recommend (holding|keeping)",
    r"guaranteed investment",
    r"guaranteed return",
    r"certain profit",
    r"there are no risks",
    r"guaranteed earnings",
    r"assured growth",
    r"we strongly recommend",
    r"it's impossible to lose",
    r"(very|extremely|extraordinary) high return",
    r"we recommend (betting|risking)",
)


def compliance_gatekeeper(state: AgentState) -> dict:
    """
    Node D: Audit and correct the draft letter.
    
    Args:
        state: Current agent state with draft_letter and rebalancing_plan
        
    Returns:
        Dict with final_letter
    """
    logger.info("Node D: Running compliance check")
    
    draft = state["draft_letter"]
    plan = state["rebalancing_plan"]
    
    all_issues: list[ComplianceIssue] = []
    
    logger.info("  Checking forbidden terms...")
    all_issues.extend(_check_forbidden_terms(draft))
    
    logger.info("  Checking for hallucinations...")
    all_issues.extend(_check_hallucinations(draft, plan))
    
    if all_issues:
        logger.warning(f"  Found {len(all_issues)} compliance issues, rewriting...")
        final_letter = _rewrite_letter(draft, all_issues, plan)
        
        remaining = _check_forbidden_terms(final_letter)
        if remaining:
            logger.warning("  Removing remaining forbidden terms...")
            final_letter = _force_remove_forbidden_terms(final_letter)
    else:
        logger.info("  No compliance issues found")
        final_letter = draft
    
    ComplianceReport(
        passed=len(all_issues) == 0,
        issues=all_issues,
        corrections_made=len(all_issues),
    )
    
    final_letter = final_letter.strip()
    
    logger.info("Node D: Compliance check complete")
    
    return {"final_letter": final_letter}


def _check_forbidden_terms(letter: str) -> list[ComplianceIssue]:
    """Check for forbidden regulatory terms."""
    issues = []
    letter_lower = letter.lower()
    
    for term in settings.compliance.forbidden_terms:
        if term in letter_lower:
            context = get_text_context(letter, term, 30)
            issues.append(ComplianceIssue(
                issue_type="FORBIDDEN_TERM",
                description=f"Forbidden term found: '{term}'",
                original_text=f"...{context}..." if context else None,
                suggested_fix=f"Remove or replace the term '{term}'",
            ))
    
    return issues


def _check_hallucinations(letter: str, plan: dict) -> list[ComplianceIssue]:
    """Verify that recommendations match the rebalancing plan."""
    issues = []
    letter_lower = letter.lower()
    
    for pattern in _SUSPICIOUS_PATTERNS:
        match = re.search(pattern, letter_lower)
        if match:
            issues.append(ComplianceIssue(
                issue_type="HALLUCINATION",
                description="Buy recommendation detected in rebalancing context",
                original_text=match.group(0),
                suggested_fix="Remove buy recommendations",
            ))
    
    planned_tickers = {
        a["ticker"].lower()
        for a in plan["actions"]
        if a["action"] != "HOLD"
    }
    
    mentioned_tickers = set(re.findall(r"\b([A-Z]{4}[0-9]{1,2})\b", letter))
    # Portuguese action words to detect sell recommendations in the letter
    action_words = ("vender", "venda", "reduzir", "realizar", "liquidar")
    
    for ticker in mentioned_tickers:
        if ticker.lower() not in planned_tickers:
            context = get_text_context(letter, ticker, 100)
            if any(word in context.lower() for word in action_words):
                issues.append(ComplianceIssue(
                    issue_type="HALLUCINATION",
                    description=f"Suggested action for {ticker} is not in the plan",
                    original_text=context[:100] if context else None,
                    suggested_fix=f"Remove recommendation for {ticker}",
                ))
    
    return issues


def _rewrite_letter(
    letter: str,
    issues: list[ComplianceIssue],
    plan: dict,
) -> str:
    """Use LLM to rewrite the letter fixing compliance issues."""
    llm = ChatOpenAI(
        model=settings.llm.model,
        temperature=settings.llm.temperature_compliance,
    )
    
    issues_text = "\n".join(
        f"- {issue.issue_type}: {issue.description}"
        for issue in issues
    )
    
    actions_summary = "\n".join(
        f"- {a['ticker']}: {a['action']} - sell {a['size_pct']:.0f}% "
        f"(R$ {a['suggested_sell_value']:,.2f})"
        for a in plan["actions"]
        if a["action"] != "HOLD"
    ) or "No sell actions recommended."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", COMPLIANCE_REWRITE_SYSTEM),
        ("human", COMPLIANCE_REWRITE_USER),
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "issues": issues_text,
        "total_sell_value": plan["total_sell_value"],
        "actions_summary": actions_summary,
        "letter": letter,
    })
    
    return response.content


def _force_remove_forbidden_terms(letter: str) -> str:
    """Force remove any remaining forbidden terms."""
    result = letter
    for term in settings.compliance.forbidden_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        result = pattern.sub("[TERM REMOVED]", result)
    return result
