"""
POLARIS - AI-Driven Personal Loan Sales System
Streamlit Chat Interface
"""

import streamlit as st
from master_agent import MasterAgent
from state import TerminalState

# Page configuration
st.set_page_config(
    page_title="POLARIS - Personal Loans",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
    }
    
    /* Chat message styling */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
    }
    
    /* User message */
    [data-testid="stChatMessageContent"] {
        font-size: 16px;
        line-height: 1.6;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #e94560 !important;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-active {
        background: linear-gradient(90deg, #00d9ff, #00ff88);
        color: #000;
    }
    
    .status-sanctioned {
        background: linear-gradient(90deg, #00ff88, #00d9ff);
        color: #000;
    }
    
    .status-rejected {
        background: linear-gradient(90deg, #ff4757, #ff6b81);
        color: #fff;
    }
    
    .status-dropped {
        background: linear-gradient(90deg, #ffa502, #ff7f50);
        color: #000;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        color: #00d9ff !important;
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(0, 217, 255, 0.1);
        border-left: 4px solid #00d9ff;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #e94560, #0f3460);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.4);
    }
</style>
""", unsafe_allow_html=True)


def get_status_badge(terminal_state):
    """Get HTML badge for terminal state."""
    if terminal_state == TerminalState.LOAN_SANCTIONED:
        return '<span class="status-badge status-sanctioned">✅ LOAN SANCTIONED</span>'
    elif terminal_state == TerminalState.LOAN_REJECTED:
        return '<span class="status-badge status-rejected">❌ LOAN REJECTED</span>'
    elif terminal_state == TerminalState.CUSTOMER_DROPPED:
        return '<span class="status-badge status-dropped">⚠️ CUSTOMER DROPPED</span>'
    elif terminal_state == TerminalState.ADDITIONAL_DOCUMENT_REQUIRED:
        return '<span class="status-badge status-dropped">📄 DOCUMENT REQUIRED</span>'
    else:
        return '<span class="status-badge status-active">🔄 IN PROGRESS</span>'


def initialize_session():
    """Initialize session state."""
    if "master_agent" not in st.session_state:
        st.session_state.master_agent = MasterAgent()
        st.session_state.master_agent.initialize()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "started" not in st.session_state:
        st.session_state.started = False


def display_sidebar():
    """Display sidebar with state information."""
    with st.sidebar:
        st.markdown("# 🌟 POLARIS")
        st.markdown("### Personal Loan Sales System")
        st.divider()
        
        state = st.session_state.master_agent.get_state()
        
        # Status
        st.markdown("### 📊 Status")
        status_html = get_status_badge(state.terminal_state)
        st.markdown(status_html, unsafe_allow_html=True)
        st.markdown(f"**Stage:** `{state.stage.value}`")
        
        st.divider()
        
        # Customer Info
        st.markdown("### 👤 Customer")
        if state.customer_name:
            st.markdown(f"**Name:** {state.customer_name}")
        if state.customer_id:
            st.markdown(f"**ID:** `{state.customer_id}`")
        if state.customer_phone:
            st.markdown(f"**Phone:** {state.customer_phone}")
        if state.credit_score:
            score_color = "🟢" if state.credit_score >= 750 else "🟡" if state.credit_score >= 700 else "🔴"
            st.markdown(f"**Credit Score:** {score_color} {state.credit_score}")
        
        st.divider()
        
        # Loan Details
        st.markdown("### 💰 Loan Details")
        if state.preapproved_limit:
            st.metric("Pre-approved Limit", f"₹{state.preapproved_limit:,.0f}")
        if state.requested_amount:
            st.metric("Requested Amount", f"₹{state.requested_amount:,.0f}")
        if state.tenure_months:
            st.markdown(f"**Tenure:** {state.tenure_months} months")
        if state.emi:
            st.metric("Monthly EMI", f"₹{state.emi:,.0f}")
        if state.interest_rate:
            st.markdown(f"**Interest Rate:** {state.interest_rate}% p.a.")
        
        st.divider()
        
        # Decision
        if state.decision:
            st.markdown("### ⚖️ Decision")
            decision_emoji = "✅" if state.decision.value == "APPROVED" else "❌" if state.decision.value == "REJECTED" else "📄"
            st.markdown(f"**{decision_emoji} {state.decision.value}**")
            if state.sanction_id:
                st.markdown(f"**Sanction ID:** `{state.sanction_id}`")
        
        st.divider()
        
        # System Info
        st.markdown("### ⚙️ System")
        st.markdown(f"**Agent Calls:** {state.total_agent_calls}/6")
        st.markdown(f"**KYC Verified:** {'✅' if state.kyc_verified else '❌'}")
        
        # Reset button
        st.divider()
        if st.button("🔄 Start New Conversation", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        # Test customers
        st.divider()
        st.markdown("### 🧪 Test Customers")
        st.markdown("""
        <div class="info-box">
        <strong>Available Numbers:</strong><br>
        • 9876543210 - Good credit ✅<br>
        • 9876543211 - Excellent credit ✅<br>
        • 9876543212 - Good credit ✅<br>
        • 9876543213 - Low credit ❌<br>
        • 9876543214 - KYC pending ⚠️
        </div>
        """, unsafe_allow_html=True)


def display_chat():
    """Display chat interface."""
    st.markdown("## 💬 Chat with POLARIS")
    
    # Display chat messages
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role, avatar="🌟" if role == "assistant" else "👤"):
            st.markdown(content)
    
    # Start button for new conversations
    if not st.session_state.started:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Loan Application", use_container_width=True):
                st.session_state.started = True
                # Send initial greeting
                response, _ = st.session_state.master_agent.process_message("hi")
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        return
    
    # Chat input
    state = st.session_state.master_agent.get_state()
    
    if state.is_terminal():
        st.info("This conversation has ended. Click 'Start New Conversation' in the sidebar to begin again.")
    else:
        if user_input := st.chat_input("Type your message..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
            
            # Get response from Master Agent
            with st.chat_message("assistant", avatar="🌟"):
                with st.spinner("Processing..."):
                    response, _ = st.session_state.master_agent.process_message(user_input)
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


def main():
    """Main application entry point."""
    initialize_session()
    display_sidebar()
    display_chat()


if __name__ == "__main__":
    main()
