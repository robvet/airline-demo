"""
Orchestrator - Agent execution pipeline.

This is the WORKSHOP ENTRY POINT for debugging agent orchestration.
Set a breakpoint at Orchestrator.run() to step through the entire flow:

    1. Triage agent receives user message
    2. Triage decides which specialist to hand off to
    3. Handoff callback hydrates context
    4. Specialist agent executes (calls tools)
    5. Response streams back

All WebSocket/HTTP plumbing is handled elsewhere - this is pure orchestration.

DEBUGGING:
    Set breakpoint at Orchestrator.run() 
    Step through to see: handoffs, tool calls, agent responses
"""
from dataclasses import dataclass
from typing import Any, AsyncIterator

from agents import Agent, Runner
from agents.run import RunResultStreaming
from chatkit.agents import stream_agent_response

from .context import AirlineAgentChatContext
from .agents import (
    triage_agent,
    faq_agent,
    seat_special_services_agent,
    flight_information_agent,
    booking_cancellation_agent,
    refunds_compensation_agent,
)


@dataclass
class OrchestrationResult:
    """Result container returned after orchestration completes."""
    result: RunResultStreaming
    completed: bool = True


class Orchestrator:
    """
    Agent execution pipeline controller.
    
    Encapsulates conversation flow for debugging, testing, and extensibility.
    This class isolates orchestration logic from server infrastructure.
    
    Usage:
        orchestrator = Orchestrator()
        event_stream, result = await orchestrator.run(agent_name, input_items, context)
        async for event, _ in event_stream:
            # Process events
    
    For Testing:
        orchestrator = Orchestrator(starting_agent=mock_agent)
    """
    
    def __init__(self, starting_agent: Agent[AirlineAgentChatContext] | None = None):
        """
        Initialize the orchestrator.
        
        Args:
            starting_agent: Override the default triage agent (useful for testing)
        """
        self._starting_agent = starting_agent or triage_agent
        self._agents: dict[str, Agent[AirlineAgentChatContext]] = {
            triage_agent.name: triage_agent,
            faq_agent.name: faq_agent,
            seat_special_services_agent.name: seat_special_services_agent,
            flight_information_agent.name: flight_information_agent,
            booking_cancellation_agent.name: booking_cancellation_agent,
            refunds_compensation_agent.name: refunds_compensation_agent,
        }
    
    @property
    def starting_agent(self) -> Agent[AirlineAgentChatContext]:
        """The default agent that handles incoming requests."""
        return self._starting_agent
    
    @property
    def agents(self) -> dict[str, Agent[AirlineAgentChatContext]]:
        """Registry of all available agents by name."""
        return self._agents
    
    def get_agent(self, name: str) -> Agent[AirlineAgentChatContext]:
        """
        Return the agent object by name, defaulting to starting agent.
        
        Args:
            name: The agent's display name
            
        Returns:
            The Agent instance, or starting_agent if not found
        """
        return self._agents.get(name, self._starting_agent)
    
    async def run(
        self,
        agent: Agent[AirlineAgentChatContext] | str,
        input_items: list[dict[str, Any]],
        context: AirlineAgentChatContext,
    ) -> tuple[AsyncIterator[tuple[Any, RunResultStreaming]], RunResultStreaming]:
        """
        Execute the agent orchestration pipeline.
        
        ==========================================================
        >>> SET BREAKPOINT HERE <<<
        ==========================================================
        
        This method is the clean entry point for debugging the entire
        agent flow without any WebSocket/HTTP plumbing.
        
        Args:
            agent: The starting agent (instance or name string)
            input_items: Conversation history as input list
            context: The airline chat context with customer state
        
        Returns:
            Tuple of (event_stream, result) where:
            - event_stream: AsyncIterator yielding SDK events
            - result: The RunResultStreaming object for post-processing
        
        Debug Flow:
            1. Step INTO this method
            2. Step OVER Runner.run_streamed() to start orchestration
            3. Step INTO the async for loop to see each event
            4. Watch result.new_items for handoffs and tool calls
            5. Check context.state for customer data updates
        
        Example Breakpoint Session:
            > orchestrator.run() called with "change my seat"
            > Runner.run_streamed(triage_agent, ...) starts
            > Event: handoff from Triage to Seat Agent
            > Event: tool_call display_seat_map
            > Event: message "Here's the seat map..."
            > Orchestration complete, return to caller
        """
        # Resolve agent name to instance if string provided
        if isinstance(agent, str):
            agent = self.get_agent(agent)
        
        # ==========================================================
        # ORCHESTRATION ENTRY POINT
        # ==========================================================
        # This is where the OpenAI Agents SDK takes control.
        # The Runner manages: agent selection, handoffs, tool calls, guardrails
        result: RunResultStreaming = Runner.run_streamed(
            agent,
            input_items,
            context=context,
        )
        
        async def event_stream() -> AsyncIterator[tuple[Any, RunResultStreaming]]:
            """
            Stream events from the agent pipeline.
            Each iteration yields one event: handoff, tool call, message chunk, etc.
            """
            async for event in stream_agent_response(context, result):
                # Yield event + result so caller can access new_items
                yield event, result
        
        return event_stream(), result


# ==========================================================
# BACKWARD COMPATIBILITY WRAPPERS
# ==========================================================
# These functions maintain backward compatibility with code that
# imports get_agent_by_name or run_conversation directly.
# New code should use the Orchestrator class directly.

def get_agent_by_name(name: str) -> Agent[AirlineAgentChatContext]:
    """Backward compatibility wrapper. Use Orchestrator.get_agent instead."""
    return Orchestrator().get_agent(name)


def run_conversation(agent, input_items, context=None):
    """Backward compatibility wrapper. Use Orchestrator.run instead."""
    return Orchestrator().run(agent, input_items, context=context)
