"""
Streamlit UI for Pacific Airlines Demo.

Calls FastAPI backend at http://localhost:8000/chat
Run with: streamlit run streamlit_app.py
"""
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Deterministic Airlines", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    /* Reduce top padding */
    .block-container {
        padding-top: 3rem;
    }
    .agent-header {
        background-color: #2563eb;
        color: white;
        padding: 10px 15px;
        border-radius: 8px 8px 0 0;
        margin-bottom: 0;
    }
    .customer-header {
        background-color: #2563eb;
        color: white;
        padding: 10px 15px;
        border-radius: 8px 8px 0 0;
        margin-bottom: 0;
    }
    .stExpander {
        border: 1px solid #e5e7eb;
        border-radius: 0;
    }
    .title-banner {
        background-color: #1e3a5f;
        color: white;
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 28px;
        font-weight: bold;
    }
    /* Slightly lighter chat input container */
    [data-testid="stChatInput"] {
        background-color: #3a4556 !important;
        border-radius: 8px !important;
    }
    [data-testid="stChatInput"] > div {
        background-color: #3a4556 !important;
    }
    .stChatInput {
        background-color: #3a4556 !important;
    }
    .stChatInput > div {
        background-color: #3a4556 !important;
        border-color: #4a5568 !important;
    }
    .stChatInput textarea {
        background-color: #3a4556 !important;
    }
    [data-testid="stBottom"] > div {
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# Page title
st.markdown("<div class='title-banner'>✈️ Deterministic Airlines</div>", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None


def call_api(user_input: str) -> dict:
    """Call FastAPI backend."""
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": user_input, "customer_name": "Workshop Attendee"},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


# Layout
left, right = st.columns([1, 1])

# Left panel - Agent Dashboard
with left:
    st.markdown('<div class="agent-header"><b>🤖 Agent Dashboard</b></div>', unsafe_allow_html=True)
    
    # Conversation Context
    with st.expander("📋 Conversation Context", expanded=True):
        resp = st.session_state.last_response
        if resp:
            st.json({
                "routed_to": resp.get("routed_to"),
                "confidence": resp.get("confidence"),
                "rewritten_input": resp.get("rewritten_input"),
            })
        else:
            st.text("No conversation yet")
    
    # Guardrails (placeholder)
    with st.expander("🛡️ Guardrails", expanded=False):
        st.text("Input validation: Enabled")
        st.text("Output filtering: Enabled")
    
    # Runner Output / API Status
    with st.expander("📡 API Status", expanded=False):
        try:
            health = requests.get(f"{API_URL}/health", timeout=5).json()
            st.success(f"Backend: {health['status']}")
            st.text(f"Endpoint: {API_URL}")
        except Exception as e:
            st.error(f"API offline: {e}")
    
    # Reset button
    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        st.session_state.last_response = None
        st.rerun()

# Right panel - Customer View
with right:
    st.markdown('<div class="customer-header"><b>💬 Customer View</b></div>', unsafe_allow_html=True)
    
    # Chat history
    chat_container = st.container(height=350)
    with chat_container:
        if not st.session_state.messages:
            st.markdown("**Hi! I'm your airline assistant. How can I help today?**")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    
    # Quick action buttons - centered
    st.markdown('<div style="display: flex; justify-content: center; gap: 10px;">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Change my seat", use_container_width=True):
            st.session_state.pending_input = "I want to change my seat"
    with col2:
        if st.button("Flight status", use_container_width=True):
            st.session_state.pending_input = "What is my flight status?"
    with col3:
        if st.button("Baggage policy", use_container_width=True):
            st.session_state.pending_input = "What is the baggage policy?"
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process pending input from buttons
    if "pending_input" in st.session_state:
        pending = st.session_state.pending_input
        del st.session_state.pending_input
        st.session_state.messages.append({"role": "user", "content": pending})
        with st.spinner("Thinking..."):
            try:
                response = call_api(pending)
                st.session_state.last_response = response
                st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
        st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("Thinking..."):
            try:
                response = call_api(prompt)
                st.session_state.last_response = response
                st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
        
        st.rerun()
