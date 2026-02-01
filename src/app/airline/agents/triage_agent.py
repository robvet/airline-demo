"""Triage Agent - Routes customers to specialist agents.

This is the entry point agent that all conversations start with.
It analyzes the customer request and hands off to the appropriate specialist.
"""
from agents import Agent

from ...azure_client import MODEL
from ..context import AirlineAgentChatContext
from ..guardrails import relevance_guardrail, jailbreak_guardrail
from ..prompts.loader import load_prompt
from ..tools import get_trip_details

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


# Create agent WITHOUT handoffs - wired in __init__.py to avoid circular imports
triage_agent = Agent[AirlineAgentChatContext](
    name="Triage Agent",
    model=MODEL,
    handoff_description="Delegates requests to the right specialist agent (flight info, booking, seats, FAQ, baggage, compensation).",
    instructions=load_prompt("triage", {"RECOMMENDED_PROMPT_PREFIX": RECOMMENDED_PROMPT_PREFIX}),
    tools=[get_trip_details],
    handoffs=[],  # Wired in __init__.py
    input_guardrails=[jailbreak_guardrail, relevance_guardrail],
)
