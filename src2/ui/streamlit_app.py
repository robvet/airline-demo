"""
Streamlit UI for Pacific Airlines Demo.

Wired to use OrchestratorAgent with our deterministic patterns.
Run with: streamlit run streamlit_app.py
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from agents.orchestrator import OrchestratorAgent
from config.llm_config import LLMConfig
from memory import InMemoryStore
from models.context import AgentContext
from services.llm_service import LLMService
from services.prompt_template_service import PromptTemplateService
from tools.faq_tool import FAQTool
from tools.tool_registry import ToolRegistry

st.set_page_config(page_title="Pacific Airlines", layout="wide")


def create_orchestrator():
    """Create and wire up the orchestrator with all dependencies."""
    config = LLMConfig()
    config.validate()
    
    llm_service = LLMService(config)
    template_service = PromptTemplateService()
    memory_store = InMemoryStore()
    
    registry = ToolRegistry()
    registry.register(
        name="faq",
        description="Answers general questions about baggage, policies, fees, and airline procedures",
        tool_class=FAQTool
    )
    
    orchestrator = OrchestratorAgent(
        registry=registry,
        llm_service=llm_service,
        template_service=template_service,
        memory_store=memory_store
    )
    
    return orchestrator, memory_store, registry


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "orchestrator" not in st.session_state:
    orch, mem, reg = create_orchestrator()
    st.session_state.orchestrator = orch
    st.session_state.memory_store = mem
    st.session_state.registry = reg
if "context" not in st.session_state:
    st.session_state.context = AgentContext(customer_name="Workshop Attendee")
if "last_response" not in st.session_state:
    st.session_state.last_response = None


def run_agent(user_input: str):
    """Run the orchestrator with user input."""
    orchestrator = st.session_state.orchestrator
    context = st.session_state.context
    
    context.turn_count += 1
    response = orchestrator.handle(user_input, context)
    st.session_state.last_response = response
    
    return response


# Layout
left, right = st.columns([3, 2])

# Left panel - Agent View
with left:
    st.markdown("### 🤖 Agent View")
    
    # Current context
    with st.expander("📌 Customer Context", expanded=True):
        ctx = st.session_state.context
        st.json({
            "customer_name": ctx.customer_name,
            "turn_count": ctx.turn_count,
        })
    
    # Registered tools
    with st.expander("🔧 Registered Tools", expanded=True):
        registry = st.session_state.registry
        st.text(registry.get_routing_descriptions())
    
    # Last response details
    with st.expander("📊 Last Response Details", expanded=True):
        resp = st.session_state.last_response
        if resp:
            st.json({
                "routed_to": resp.routed_to,
                "confidence": resp.confidence,
                "original_input": resp.original_input,
                "rewritten_input": resp.rewritten_input,
            })
        else:
            st.text("No response yet")
    
    # Memory (conversation history)
    with st.expander("🧠 Conversation Memory", expanded=False):
        memory = st.session_state.memory_store
        session_id = st.session_state.context.customer_name
        history = memory.get_history(session_id)
        if history:
            for i, turn in enumerate(history):
                st.markdown(f"**Turn {i+1}:** {turn.intent} (conf: {turn.confidence:.2f})")
                st.text(f"  User: {turn.user_input[:50]}...")
                st.text(f"  Agent: {turn.agent_response[:50]}...")
                if turn.tool_reasoning:
                    st.text(f"  Reasoning: {turn.tool_reasoning[:50]}...")
        else:
            st.text("No history yet")
    
    # Reset button
    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        st.session_state.last_response = None
        orch, mem, reg = create_orchestrator()
        st.session_state.orchestrator = orch
        st.session_state.memory_store = mem
        st.session_state.registry = reg
        st.session_state.context = AgentContext(customer_name="Workshop Attendee")
        st.rerun()

# Right panel - Chat
with right:
    st.markdown("### 💬 Chat")
    
    # Chat history
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about baggage, policies, fees..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get response
        with st.spinner("Thinking..."):
            try:
                response = run_agent(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response.answer})
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
        
        st.rerun()
