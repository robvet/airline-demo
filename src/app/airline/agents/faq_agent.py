"""FAQ Agent - Answers policy and common questions.

Uses the faq_lookup_tool to provide accurate answers from the knowledge base
rather than relying on training data.
"""
from agents import Agent

from ...azure_client import MODEL
from ..context import AirlineAgentChatContext
from ..guardrails import relevance_guardrail, jailbreak_guardrail
from ..prompts.loader import load_prompt
from ..tools import faq_lookup_tool

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX


# Create agent WITHOUT handoffs - wired in __init__.py to avoid circular imports
faq_agent = Agent[AirlineAgentChatContext](
    name="FAQ Agent",
    model=MODEL,
    handoff_description="Answers common questions about policies, baggage, seats, and compensation.",
    instructions=load_prompt("faq", {"RECOMMENDED_PROMPT_PREFIX": RECOMMENDED_PROMPT_PREFIX}),
    tools=[faq_lookup_tool],
    handoffs=[],  # Wired in __init__.py
    input_guardrails=[jailbreak_guardrail, relevance_guardrail],
)
