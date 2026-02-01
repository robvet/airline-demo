"""Seat & Special Services Agent - Handles seat changes and accessibility requests.

Manages seat updates, special service accommodations (medical, accessibility),
and provides the interactive seat map for visual selection.
"""
from agents import Agent, RunContextWrapper

from ...azure_client import MODEL
from ..context import AirlineAgentChatContext
from ..guardrails import relevance_guardrail, jailbreak_guardrail
from ..prompts.loader import load_prompt
from ..tools import update_seat, assign_special_service_seat, display_seat_map

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


def seat_services_instructions(
    run_context: RunContextWrapper[AirlineAgentChatContext], agent: Agent[AirlineAgentChatContext]
) -> str:
    """Load seat services prompt with context variables."""
    ctx = run_context.context.state
    return load_prompt("seat_services", {
        "RECOMMENDED_PROMPT_PREFIX": RECOMMENDED_PROMPT_PREFIX,
        "confirmation": ctx.confirmation_number or "[unknown]",
        "flight": ctx.flight_number or "[unknown]",
        "seat": ctx.seat_number or "[unassigned]",
    })


# Create agent WITHOUT handoffs - wired in __init__.py to avoid circular imports
seat_special_services_agent = Agent[AirlineAgentChatContext](
    name="Seat and Special Services Agent",
    model=MODEL,
    handoff_description="Updates seats and handles medical or special service seating.",
    instructions=seat_services_instructions,
    tools=[update_seat, assign_special_service_seat, display_seat_map],
    handoffs=[],  # Wired in __init__.py
    input_guardrails=[jailbreak_guardrail, relevance_guardrail],
)
