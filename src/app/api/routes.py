"""
API Routes for OpenAI Airlines Demo.

This module defines the HTTP endpoints using FastAPI's APIRouter.
Similar to a Controller in ASP.NET or Spring.

ARCHITECTURE:
    main.py (Program.cs)  →  Startup config, middleware, app creation
    routes.py (Controller) →  HTTP endpoint definitions
"""
import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response, StreamingResponse
from chatkit.server import StreamingResult

from ..server import AirlineServer


# Module-level server instance (created once, reused)
_chat_server: AirlineServer | None = None


def get_server() -> AirlineServer:
    """
    Dependency provider for AirlineServer.
    
    Similar to DI container resolution in ASP.NET:
        services.AddSingleton<AirlineServer>()
    """
    global _chat_server
    if _chat_server is None:
        _chat_server = AirlineServer()
    return _chat_server


# Create the router - like declaring a Controller
router = APIRouter()


##########################################################################
# ChatKit Endpoints
##########################################################################

@router.post("/chatkit")
async def chatkit_endpoint(
    request: Request, 
    server: AirlineServer = Depends(get_server)
) -> Response:
    """
    Main Chat Endpoint - Process user messages through the agent pipeline.
    
    This is the primary entry point for conversation. The ChatKit UI posts
    user messages here, and the server routes them through the triage agent
    to specialist agents (FAQ, booking, seats, refunds, flight info).
    
    Request:
        Body: ChatKit protocol payload (JSON) containing:
            - thread_id: Conversation identifier (optional - omit for new chats)
            - message: User's text input
    
    Response:
        Streaming (SSE): ThreadStreamEvent objects emitted as agents process:
            - MessageOutputItem: Agent text responses shown in chat
            - HandoffOutputItem: Agent-to-agent transfers (e.g., Triage -> Booking)
            - ToolCallOutputItem: Tool invocation results (e.g., flight lookup)
            - ClientEffectEvent: UI state update signals
    
    Flow:
        1. User message received
        2. Triage agent determines intent
        3. Handoff to specialist agent (if needed)
        4. Specialist executes tools and responds
        5. Response streamed back as SSE events
    
    Called by: ui/components/chatkit-panel.tsx (ChatKitProvider)
    """
    payload = await request.body()
    result = await server.process(payload, {"request": request})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return Response(content=result)


@router.get("/chatkit/state")
async def chatkit_state(
    thread_id: str = Query(...),
    server: AirlineServer = Depends(get_server),
) -> Dict[str, Any]:
    """
    Get Conversation State - Snapshot of a thread's current state.
    
    Returns the full state of a conversation for UI hydration or debugging.
    Used by the Runner Output panel to show agent activity, tool calls,
    handoffs, and guardrail checks.
    
    Request:
        Query Params:
            - thread_id (required): The conversation thread identifier
    
    Response:
        JSON object containing:
            - thread_id: The conversation identifier
            - current_agent: Name of the active agent (e.g., "Triage Agent")
            - context: Customer context (confirmation_number, flight_number, seat)
            - agents: List of all available agents with tools and handoffs
            - events: History of agent events (messages, handoffs, tool calls)
            - guardrails: Input guardrail check results (passed/failed + reasoning)
    
    Called by: ui/components/runner-output.tsx (initial load)
    """
    return await server.snapshot(thread_id, {"request": None})


@router.get("/chatkit/bootstrap")
async def chatkit_bootstrap(
    server: AirlineServer = Depends(get_server),
) -> Dict[str, Any]:
    """
    Bootstrap Endpoint - Initialize a new conversation.
    
    Creates a fresh conversation thread and returns the initial state.
    Called when the UI first loads before any user interaction.
    Returns an empty conversation with the full agent registry so the
    UI can display available agents and their capabilities.
    
    Request:
        None (GET with no parameters)
    
    Response:
        JSON object containing:
            - thread_id: Newly generated conversation identifier
            - current_agent: "Triage Agent" (always starts here)
            - context: Empty customer context
            - agents: Full list of agents with tools, handoffs, guardrails
            - events: Empty list (no activity yet)
            - guardrails: Empty list (no checks yet)
    
    Called by: ui/components/runner-output.tsx (on initial page load)
    """
    return await server.snapshot(None, {"request": None})


@router.get("/chatkit/state/stream")
async def chatkit_state_stream(
    thread_id: str = Query(...),
    server: AirlineServer = Depends(get_server),
):
    """
    State Stream Endpoint - Real-time state updates via Server-Sent Events.
    
    Establishes a persistent SSE connection for live updates as agents
    process messages. The Runner Output panel subscribes to this stream
    to show real-time tool calls, handoffs, and context changes without
    polling.
    
    Request:
        Query Params:
            - thread_id (required): The conversation thread to subscribe to
    
    Response:
        SSE Stream: Continuous stream of state snapshots as JSON:
            - Initial snapshot sent immediately on connection
            - Subsequent updates pushed when agent activity occurs
            - events_delta: Only new events since last update (optimization)
    
    Connection Lifecycle:
        1. Client connects with thread_id
        2. Server registers client as listener for that thread
        3. Initial state snapshot sent
        4. Updates pushed on agent activity (via asyncio.Queue)
        5. Client disconnects -> listener unregistered (finally block)
    
    Called by: ui/components/runner-output.tsx (useEffect subscription)
    """
    thread = await server.ensure_thread(thread_id, {"request": None})
    queue = server.register_listener(thread.id)

    async def event_generator():
        try:
            initial = await server.snapshot(thread.id, {"request": None})
            yield f"data: {json.dumps(initial, default=str)}\n\n"
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
        finally:
            server.unregister_listener(thread.id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


##########################################################################
# Health Check
##########################################################################

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health Check Endpoint - Liveness probe for infrastructure.
    
    Simple endpoint for load balancers, Kubernetes, Azure Container Apps,
    or any orchestrator to verify the service is running.
    
    Request:
        None (GET with no parameters)
    
    Response:
        JSON: {"status": "healthy"}
        HTTP 200 indicates service is alive
    
    Used by:
        - Kubernetes liveness/readiness probes
        - Azure App Service health checks
        - Load balancer health checks
        - Monitoring systems (Prometheus, Datadog, etc.)
    """
    return {"status": "healthy"}
