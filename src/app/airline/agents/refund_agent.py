"""Refunds & Compensation Agent - Handles disruption support.

Opens compensation cases and issues hotel/meal vouchers
for customers affected by delays or missed connections.
"""
from agents import Agent, RunContextWrapper

from ...azure_client import MODEL
from ..context import AirlineAgentChatContext
from ..guardrails import relevance_guardrail, jailbreak_guardrail
from ..prompts.loader import load_prompt
from ..tools import issue_compensation, faq_lookup_tool

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


def refunds_compensation_instructions(
    run_context: RunContextWrapper[AirlineAgentChatContext], agent: Agent[AirlineAgentChatContext]
) -> str:
    """Load refunds/compensation prompt with context variables."""
    ctx = run_context.context.state
    return load_prompt("refund", {
        "RECOMMENDED_PROMPT_PREFIX": RECOMMENDED_PROMPT_PREFIX,
        "confirmation": ctx.confirmation_number or "[unknown]",
        "case_id": ctx.compensation_case_id or "[not opened]",
    })


# Create agent WITHOUT handoffs - wired in __init__.py to avoid circular imports
refunds_compensation_agent = Agent[AirlineAgentChatContext](
    name="Refunds and Compensation Agent",
    model=MODEL,
    handoff_description="Opens compensation cases and issues hotel/meal support after delays.",
    instructions=refunds_compensation_instructions,
    tools=[issue_compensation, faq_lookup_tool],
    handoffs=[],  # Wired in __init__.py
    input_guardrails=[jailbreak_guardrail, relevance_guardrail],
)
