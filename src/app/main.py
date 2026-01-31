from __future__ import annotations as _annotations

import os

from .config import settings
from .observability.telemetry_service import setup_telemetry
from .utils.lifespan_manager import LifespanManager

# Disable tracing before importing agents
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents import set_default_openai_client
from .azure_client import azure_client

set_default_openai_client(azure_client)

# Import the router (like registering a Controller in ASP.NET)
from .api.routes import router

##########################################################################
# Architectural Observation - Facade Pattern
##########################################################################
# We call setup_telemetry() rather than TelemetryService() directly.
#
# This is the FACADE PATTERN - a function that abstracts a concrete class.
#
# WHY: Most classes in a system won't change, but telemetry providers
# WILL change over time. Today it's Azure, tomorrow it might be Datadog.
#
# BENEFITS:
#   - Swap Azure Monitor for Datadog without changing this file
#   - Use no-op provider for local dev
#   - Mock provider for unit testing
#
# See telemetry_service.py for the implementation and provider swap logic.
##########################################################################

# Initialize telemetry (see Facade Pattern note above)
setup_telemetry()

# Lifespan manager handles startup/shutdown (port cleanup, browser, telemetry flush)
lifespan_manager = LifespanManager(
    port=settings.server_port,
    open_browser=True,
    flush_telemetry=True,
)

app = FastAPI(
    title="Deterministic Precision Reference App",
    lifespan=lifespan_manager.lifespan,
)

# Instrument FastAPI for OpenTelemetry tracing (traces all HTTP requests)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

# Disable tracing for zero data retention orgs
os.environ.setdefault("OPENAI_TRACING_DISABLED", "1")

# CORS configuration (adjust as needed for deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes (like app.UseEndpoints() in ASP.NET)
app.include_router(router)
