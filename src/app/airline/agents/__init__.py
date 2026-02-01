"""
Agents package - Specialized airline customer service agents.

This package contains all agent definitions and handles handoff wiring.

IMPORTANT: Handoffs are wired here (not in individual files) to avoid circular imports.
Individual agent files create agents with empty handoffs lists, then we wire them here
after all agents are imported.

Usage:
    from .airline.agents import triage_agent
    # triage_agent is now fully wired with all handoffs
"""
from agents import handoff

# Import all agents (created with empty handoffs)
from .triage_agent import triage_agent
from .faq_agent import faq_agent
from .seat_agent import seat_special_services_agent
from .flight_agent import flight_information_agent
from .booking_agent import booking_cancellation_agent
from .refund_agent import refunds_compensation_agent

# Import handoff callbacks
from .handoff_callbacks import on_seat_booking_handoff, on_booking_handoff


# =============================================================================
# HANDOFF WIRING
# =============================================================================
# This runs at import time, after all agents are created.
# The order matters for some operations, but extend/append are safe.

# Triage can hand off to all specialists
triage_agent.handoffs = [
    flight_information_agent,
    handoff(agent=booking_cancellation_agent, on_handoff=on_booking_handoff),
    handoff(agent=seat_special_services_agent, on_handoff=on_seat_booking_handoff),
    faq_agent,
    refunds_compensation_agent,
]

# FAQ can return to triage
faq_agent.handoffs.append(triage_agent)

# Seat services can hand off to refunds or return to triage
seat_special_services_agent.handoffs.extend([refunds_compensation_agent, triage_agent])

# Flight info can hand off to booking or return to triage
flight_information_agent.handoffs.extend([
    handoff(agent=booking_cancellation_agent, on_handoff=on_booking_handoff),
    triage_agent,
])

# Booking can hand off to seat services, refunds, or return to triage
booking_cancellation_agent.handoffs.extend([
    handoff(agent=seat_special_services_agent, on_handoff=on_seat_booking_handoff),
    refunds_compensation_agent,
    triage_agent,
])

# Refunds can consult FAQ or return to triage
refunds_compensation_agent.handoffs.extend([faq_agent, triage_agent])


# =============================================================================
# EXPORTS
# =============================================================================
__all__ = [
    # Agents
    "triage_agent",
    "faq_agent",
    "seat_special_services_agent",
    "flight_information_agent",
    "booking_cancellation_agent",
    "refunds_compensation_agent",
    # Callbacks (for reference/testing)
    "on_seat_booking_handoff",
    "on_booking_handoff",
]
