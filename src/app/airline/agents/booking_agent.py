"""Booking & Cancellation Agent - Handles flight booking changes.

Manages new bookings, rebookings after delays/cancellations,
and flight cancellations with automatic seat assignment.
"""
from agents import Agent, RunContextWrapper

from ...azure_client import MODEL
from ..context import AirlineAgentChatContext
from ..guardrails import relevance_guardrail, jailbreak_guardrail
from ..prompts.loader import load_prompt
from ..tools import cancel_flight, get_matching_flights, book_new_flight

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


def booking_cancellation_instructions(
    run_context: RunContextWrapper[AirlineAgentChatContext], agent: Agent[AirlineAgentChatContext]
) -> str:
    """Load booking/cancellation prompt with context variables."""
    ctx = run_context.context.state
    return load_prompt("booking", {
        "RECOMMENDED_PROMPT_PREFIX": RECOMMENDED_PROMPT_PREFIX,
        "confirmation": ctx.confirmation_number or "[unknown]",
        "flight": ctx.flight_number or "[unknown]",
    })


# Create agent WITHOUT handoffs - wired in __init__.py to avoid circular imports
booking_cancellation_agent = Agent[AirlineAgentChatContext](
    name="Booking and Cancellation Agent",
    model=MODEL,
    handoff_description="Handles new bookings, rebookings after delays, and cancellations.",
    instructions=booking_cancellation_instructions,
    tools=[cancel_flight, get_matching_flights, book_new_flight],
    handoffs=[],  # Wired in __init__.py
    input_guardrails=[jailbreak_guardrail, relevance_guardrail],
)
