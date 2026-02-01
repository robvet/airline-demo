"""Agent definitions for the airline customer service demo.

This module defines all specialist agents and their handoff relationships.
Prompts are loaded from external template files in the prompts/ folder.
"""
from __future__ import annotations as _annotations

import random
import string

from agents import Agent, RunContextWrapper, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from ..azure_client import MODEL
from .context import AirlineAgentChatContext
from .demo_data import apply_itinerary_defaults
from .guardrails import jailbreak_guardrail, relevance_guardrail
from .prompts.loader import load_prompt
from .tools import (
    assign_special_service_seat,
    book_new_flight,
    cancel_flight,
    display_seat_map,
    faq_lookup_tool,
    flight_status_tool,
    get_matching_flights,
    get_trip_details,
    issue_compensation,
    update_seat,
)


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


seat_special_services_agent = Agent[AirlineAgentChatContext](
    name="Seat and Special Services Agent",
    model=MODEL,
    handoff_description="Updates seats and handles medical or special service seating.",
    instructions=seat_services_instructions,
    tools=[update_seat, assign_special_service_seat, display_seat_map],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


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


flight_information_agent = Agent[AirlineAgentChatContext](
    name="Flight Information Agent",
    model=MODEL,
    handoff_description="Provides flight status, connection impact, and alternate options.",
    instructions=flight_information_instructions,
    tools=[flight_status_tool, get_matching_flights],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


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


booking_cancellation_agent = Agent[AirlineAgentChatContext](
    name="Booking and Cancellation Agent",
    model=MODEL,
    handoff_description="Handles new bookings, rebookings after delays, and cancellations.",
    instructions=booking_cancellation_instructions,
    tools=[cancel_flight, get_matching_flights, book_new_flight],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


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


refunds_compensation_agent = Agent[AirlineAgentChatContext](
    name="Refunds and Compensation Agent",
    model=MODEL,
    handoff_description="Opens compensation cases and issues hotel/meal support after delays.",
    instructions=refunds_compensation_instructions,
    tools=[issue_compensation, faq_lookup_tool],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


faq_agent = Agent[AirlineAgentChatContext](
    name="FAQ Agent",
    model=MODEL,
    handoff_description="Answers common questions about policies, baggage, seats, and compensation.",
    instructions=load_prompt("faq", {"RECOMMENDED_PROMPT_PREFIX": RECOMMENDED_PROMPT_PREFIX}),
    tools=[faq_lookup_tool],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


triage_agent = Agent[AirlineAgentChatContext](
    name="Triage Agent",
    model=MODEL,
    handoff_description="Delegates requests to the right specialist agent (flight info, booking, seats, FAQ, baggage, compensation).",
    instructions=load_prompt("triage", {"RECOMMENDED_PROMPT_PREFIX": RECOMMENDED_PROMPT_PREFIX}),
    tools=[get_trip_details],
    handoffs=[],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentChatContext]) -> None:
    """Ensure context is hydrated when handing off to the seat and special services agent."""
    apply_itinerary_defaults(context.context.state)
    if context.context.state.flight_number is None:
        context.context.state.flight_number = f"FLT-{random.randint(100, 999)}"
    if context.context.state.confirmation_number is None:
        context.context.state.confirmation_number = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )


async def on_booking_handoff(
    context: RunContextWrapper[AirlineAgentChatContext]
) -> None:
    """Prepare context when handing off to booking and cancellation."""
    apply_itinerary_defaults(context.context.state)
    if context.context.state.confirmation_number is None:
        context.context.state.confirmation_number = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
    if context.context.state.flight_number is None:
        context.context.state.flight_number = f"FLT-{random.randint(100, 999)}"


# Set up handoff relationships
triage_agent.handoffs = [
    flight_information_agent,
    handoff(agent=booking_cancellation_agent, on_handoff=on_booking_handoff),
    handoff(agent=seat_special_services_agent, on_handoff=on_seat_booking_handoff),
    faq_agent,
    refunds_compensation_agent,
]
faq_agent.handoffs.append(triage_agent)
seat_special_services_agent.handoffs.extend([refunds_compensation_agent, triage_agent])
flight_information_agent.handoffs.extend(
    [
        handoff(agent=booking_cancellation_agent, on_handoff=on_booking_handoff),
        triage_agent,
    ]
)
booking_cancellation_agent.handoffs.extend(
    [
        handoff(agent=seat_special_services_agent, on_handoff=on_seat_booking_handoff),
        refunds_compensation_agent,
        triage_agent,
    ]
)
refunds_compensation_agent.handoffs.extend([faq_agent, triage_agent])
