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
    """Main chat endpoint - processes user messages through the agent pipeline."""
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
    """Get the current state of a conversation thread."""
    return await server.snapshot(thread_id, {"request": None})


@router.get("/chatkit/bootstrap")
async def chatkit_bootstrap(
    server: AirlineServer = Depends(get_server),
) -> Dict[str, Any]:
    """Bootstrap a new conversation - returns initial state."""
    return await server.snapshot(None, {"request": None})


@router.get("/chatkit/state/stream")
async def chatkit_state_stream(
    thread_id: str = Query(...),
    server: AirlineServer = Depends(get_server),
):
    """Stream state updates for a conversation thread via SSE."""
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
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy"}
