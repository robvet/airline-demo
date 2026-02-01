"""Handoff callback functions for context hydration.

These callbacks run when an agent hands off to another agent,
ensuring the destination agent has the context data it needs.
"""
import random
import string

from agents import RunContextWrapper

from ..context import AirlineAgentChatContext
from ..demo_data import apply_itinerary_defaults


async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentChatContext]) -> None:
    """
    Ensure context is hydrated when handing off to the seat and special services agent.
    
    Generates confirmation number and flight number if not present,
    and applies default itinerary data.
    """
    apply_itinerary_defaults(context.context.state)
    if context.context.state.flight_number is None:
        context.context.state.flight_number = f"FLT-{random.randint(100, 999)}"
    if context.context.state.confirmation_number is None:
        context.context.state.confirmation_number = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )


async def on_booking_handoff(context: RunContextWrapper[AirlineAgentChatContext]) -> None:
    """
    Prepare context when handing off to booking and cancellation.
    
    Generates confirmation number and flight number if not present,
    and applies default itinerary data.
    """
    apply_itinerary_defaults(context.context.state)
    if context.context.state.confirmation_number is None:
        context.context.state.confirmation_number = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
    if context.context.state.flight_number is None:
        context.context.state.flight_number = f"FLT-{random.randint(100, 999)}"
