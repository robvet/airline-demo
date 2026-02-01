"""Flight Information Agent - Provides flight status and connection impact.

Checks flight status, identifies connection risks from delays,
and proposes alternate flight options when disruptions occur.
"""
from agents import Agent, RunContextWrapper

from ...azure_client import MODEL
from ..context import AirlineAgentChatContext
from ..guardrails import relevance_guardrail, jailbreak_guardrail
from ..prompts.loader import load_prompt
from ..tools import flight_status_tool, get_matching_flights

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


def flight_information_instructions(
    run_context: RunContextWrapper[AirlineAgentChatContext], agent: Agent[AirlineAgentChatContext]
) -> str:
    """Load flight information prompt with context variables."""
    ctx = run_context.context.state
    return load_prompt("flight_info", {
        "RECOMMENDED_PROMPT_PREFIX": RECOMMENDED_PROMPT_PREFIX,
        "confirmation": ctx.confirmation_number or "[unknown]",
        "flight": ctx.flight_number or "[unknown]",
    })


# Create agent WITHOUT handoffs - wired in __init__.py to avoid circular imports
flight_information_agent = Agent[AirlineAgentChatContext](
    name="Flight Information Agent",
    model=MODEL,
    handoff_description="Provides flight status, connection impact, and alternate options.",
    instructions=flight_information_instructions,
    tools=[flight_status_tool, get_matching_flights],
    handoffs=[],  # Wired in __init__.py
    input_guardrails=[jailbreak_guardrail, relevance_guardrail],
)
