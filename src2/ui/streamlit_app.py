"""
Streamlit UI for OpenAI Airlines Demo.

Single-agent architecture with AirlineAgent.
Run with: streamlit run streamlit_app.py
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from app.airline.agent import AirlineAgent

st.set_page_config(page_title="OpenAI Airlines", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "events" not in st.session_state:
    st.session_state.events = []
if "agent" not in st.session_state:
    st.session_state.agent = AirlineAgent()


def run_agent(user_input: str) -> str:
    """Run the agent with user input."""
    agent: AirlineAgent = st.session_state.agent
    
    # Run agent - simple!
    result = agent.run(user_input)
    
    # Record events for debugging
    for item in result.new_items:
        item_type = type(item).__name__
        st.session_state.events.append({
            "type": item_type,
            "content": str(item)[:100]
        })
    
    return result.response


# Layout
left, right = st.columns([3, 2])

# Left panel - Agent View
with left:
    st.markdown("### 🤖 Agent View")
    
    agent: AirlineAgent = st.session_state.agent
    
    # Current agent
    st.markdown(f"**Active Agent:** `{agent.agent_name}`")
    
    # Tools list
    with st.expander("🔧 Available Tools", expanded=False):
        for tool in AirlineAgent.TOOLS:
            name = getattr(tool, "name", str(tool))
            st.text(f"  • {name}")
    
    # Context - live from agent
    with st.expander("📌 Customer Context", expanded=True):
        ctx = agent.context
        st.json({
            "confirmation_number": ctx.confirmation_number,
            "flight_number": ctx.flight_number,
            "seat_number": ctx.seat_number,
            "passenger_name": ctx.passenger_name,
        })
    
    # Events
    with st.expander("⚡ Runner Events", expanded=True):
        if st.session_state.events:
            for e in st.session_state.events[-10:]:  # Last 10
                st.text(f"{e['type']}: {e['content'][:60]}")
        else:
            st.text("No events yet")
    
    # Reset button
    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        st.session_state.events = []
        st.session_state.agent = AirlineAgent()
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
    if prompt := st.chat_input("Ask about flights, seats, baggage..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get response
        with st.spinner("Thinking..."):
            try:
                response = run_agent(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
        
        st.rerun()
