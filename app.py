"""
POLARIS - AI-Driven Personal Loan Sales System
Premium Streamlit Chat Interface with Visual Polish
"""

import streamlit as st
from master_agent import MasterAgent
from state import TerminalState, Stage
from factoring import CollectionsAgent, ReconciliationAgent, MatchTier
from factoring.collections_fsm import CollectionOutcome
from factoring.mock_data import get_back_office_dataset
import time

# Page configuration
st.set_page_config(
    page_title="POLARIS - FSM-Governed Lending Agents",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS with animations and glassmorphism
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container - Dark gradient background */
    .main {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* Glassmorphism card effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 16px !important;
        padding: 16px !important;
        margin: 12px 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        animation: fadeInUp 0.4s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* User message */
    [data-testid="stChatMessageContent"] {
        font-size: 15px;
        line-height: 1.7;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #0f3460 100%);
        border-right: 1px solid rgba(233, 69, 96, 0.3);
    }
    
    [data-testid="stSidebar"] > div {
        padding-top: 0;
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(90deg, #e94560, #ff6b6b, #ffd93d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700 !important;
    }
    
    h2, h3 {
        color: #e94560 !important;
        font-weight: 600 !important;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .status-active {
        background: linear-gradient(90deg, #00d9ff, #00ff88);
        color: #000;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.4);
    }
    
    .status-sanctioned {
        background: linear-gradient(90deg, #00ff88, #00d9ff);
        color: #000;
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
        animation: glow 1.5s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 0 20px rgba(0, 255, 136, 0.4); }
        to { box-shadow: 0 0 40px rgba(0, 255, 136, 0.8); }
    }
    
    .status-rejected {
        background: linear-gradient(90deg, #ff4757, #ff6b81);
        color: #fff;
        box-shadow: 0 0 20px rgba(255, 71, 87, 0.4);
    }
    
    .status-dropped {
        background: linear-gradient(90deg, #ffa502, #ff7f50);
        color: #000;
        box-shadow: 0 0 20px rgba(255, 165, 2, 0.4);
    }

    /* Cash application tier badges */
    .tier-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .tier-auto { background: rgba(0, 255, 136, 0.18); color: #00ff88; border: 1px solid rgba(0,255,136,0.4); }
    .tier-logged { background: rgba(0, 217, 255, 0.15); color: #00d9ff; border: 1px solid rgba(0,217,255,0.4); }
    .tier-review { background: rgba(255, 217, 61, 0.15); color: #ffd93d; border: 1px solid rgba(255,217,61,0.4); }
    .tier-exception { background: rgba(255, 71, 87, 0.15); color: #ff6b81; border: 1px solid rgba(255,71,87,0.4); }

    .blocked-banner {
        background: rgba(255, 71, 87, 0.12);
        border: 1px solid rgba(255, 71, 87, 0.5);
        border-radius: 12px;
        padding: 14px 18px;
        margin: 10px 0;
        color: #ff6b81;
        font-weight: 600;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #00d9ff, #00ff88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.6) !important;
    }
    
    /* Progress steps */
    .progress-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        margin: 15px 0;
    }
    
    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }
    
    .progress-step::after {
        content: '';
        position: absolute;
        top: 15px;
        left: 50%;
        width: 100%;
        height: 2px;
        background: rgba(255, 255, 255, 0.1);
        z-index: 0;
    }
    
    .progress-step:last-child::after {
        display: none;
    }
    
    .step-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 600;
        z-index: 1;
        transition: all 0.3s ease;
    }
    
    .step-completed {
        background: linear-gradient(135deg, #00ff88, #00d9ff);
        color: #000;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
    }
    
    .step-active {
        background: linear-gradient(135deg, #e94560, #ff6b6b);
        color: #fff;
        box-shadow: 0 0 20px rgba(233, 69, 96, 0.6);
        animation: pulse 1.5s infinite;
    }
    
    .step-pending {
        background: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .step-label {
        font-size: 9px;
        margin-top: 5px;
        color: rgba(255, 255, 255, 0.5);
        text-align: center;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #e94560, #ff6b6b) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(233, 69, 96, 0.5) !important;
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(0, 217, 255, 0.08);
        border-left: 4px solid #00d9ff;
        padding: 12px 16px;
        border-radius: 0 12px 12px 0;
        margin: 8px 0;
        font-size: 13px;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(233, 69, 96, 0.3), transparent);
        margin: 20px 0;
    }
    
    /* Chat input styling */
    .stChatInput > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(233, 69, 96, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stChatInput input {
        color: white !important;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 8px 16px;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background: #e94560;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    
    /* Confetti canvas */
    #confetti-canvas {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
    }
    
    /* Logo animation */
    .logo-container {
        text-align: center;
        padding: 20px 0;
    }
    
    .logo-text {
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(90deg, #e94560, #ff6b6b, #ffd93d, #00ff88, #00d9ff);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 3s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% center; }
        50% { background-position: 100% center; }
        100% { background-position: 0% center; }
    }
    
    .logo-subtitle {
        color: rgba(255, 255, 255, 0.6);
        font-size: 14px;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-top: 5px;
    }
    
    /* Success animation */
    .success-animation {
        animation: successPop 0.5s ease-out;
    }
    
    @keyframes successPop {
        0% { transform: scale(0.8); opacity: 0; }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Confetti JavaScript
CONFETTI_JS = """
<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
<script>
function fireConfetti() {
    var duration = 3 * 1000;
    var animationEnd = Date.now() + duration;
    var defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 };
    
    function randomInRange(min, max) {
        return Math.random() * (max - min) + min;
    }
    
    var interval = setInterval(function() {
        var timeLeft = animationEnd - Date.now();
        
        if (timeLeft <= 0) {
            return clearInterval(interval);
        }
        
        var particleCount = 50 * (timeLeft / duration);
        
        confetti(Object.assign({}, defaults, {
            particleCount,
            origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
            colors: ['#e94560', '#00ff88', '#00d9ff', '#ffd93d', '#ff6b6b']
        }));
        confetti(Object.assign({}, defaults, {
            particleCount,
            origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
            colors: ['#e94560', '#00ff88', '#00d9ff', '#ffd93d', '#ff6b6b']
        }));
    }, 250);
}
</script>
"""


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


def get_progress_steps(current_stage):
    """Generate progress steps HTML."""
    stages = [
        ("INTRO", "Start"),
        ("NEED_DISCOVERY", "Phone"),
        ("OFFER_PRESENTATION", "Offer"),
        ("KYC_VERIFICATION", "KYC"),
        ("UNDERWRITING", "Check"),
        ("SANCTION", "Done"),
    ]
    
    stage_order = [s[0] for s in stages]
    
    try:
        current_idx = stage_order.index(current_stage.value) if current_stage else 0
    except ValueError:
        current_idx = len(stage_order)  # END state
    
    html = '<div class="progress-container">'
    for idx, (stage, label) in enumerate(stages):
        if idx < current_idx:
            circle_class = "step-completed"
            icon = "✓"
        elif idx == current_idx:
            circle_class = "step-active"
            icon = str(idx + 1)
        else:
            circle_class = "step-pending"
            icon = str(idx + 1)
        
        html += f'''
        <div class="progress-step">
            <div class="step-circle {circle_class}">{icon}</div>
            <div class="step-label">{label}</div>
        </div>
        '''
    html += '</div>'
    return html


def initialize_session():
    """Initialize session state."""
    if "master_agent" not in st.session_state:
        st.session_state.master_agent = MasterAgent()
        st.session_state.master_agent.initialize()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "started" not in st.session_state:
        st.session_state.started = False
    
    if "show_confetti" not in st.session_state:
        st.session_state.show_confetti = False


def display_sidebar():
    """Display sidebar with state information."""
    with st.sidebar:
        # Logo
        st.markdown("""
        <div class="logo-container">
            <div class="logo-text">🌟 POLARIS</div>
            <div class="logo-subtitle">FSM-Governed Lending Agents</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        state = st.session_state.master_agent.get_state()
        
        # Progress Steps
        st.markdown("### 📍 Progress")
        st.markdown(get_progress_steps(state.stage), unsafe_allow_html=True)
        
        st.divider()
        
        # Status
        st.markdown("### 📊 Status")
        status_html = get_status_badge(state.terminal_state)
        st.markdown(status_html, unsafe_allow_html=True)
        
        st.divider()
        
        # Customer Info
        if state.customer_name:
            st.markdown("### 👤 Customer")
            st.markdown(f"**{state.customer_name}**")
            if state.customer_id:
                st.caption(f"ID: {state.customer_id}")
            if state.credit_score:
                score_color = "🟢" if state.credit_score >= 750 else "🟡" if state.credit_score >= 700 else "🔴"
                st.markdown(f"Credit Score: {score_color} **{state.credit_score}**")
            st.divider()
        
        # Loan Details
        if state.preapproved_limit or state.requested_amount:
            st.markdown("### 💰 Loan Details")
            
            col1, col2 = st.columns(2)
            if state.preapproved_limit:
                with col1:
                    st.metric("Limit", f"₹{state.preapproved_limit/100000:.1f}L")
            if state.requested_amount:
                with col2:
                    st.metric("Amount", f"₹{state.requested_amount/100000:.1f}L")
            
            if state.tenure_months:
                st.markdown(f"**Tenure:** {state.tenure_months} months")
            if state.emi:
                st.markdown(f"**EMI:** ₹{state.emi:,.0f}/month")
            if state.interest_rate:
                st.markdown(f"**Rate:** {state.interest_rate}% p.a.")
            
            st.divider()
        
        # Decision
        if state.decision:
            st.markdown("### ⚖️ Decision")
            if state.decision.value == "APPROVED":
                st.success(f"✅ {state.decision.value}")
            elif state.decision.value == "REJECTED":
                st.error(f"❌ {state.decision.value}")
            else:
                st.warning(f"📄 {state.decision.value}")
            
            if state.sanction_id:
                st.code(state.sanction_id, language=None)
            st.divider()
        
        # System Info
        st.markdown("### ⚙️ System")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"Calls: **{state.total_agent_calls}/6**")
        with col2:
            st.markdown(f"KYC: **{'✅' if state.kyc_verified else '❌'}**")
        
        # Reset button
        st.divider()
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        # Test customers
        st.divider()
        st.markdown("### 🧪 Test Numbers")
        st.markdown("""
        <div class="info-box">
        <strong>9876543210</strong> - Rahul ✅<br>
        <strong>9876543213</strong> - Low Credit ❌<br>
        <strong>9876543214</strong> - KYC Pending ⚠️
        </div>
        """, unsafe_allow_html=True)


def display_chat():
    """Display chat interface."""
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1>💬 Personal Loan Assistant</h1>
        <p style="color: rgba(255,255,255,0.5);">Powered by AI • Instant Decisions • Pre-approved Offers</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we should show confetti
    state = st.session_state.master_agent.get_state()
    if state.terminal_state == TerminalState.LOAN_SANCTIONED and not st.session_state.get("confetti_fired"):
        st.session_state.confetti_fired = True
        st.markdown(CONFETTI_JS, unsafe_allow_html=True)
        st.markdown("<script>fireConfetti();</script>", unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role, avatar="🌟" if role == "assistant" else "👤"):
            st.markdown(content)
    
    # Start button for new conversations
    if not st.session_state.started:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Loan Application", use_container_width=True):
                st.session_state.started = True
                # Send initial greeting
                response, _ = st.session_state.master_agent.process_message("hi")
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        return
    
    # Handle Document Collection with REAL file uploader
    if state.stage == Stage.DOCUMENT_COLLECTION and not state.salary_slip_received:
        st.markdown("---")
        with st.container():
            st.markdown("### 📄 Income Verification Required")
            st.markdown("To process your loan request above the pre-approved limit, please upload your salary slip.")
            
            uploaded_file = st.file_uploader(
                "Upload Salary Slip",
                type=['pdf', 'png', 'jpg', 'jpeg'],
                key="salary_uploader",
                help="Upload your latest salary slip or bank statement showing salary credit"
            )
            
            if uploaded_file is not None:
                with st.spinner("🔍 Analyzing document with AI..."):
                    time.sleep(2)  # Simulate OCR processing time
                    
                    # Send a system event to the agent
                    sys_msg = f"SYSTEM_UPLOAD_EVENT: {uploaded_file.name}"
                    response, _ = st.session_state.master_agent.process_message(sys_msg)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
        st.markdown("---")
    
    # Chat input
    if state.is_terminal():
        if state.terminal_state == TerminalState.LOAN_SANCTIONED:
            st.success("🎉 Congratulations! Your loan has been sanctioned!")
            
            # Add download button for sanction letter
            if state.sanction_id:
                pdf_path = f"sanction_letters/{state.sanction_id}.pdf"
                try:
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                        st.download_button(
                            label="📄 Download Sanction Letter",
                            data=pdf_bytes,
                            file_name=f"{state.sanction_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                except FileNotFoundError:
                    st.info("Sanction letter is being generated...")
                    
        elif state.terminal_state == TerminalState.LOAN_REJECTED:
            st.error("Your application could not be approved at this time.")
        else:
            st.warning("This conversation has ended.")
        st.info("Click 'New Conversation' in the sidebar to start again.")
    else:
        if user_input := st.chat_input("Type your message..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
            
            # Get response from Master Agent
            with st.chat_message("assistant", avatar="🌟"):
                with st.spinner(""):
                    # Typing indicator
                    typing_placeholder = st.empty()
                    typing_placeholder.markdown("""
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    response, _ = st.session_state.master_agent.process_message(user_input)
                    
                    typing_placeholder.empty()
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


TIER_BADGES = {
    MatchTier.AUTO_APPLY: '<span class="tier-badge tier-auto">AUTO-APPLY 100%</span>',
    MatchTier.AUTO_APPLY_LOGGED: '<span class="tier-badge tier-logged">AUTO + AUDIT LOG</span>',
    MatchTier.REVIEW: '<span class="tier-badge tier-review">REVIEW</span>',
    MatchTier.EXCEPTION: '<span class="tier-badge tier-exception">EXCEPTION</span>',
}


def initialize_back_office():
    """Initialize back-office session state."""
    if "bo_data" not in st.session_state:
        debtors, invoices, payments = get_back_office_dataset()
        st.session_state.bo_data = {"debtors": debtors, "invoices": invoices, "payments": payments}
        st.session_state.bo_recon = None
        st.session_state.bo_cases = None
        st.session_state.bo_case_log = {}


def display_cash_application():
    """Cash application: run reconciliation, show tiers, KPIs, exception queue."""
    data = st.session_state.bo_data
    st.markdown("### 💸 Cash Application")
    st.caption(
        "Incoming bank feed vs open factored invoices. Deterministic matching with "
        "confidence tiers — the agent auto-applies only what is unambiguous; "
        "everything else waits for a human."
    )

    if st.button("▶ Run Cash Application", use_container_width=False):
        agent = ReconciliationAgent()
        st.session_state.bo_recon = agent.process(
            data["payments"], data["invoices"], data["debtors"]
        )

    recon = st.session_state.bo_recon
    if not recon:
        st.info(f"{len(data['payments'])} payments on the bank feed, "
                f"{sum(1 for i in data['invoices'] if i.is_open)} open invoices. "
                "Run cash application to match them.")
        return

    kpis = recon["kpis"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Auto-Match Rate", f"{kpis['auto_match_rate']}%")
    c2.metric("Auto-Applied", kpis["auto_applied"])
    c3.metric("Needs Review", kpis["review"])
    c4.metric("Exceptions", kpis["exceptions"])

    rows = []
    for p in recon["results"]:
        rows.append(
            f"<tr><td>{p.payment_id}</td><td>{p.payer_name}</td>"
            f"<td>${p.amount:,.2f}</td><td><code>{p.reference_text or '—'}</code></td>"
            f"<td>{TIER_BADGES[p.match_tier]}</td><td>{p.match_confidence}%</td>"
            f"<td>{', '.join(p.matched_invoice_ids) or '—'}</td></tr>"
        )
    st.markdown(
        "<table style='width:100%; font-size:13px;'>"
        "<tr><th>Payment</th><th>Payer</th><th>Amount</th><th>Memo</th>"
        "<th>Tier</th><th>Conf.</th><th>Matched Invoices</th></tr>"
        + "".join(rows) + "</table>",
        unsafe_allow_html=True,
    )

    review_items = [p for p in recon["results"] if p.match_tier == MatchTier.REVIEW]
    exception_items = [p for p in recon["results"] if p.match_tier == MatchTier.EXCEPTION]

    with st.expander(f"🟡 Review queue ({len(review_items)})"):
        for p in review_items:
            st.markdown(f"**{p.payment_id}** · ${p.amount:,.2f} — {p.match_reason}")
    with st.expander(f"🔴 Exception queue ({len(exception_items)})"):
        for p in exception_items:
            st.markdown(f"**{p.payment_id}** · ${p.amount:,.2f} — {p.match_reason}")
    if recon["audit_log"]:
        with st.expander(f"📋 Audit log ({len(recon['audit_log'])})"):
            for entry in recon["audit_log"]:
                st.markdown(f"- {entry}")


def display_collections():
    """Collections queue and per-case FSM driver."""
    data = st.session_state.bo_data
    st.markdown("### 📞 Collections")
    st.caption(
        "Past-due invoices ranked by priority. Every case runs inside a strict FSM: "
        "the agent cannot send the same message twice, cannot skip the escalation "
        "gate, and cannot act on a closed case."
    )

    if st.session_state.bo_cases is None:
        if st.button("▶ Build Collections Queue"):
            agent = CollectionsAgent()
            cases = agent.prioritize(data["invoices"], data["debtors"])
            st.session_state.bo_cases = {c.case_id: c for c in cases}
            st.session_state.bo_agent = agent
            st.rerun()
        return

    cases = st.session_state.bo_cases
    agent = st.session_state.bo_agent
    invoices = {i.invoice_id: i for i in data["invoices"]}

    queue_rows = []
    for c in sorted(cases.values(), key=lambda c: c.priority_score, reverse=True):
        debtor = data["debtors"][c.debtor_id]
        queue_rows.append(
            f"<tr><td>{c.case_id}</td><td>{debtor.name}</td>"
            f"<td>${c.open_amount:,.2f}</td><td>{c.aging_bucket}</td>"
            f"<td>{c.priority_score:,.0f}</td><td><b>{c.stage.value}</b></td>"
            f"<td>{c.outreach_count}</td></tr>"
        )
    st.markdown(
        "<table style='width:100%; font-size:13px;'>"
        "<tr><th>Case</th><th>Account Debtor</th><th>Open</th><th>Aging</th>"
        "<th>Priority</th><th>Stage</th><th>Outreaches</th></tr>"
        + "".join(queue_rows) + "</table>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    case_id = st.selectbox("Work a case", list(cases.keys()))
    case = cases[case_id]
    invoice = invoices[case.invoice_id]
    debtor = data["debtors"][case.debtor_id]
    log = st.session_state.bo_case_log.setdefault(case_id, [])

    work_col, inspect_col = st.columns([3, 2])

    with work_col:
        b1, b2, b3 = st.columns(3)
        if b1.button("✉️ Send reminder", use_container_width=True):
            outcome, msg = agent.run_outreach(case, invoice, debtor)
            if outcome is CollectionOutcome.OK:
                log.append(("agent", msg))
            else:
                log.append(("blocked", f"Send blocked by FSM: {outcome.value}"))
            st.rerun()
        if b2.button("🔁 Retry same send", use_container_width=True,
                     help="Simulates a looping agent re-attempting its last action"):
            if case.sent_message_hashes and log:
                last_sent = next((m for role, m in reversed(log) if role == "agent"), None)
                if last_sent:
                    case.start_outreach()
                    outcome, _ = case.send_message(last_sent)
                    log.append(("blocked" if outcome is not CollectionOutcome.OK else "agent",
                                f"Duplicate send attempt → {outcome.value}"))
            else:
                log.append(("blocked", "Nothing sent yet — send a reminder first"))
            st.rerun()
        if b3.button("⚠️ Escalate", use_container_width=True):
            outcome = case.escalate()
            log.append(("blocked" if outcome is not CollectionOutcome.OK else "agent",
                        f"Escalation attempt → {outcome.value}"))
            st.rerun()

        reply = st.text_input("Simulate debtor reply",
                              placeholder='e.g. "We will pay by Friday" or "We dispute this invoice"')
        if st.button("Submit reply") and reply:
            outcome = agent.handle_response(case, reply)
            log.append(("debtor", reply))
            log.append(("agent", f"Response classified → case now in {case.stage.value}"))
            st.rerun()

        for role, msg in log[-8:]:
            if role == "blocked":
                st.markdown(f'<div class="blocked-banner">🛑 {msg}</div>', unsafe_allow_html=True)
            elif role == "debtor":
                with st.chat_message("user", avatar="🏢"):
                    st.markdown(msg)
            else:
                with st.chat_message("assistant", avatar="🌟"):
                    st.markdown(msg)

    with inspect_col:
        st.markdown("#### 🔍 Case FSM State")
        st.json(case.to_dict())
        st.markdown("#### 📜 Transition history")
        for entry in case.history[-10:]:
            icon = "🛑" if entry.startswith("BLOCKED") else "→"
            st.markdown(f"<div style='font-size:12px'>{icon} {entry}</div>",
                        unsafe_allow_html=True)


def display_back_office():
    """Factoring back-office tab: cash application + collections."""
    initialize_back_office()
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1>🏦 Factoring Back Office</h1>
        <p style="color: rgba(255,255,255,0.5);">Cash Application • Collections • Exception-Based Review</p>
    </div>
    """, unsafe_allow_html=True)

    display_cash_application()
    st.markdown("---")
    display_collections()

    st.markdown("---")
    if st.button("🔄 Reset Back Office Data"):
        for key in ("bo_data", "bo_recon", "bo_cases", "bo_case_log", "bo_agent"):
            st.session_state.pop(key, None)
        st.rerun()


def main():
    """Main application entry point."""
    initialize_session()
    display_sidebar()
    tab_loans, tab_back_office = st.tabs(["💬 Loan Origination", "🏦 Factoring Back Office"])
    with tab_loans:
        display_chat()
    with tab_back_office:
        display_back_office()


if __name__ == "__main__":
    main()
