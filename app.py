"""
POLARIS - FSM-Governed Financial Agents
Streamlit ledger console: loan origination + factoring back office.
"""

import csv
import io

import streamlit as st
from master_agent import MasterAgent
from state import TerminalState, Stage
from config import DEMO_MODE
from factoring import CollectionsAgent, ReconciliationAgent, MatchTier
from factoring.collections_fsm import CollectionOutcome
from factoring.mock_data import get_back_office_dataset
from factoring.reconciliation_agent import apply_match, reject_match
from factoring import portfolio

# Page configuration
st.set_page_config(
    page_title="POLARIS - FSM-Governed Financial Agents",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ledger-console CSS: light, flat, no gradients/glow/animation beyond a
# short hover transition. Monospace tabular numerals for ids/amounts.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, sans-serif;
    }

    .stApp {
        background: #fafaf7;
        color: #16181d;
    }

    .mono {
        font-family: 'JetBrains Mono', 'SF Mono', monospace;
        font-variant-numeric: tabular-nums;
    }

    h1, h2, h3 {
        color: #16181d !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px;
    }

    .section-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: #6b6d73;
        margin-bottom: 4px;
    }

    .ledger-card {
        background: #ffffff;
        border: 1px solid #e3e2dc;
        border-radius: 4px;
        padding: 16px 18px;
        margin: 8px 0;
    }

    .demo-caption {
        font-size: 12px;
        color: #6b6d73;
        border: 1px solid #e3e2dc;
        border-radius: 4px;
        padding: 6px 10px;
        margin: 6px 0 14px 0;
        background: #f0efe9;
    }

    /* Status pills: tinted bg, darker text, hairline border. No glow. */
    .pill {
        display: inline-block;
        padding: 2px 9px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.4px;
        border: 1px solid;
    }
    .pill-green  { background: #eaf6ef; color: #1a7f4b; border-color: #bfe3cd; }
    .pill-amber  { background: #fbf1e0; color: #a06b00; border-color: #edd8ab; }
    .pill-red    { background: #fbeae8; color: #b3392e; border-color: #edc4be; }
    .pill-blue   { background: #eaf0fb; color: #1f4ab8; border-color: #c3d2f2; }
    .pill-gray   { background: #f0efe9; color: #6b6d73; border-color: #e3e2dc; }

    .blocked-row {
        background: #fbeae8;
        border-left: 3px solid #b3392e;
        padding: 6px 10px;
        margin: 3px 0;
        color: #8a2c23;
        font-size: 13px;
    }

    .event-row {
        padding: 5px 10px;
        margin: 2px 0;
        font-size: 13px;
        border-left: 3px solid #e3e2dc;
    }

    .channel-tag {
        display: inline-block;
        padding: 1px 7px;
        border-radius: 3px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        background: #eaf0fb;
        color: #1f4ab8;
        border: 1px solid #c3d2f2;
        margin-right: 6px;
    }

    /* Ledger table */
    table.ledger { width: 100%; border-collapse: collapse; font-size: 13px; }
    table.ledger th {
        text-align: left;
        font-size: 11px;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        color: #6b6d73;
        border-bottom: 1px solid #e3e2dc;
        padding: 6px 8px;
        font-weight: 700;
    }
    table.ledger td {
        border-bottom: 1px solid #edece6;
        padding: 6px 8px;
        vertical-align: top;
    }
    table.ledger tr:hover { background: #f5f4ef; }

    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 26px !important;
        font-weight: 600 !important;
        color: #16181d !important;
    }
    [data-testid="stMetricLabel"] {
        color: #6b6d73 !important;
        font-size: 11px !important;
        letter-spacing: 0.8px !important;
        text-transform: uppercase;
    }

    .stButton > button {
        background: #ffffff !important;
        color: #1f4ab8 !important;
        border: 1px solid #1f4ab8 !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 6px 16px !important;
        transition: background 120ms ease, color 120ms ease !important;
    }
    .stButton > button:hover {
        background: #1f4ab8 !important;
        color: #ffffff !important;
    }

    hr { border: none; height: 1px; background: #e3e2dc; margin: 18px 0; }

    .avatar-circle {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        font-size: 11px;
        font-weight: 700;
        background: #eaf0fb;
        color: #1f4ab8;
        border: 1px solid #c3d2f2;
    }

    .checklist-item { font-size: 13px; padding: 3px 0; }
    .checklist-done { color: #1a7f4b; }
    .checklist-active { color: #1f4ab8; font-weight: 600; }
    .checklist-pending { color: #a6a8ad; }
</style>
""", unsafe_allow_html=True)


TIER_PILL = {
    MatchTier.AUTO_APPLY: '<span class="pill pill-green">AUTO-APPLY 100</span>',
    MatchTier.AUTO_APPLY_LOGGED: '<span class="pill pill-blue">AUTO + LOG 90</span>',
    MatchTier.REVIEW: '<span class="pill pill-amber">REVIEW</span>',
    MatchTier.EXCEPTION: '<span class="pill pill-red">EXCEPTION</span>',
}

STAGE_PILL = {
    "PRIORITIZE": "pill-gray", "OUTREACH": "pill-blue", "AWAIT_RESPONSE": "pill-blue",
    "PROMISE_TO_PAY": "pill-green", "DISPUTE_INTAKE": "pill-amber",
    "ESCALATE": "pill-red", "RESOLVED": "pill-green", "WRITTEN_OFF": "pill-gray",
}


def get_status_badge(terminal_state):
    """Get HTML pill for terminal state."""
    if terminal_state == TerminalState.LOAN_SANCTIONED:
        return '<span class="pill pill-green">LOAN SANCTIONED</span>'
    elif terminal_state == TerminalState.LOAN_REJECTED:
        return '<span class="pill pill-red">LOAN REJECTED</span>'
    elif terminal_state == TerminalState.CUSTOMER_DROPPED:
        return '<span class="pill pill-amber">CUSTOMER DROPPED</span>'
    elif terminal_state == TerminalState.ADDITIONAL_DOCUMENT_REQUIRED:
        return '<span class="pill pill-amber">DOCUMENT REQUIRED</span>'
    else:
        return '<span class="pill pill-blue">IN PROGRESS</span>'


def get_progress_steps(current_stage):
    """Plain numbered checklist with checkmark glyphs for completed steps."""
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

    lines = []
    for idx, (stage, label) in enumerate(stages):
        if idx < current_idx:
            lines.append(f'<div class="checklist-item checklist-done">&#10003; {label}</div>')
        elif idx == current_idx:
            lines.append(f'<div class="checklist-item checklist-active">{idx + 1}. {label}</div>')
        else:
            lines.append(f'<div class="checklist-item checklist-pending">{idx + 1}. {label}</div>')
    return "".join(lines)


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
        st.markdown("### POLARIS")
        st.caption("FSM-governed financial agents")
        if DEMO_MODE:
            st.markdown(
                '<div class="demo-caption">Demo mode: LLM responses are canned templates. '
                'Matching, portfolio math, and FSM logic run for real.</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        state = st.session_state.master_agent.get_state()

        st.markdown('<div class="section-label">Progress</div>', unsafe_allow_html=True)
        st.markdown(get_progress_steps(state.stage), unsafe_allow_html=True)

        st.divider()

        st.markdown('<div class="section-label">Status</div>', unsafe_allow_html=True)
        st.markdown(get_status_badge(state.terminal_state), unsafe_allow_html=True)

        st.divider()

        if state.customer_name:
            st.markdown('<div class="section-label">Customer</div>', unsafe_allow_html=True)
            st.markdown(f"**{state.customer_name}**")
            if state.customer_id:
                st.caption(f"ID: {state.customer_id}")
            if state.credit_score:
                tier = "pill-green" if state.credit_score >= 750 else "pill-amber" if state.credit_score >= 700 else "pill-red"
                st.markdown(
                    f'Credit score: <span class="pill {tier}">{state.credit_score}</span>',
                    unsafe_allow_html=True,
                )
            st.divider()

        if state.preapproved_limit or state.requested_amount:
            st.markdown('<div class="section-label">Loan Details</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            if state.preapproved_limit:
                with col1:
                    st.metric("Limit", f"Rs {state.preapproved_limit/100000:.1f}L")
            if state.requested_amount:
                with col2:
                    st.metric("Amount", f"Rs {state.requested_amount/100000:.1f}L")

            if state.tenure_months:
                st.markdown(f"**Tenure:** {state.tenure_months} months")
            if state.emi:
                st.markdown(f"**EMI:** Rs {state.emi:,.0f}/month")
            if state.interest_rate:
                st.markdown(f"**Rate:** {state.interest_rate}% p.a.")

            st.divider()

        if state.decision:
            st.markdown('<div class="section-label">Decision</div>', unsafe_allow_html=True)
            if state.decision.value == "APPROVED":
                st.success(state.decision.value)
            elif state.decision.value == "REJECTED":
                st.error(state.decision.value)
            else:
                st.warning(state.decision.value)

            if state.sanction_id:
                st.code(state.sanction_id, language=None)
            st.divider()

        st.markdown('<div class="section-label">System</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"Calls: **{state.total_agent_calls}/6**")
        with col2:
            st.markdown(f"KYC: **{'yes' if state.kyc_verified else 'no'}**")

        st.divider()
        if st.button("New Conversation", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.divider()
        st.markdown('<div class="section-label">Test Numbers (sample data)</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="demo-caption">
        <span class="mono">9876543210</span> - Rahul, approves<br>
        <span class="mono">9876543213</span> - Low credit, rejects<br>
        <span class="mono">9876543214</span> - KYC pending
        </div>
        """, unsafe_allow_html=True)


def display_chat():
    """Display chat interface."""
    st.markdown("## Personal Loan Assistant")
    st.caption("Consumer loan origination, India NBFC (sample data)")

    state = st.session_state.master_agent.get_state()

    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        avatar_letter = "P" if role == "assistant" else "U"
        with st.chat_message(role):
            st.markdown(
                f'<span class="avatar-circle">{avatar_letter}</span>&nbsp; {content}',
                unsafe_allow_html=True,
            )

    if not st.session_state.started:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Start Loan Application", use_container_width=True):
                st.session_state.started = True
                response, _ = st.session_state.master_agent.process_message("hi")
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        return

    if state.stage == Stage.DOCUMENT_COLLECTION and not state.salary_slip_received:
        st.markdown("---")
        with st.container():
            st.markdown("### Income Verification Required")
            st.markdown("To process your loan request above the pre-approved limit, please upload your salary slip.")

            uploaded_file = st.file_uploader(
                "Upload Salary Slip",
                type=['pdf', 'png', 'jpg', 'jpeg'],
                key="salary_uploader",
                help="Upload your latest salary slip or bank statement showing salary credit"
            )

            if uploaded_file is not None:
                with st.spinner("Analyzing document..."):
                    sys_msg = f"SYSTEM_UPLOAD_EVENT: {uploaded_file.name}"
                    response, _ = st.session_state.master_agent.process_message(sys_msg)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
        st.markdown("---")

    if state.is_terminal():
        if state.terminal_state == TerminalState.LOAN_SANCTIONED:
            st.success("Loan sanctioned.")

            if state.sanction_id:
                pdf_path = f"sanction_letters/{state.sanction_id}.pdf"
                try:
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                        st.download_button(
                            label="Download Sanction Letter",
                            data=pdf_bytes,
                            file_name=f"{state.sanction_id}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                except FileNotFoundError:
                    st.info("Sanction letter is being generated.")

        elif state.terminal_state == TerminalState.LOAN_REJECTED:
            st.error("Your application could not be approved at this time.")
        else:
            st.warning("This conversation has ended.")
        st.info("Click 'New Conversation' in the sidebar to start again.")
    else:
        if user_input := st.chat_input("Type your message..."):
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.chat_message("user"):
                st.markdown(f'<span class="avatar-circle">U</span>&nbsp; {user_input}', unsafe_allow_html=True)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response, _ = st.session_state.master_agent.process_message(user_input)
                    st.markdown(f'<span class="avatar-circle">P</span>&nbsp; {response}', unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


def initialize_back_office():
    """Initialize back-office session state."""
    if "bo_data" not in st.session_state:
        debtors, invoices, payments = get_back_office_dataset()
        st.session_state.bo_data = {"debtors": debtors, "invoices": invoices, "payments": payments}
        st.session_state.bo_recon = None
        st.session_state.bo_audit_trail = []
        st.session_state.bo_cases = None
        st.session_state.bo_case_log = {}


def _ledger_table(headers, rows):
    head = "".join(f"<th>{h}</th>" for h in headers)
    return f"<table class='ledger'><tr>{head}</tr>{''.join(rows)}</table>"


def display_payment_matching():
    """Payment matching (cash application): run reconciliation, review queue,
    exception queue, and a searchable confidence-scored audit trail."""
    data = st.session_state.bo_data
    st.markdown("### Payment Matching")
    st.caption(
        "Cash application: incoming bank feed vs open factored invoices (sample data). "
        "Deterministic matching with confidence tiers, no LLM in this path. The agent "
        "auto-applies only what is unambiguous; everything else waits for a human."
    )

    if st.button("Run Payment Matching"):
        agent = ReconciliationAgent()
        result = agent.process(data["payments"], data["invoices"], data["debtors"])
        st.session_state.bo_recon = result
        st.session_state.bo_audit_trail = list(result["audit_trail"])

    recon = st.session_state.bo_recon
    if not recon:
        st.info(f"{len(data['payments'])} payments on the bank feed, "
                f"{sum(1 for i in data['invoices'] if i.is_open)} open invoices. "
                "Run payment matching to match them.")
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
            f"<tr><td class='mono'>{p.payment_id}</td><td>{p.payer_name}</td>"
            f"<td class='mono'>${p.amount:,.2f}</td><td class='mono'>{p.reference_text or '-'}</td>"
            f"<td>{TIER_PILL[p.match_tier]}</td><td class='mono'>{p.match_confidence}%</td>"
            f"<td class='mono'>{', '.join(p.matched_invoice_ids) or '-'}</td>"
            f"<td>{p.match_reason or ''}</td></tr>"
        )
    st.markdown(
        _ledger_table(
            ["Payment", "Payer", "Amount", "Memo", "Tier", "Conf.", "Matched Invoices", "Match Reason"],
            rows,
        ),
        unsafe_allow_html=True,
    )

    st.markdown("---")
    _display_review_queue(recon, data)
    st.markdown("---")
    _display_exception_queue(recon, data)
    st.markdown("---")
    _display_audit_trail()


def _display_review_queue(recon, data):
    """Actionable review queue: candidates shown with Approve / Send-to-exceptions."""
    invoices_by_id = {i.invoice_id: i for i in data["invoices"]}
    review_items = [p for p in recon["results"] if p.match_tier == MatchTier.REVIEW and not p.applied]

    st.markdown(f"#### Review queue ({len(review_items)})")
    st.caption("Probable matches awaiting a human decision. Approve applies the match to the ledger; "
               "Send to exceptions routes it to the exception queue instead.")

    if not review_items:
        st.caption("Nothing pending review.")
        return

    for p in review_items:
        candidates = [invoices_by_id[iid] for iid in p.matched_invoice_ids if iid in invoices_by_id]
        cand_text = ", ".join(
            f"{inv.invoice_id} (open ${inv.open_amount:,.2f})" for inv in candidates
        ) or "no candidate invoice"
        with st.container():
            st.markdown(
                f"<div class='ledger-card'>"
                f"<span class='mono'><b>{p.payment_id}</b></span> &middot; "
                f"<span class='mono'>${p.amount:,.2f}</span> &middot; {p.match_confidence}% confidence<br>"
                f"<span style='color:#6b6d73'>Candidates: {cand_text}</span><br>"
                f"<span style='color:#6b6d73'>{p.match_reason}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            b1, b2 = st.columns(2)
            if b1.button("Approve", key=f"approve_{p.payment_id}"):
                entry = apply_match(p, data["invoices"], actor="human")
                st.session_state.bo_audit_trail.append(entry)
                st.rerun()
            if b2.button("Send to exceptions", key=f"reject_{p.payment_id}"):
                entry = reject_match(p, "Sent to exceptions by reviewer", actor="human")
                st.session_state.bo_audit_trail.append(entry)
                st.rerun()


def _display_exception_queue(recon, data):
    invoices_by_id = {i.invoice_id: i for i in data["invoices"]}
    exception_items = [p for p in recon["results"] if p.match_tier == MatchTier.EXCEPTION and not p.applied]

    st.markdown(f"#### Exception queue ({len(exception_items)})")
    st.caption("Ambiguous or unmatched payments. A human can approve one of the listed "
               "candidates directly, if any, or leave it for manual research.")

    if not exception_items:
        st.caption("No exceptions.")
        return

    for p in exception_items:
        candidates = [invoices_by_id[iid] for iid in p.matched_invoice_ids if iid in invoices_by_id]
        cand_text = ", ".join(
            f"{inv.invoice_id} (open ${inv.open_amount:,.2f})" for inv in candidates
        ) or "no candidate invoice"
        st.markdown(
            f"<div class='ledger-card'>"
            f"<span class='mono'><b>{p.payment_id}</b></span> &middot; "
            f"<span class='mono'>${p.amount:,.2f}</span><br>"
            f"<span style='color:#6b6d73'>Candidates: {cand_text}</span><br>"
            f"<span style='color:#6b6d73'>{p.match_reason}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if candidates:
            if st.button("Approve first candidate", key=f"approve_exc_{p.payment_id}"):
                p.matched_invoice_ids = [candidates[0].invoice_id]
                entry = apply_match(p, data["invoices"], actor="human")
                st.session_state.bo_audit_trail.append(entry)
                st.rerun()


def _display_audit_trail():
    """First-class, searchable confidence-scored audit trail."""
    st.markdown("#### Confidence-scored audit trail")
    st.caption("Every payment matching decision, system or human, timestamped and searchable.")

    trail = st.session_state.bo_audit_trail
    if not trail:
        st.caption("No audit entries yet.")
        return

    query = st.text_input("Search audit trail", placeholder="payment id, invoice id, actor, reason...",
                           key="audit_search")
    filtered = trail
    if query:
        q = query.lower()
        filtered = [
            e for e in trail
            if q in str(e.get("payment_id", "")).lower()
            or q in " ".join(e.get("invoice_ids", [])).lower()
            or q in str(e.get("actor", "")).lower()
            or q in str(e.get("reason", "")).lower()
            or q in str(e.get("tier", "")).lower()
        ]

    rows = []
    for e in sorted(filtered, key=lambda e: e["timestamp"], reverse=True):
        actor_pill = "pill-blue" if e["actor"] == "human" else "pill-gray"
        rows.append(
            f"<tr><td class='mono'>{e['timestamp']}</td>"
            f"<td><span class='pill {actor_pill}'>{e['actor']}</span></td>"
            f"<td class='mono'>{e['payment_id']}</td>"
            f"<td class='mono'>{', '.join(e['invoice_ids']) or '-'}</td>"
            f"<td class='mono'>{e['tier'] or '-'}</td>"
            f"<td class='mono'>{e['confidence']}%</td>"
            f"<td>{e['reason']}</td></tr>"
        )
    st.markdown(
        _ledger_table(
            ["Timestamp", "Actor", "Payment", "Invoices", "Tier", "Confidence", "Reason"],
            rows,
        ),
        unsafe_allow_html=True,
    )


def display_collections():
    """Collections queue and per-case FSM driver."""
    data = st.session_state.bo_data
    st.markdown("### Collections")
    st.caption(
        "Past-due invoices ranked by priority (sample data). Every case runs inside a strict FSM: "
        "the agent cannot send the same message twice, cannot skip the escalation "
        "gate, and cannot act on a closed case."
    )

    if st.session_state.bo_cases is None:
        if st.button("Build Collections Queue"):
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
        stage_class = STAGE_PILL.get(c.stage.value, "pill-gray")
        queue_rows.append(
            f"<tr><td class='mono'>{c.case_id}</td><td>{debtor.name}</td>"
            f"<td class='mono'>${c.open_amount:,.2f}</td><td class='mono'>{c.aging_bucket}</td>"
            f"<td class='mono'>{c.priority_score:,.0f}</td>"
            f"<td><span class='pill {stage_class}'>{c.stage.value}</span></td>"
            f"<td class='mono'>{c.outreach_count}</td></tr>"
        )
    st.markdown(
        _ledger_table(
            ["Case", "Account Debtor", "Open", "Aging", "Priority", "Stage", "Outreaches"],
            queue_rows,
        ),
        unsafe_allow_html=True,
    )

    st.markdown("---")
    case_id = st.selectbox("Work a case", list(cases.keys()))
    case = cases[case_id]
    invoice = invoices[case.invoice_id]
    debtor = data["debtors"][case.debtor_id]
    log = st.session_state.bo_case_log.setdefault(case_id, [])

    language = st.radio("Message language", ["en", "es"], horizontal=True, key=f"lang_{case_id}")

    work_col, inspect_col = st.columns([3, 2])

    with work_col:
        b1, b2, b3 = st.columns(3)
        if b1.button("Send reminder", use_container_width=True):
            outcome, msg = agent.run_outreach(case, invoice, debtor, language=language)
            if outcome is CollectionOutcome.OK:
                log.append(("agent", msg, case.channel_history[-1] if case.channel_history else None))
            else:
                log.append(("blocked", f"Send blocked by FSM: {outcome.value}", None))
            st.rerun()
        if b2.button("Retry identical send (will be blocked)", use_container_width=True,
                     help="Simulates a looping agent re-attempting its last action"):
            if case.sent_message_hashes and log:
                last_sent = next((m for role, m, _ in reversed(log) if role == "agent"), None)
                if last_sent:
                    case.start_outreach()
                    outcome, _ = case.send_message(last_sent)
                    log.append(("blocked" if outcome is not CollectionOutcome.OK else "agent",
                                f"Duplicate send attempt: {outcome.value}", None))
            else:
                log.append(("blocked", "Nothing sent yet - send a reminder first", None))
            st.rerun()
        if b3.button("Escalate", use_container_width=True):
            outcome = case.escalate()
            log.append(("blocked" if outcome is not CollectionOutcome.OK else "agent",
                        f"Escalation attempt: {outcome.value}", None))
            st.rerun()

        reply = st.text_input("Simulate debtor reply",
                              placeholder='e.g. "We will pay by Friday" or "We dispute this invoice"')
        if st.button("Submit reply") and reply:
            agent.handle_response(case, reply)
            log.append(("debtor", reply, None))
            log.append(("agent", f"Response classified, case now in {case.stage.value}", None))
            st.rerun()

        for role, msg, channel in log[-8:]:
            if role == "blocked":
                st.markdown(f'<div class="blocked-row">BLOCKED &mdash; {msg}</div>', unsafe_allow_html=True)
            elif role == "debtor":
                with st.chat_message("user"):
                    st.markdown(f'<span class="avatar-circle">D</span>&nbsp; {msg}', unsafe_allow_html=True)
            else:
                tag = f'<span class="channel-tag">{channel}</span>' if channel else ""
                with st.chat_message("assistant"):
                    st.markdown(f'<span class="avatar-circle">P</span>&nbsp; {tag}{msg}', unsafe_allow_html=True)

    with inspect_col:
        st.markdown("#### Case state")
        c = case.to_dict()
        st.markdown(
            "<div class='ledger-card'>"
            f"<div><span style='color:#6b6d73'>Invoice</span> <span class='mono'>{c['invoice_id']}</span></div>"
            f"<div><span style='color:#6b6d73'>Open amount</span> <span class='mono'>${c['open_amount']:,.2f}</span></div>"
            f"<div><span style='color:#6b6d73'>Aging</span> <span class='mono'>{c['aging_bucket']}</span></div>"
            f"<div><span style='color:#6b6d73'>Stage</span> <span class='pill {STAGE_PILL.get(c['stage'], 'pill-gray')}'>{c['stage']}</span></div>"
            f"<div><span style='color:#6b6d73'>Outreaches</span> <span class='mono'>{c['outreach_count']}</span></div>"
            f"<div><span style='color:#6b6d73'>Next channel</span> <span class='channel-tag'>{c['next_channel']}</span></div>"
            f"<div><span style='color:#6b6d73'>Dilution reserve</span> <span class='mono'>${c['dilution_reserve']:,.2f}</span></div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Transition history")
        st.caption("BLOCKED rows show the guard that fired, by name.")
        for entry in case.history[-10:]:
            if entry.startswith("BLOCKED"):
                st.markdown(f'<div class="blocked-row">{entry}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="event-row">{entry}</div>', unsafe_allow_html=True)


def display_portfolio_monitor():
    """Portfolio monitor: covenant-style table + data-tape CSV export."""
    data = st.session_state.bo_data
    invoices = data["invoices"]
    debtors = data["debtors"]

    st.markdown("### Portfolio Monitor")
    st.caption(
        "Computed from the open ledger (sample data). Thresholds below are a configurable "
        "sample policy, not a published industry or client covenant."
    )

    c1, c2 = st.columns(2)
    c1.metric("Open AR Total", f"${portfolio.open_ar_total(invoices):,.0f}")
    c2.metric("Funds Employed", f"${portfolio.funds_employed(invoices):,.0f}")

    st.markdown("#### Covenant table")
    rows = []
    for row in portfolio.covenant_table(invoices, debtors):
        status_class = "pill-green" if row["status"] == "COMPLIANT" else "pill-amber"
        rows.append(
            f"<tr><td>{row['metric']}</td><td class='mono'>{row['current']}</td>"
            f"<td class='mono'>{row['threshold']}</td>"
            f"<td><span class='pill {status_class}'>{row['status']}</span></td></tr>"
        )
    st.markdown(
        _ledger_table(["Metric", "Current", "Threshold", "Status"], rows),
        unsafe_allow_html=True,
    )

    st.markdown("#### Concentration by account debtor")
    conc_rows = []
    for row in portfolio.concentration_by_debtor(invoices, debtors):
        status_class = "pill-green" if row["status"] == "COMPLIANT" else "pill-amber"
        conc_rows.append(
            f"<tr><td>{row['debtor_name']}</td><td class='mono'>${row['open_amount']:,.2f}</td>"
            f"<td class='mono'>{row['pct_of_open_ar']}%</td>"
            f"<td><span class='pill {status_class}'>{row['status']}</span></td></tr>"
        )
    st.markdown(
        _ledger_table(["Account Debtor", "Open Amount", "% of Open AR", "Status"], conc_rows),
        unsafe_allow_html=True,
    )

    st.markdown("#### Aging distribution")
    aging = portfolio.aging_distribution(invoices)
    aging_rows = []
    for bucket in ("CURRENT", "1-30", "31-60", "61-90", "90+"):
        b = aging[bucket]
        aging_rows.append(
            f"<tr><td class='mono'>{bucket}</td><td class='mono'>{b['count']}</td>"
            f"<td class='mono'>${b['amount']:,.2f}</td><td class='mono'>{b['pct_of_open_ar']}%</td></tr>"
        )
    st.markdown(
        _ledger_table(["Bucket", "Count", "Amount", "% of Open AR"], aging_rows),
        unsafe_allow_html=True,
    )
    st.caption(f"Over 60 days: {aging['pct_over_60']}% "
               f"({'WARNING' if aging['status'] == 'WARNING' else 'compliant'})")

    st.markdown("---")
    csv_buffer = io.StringIO()
    tape_rows = portfolio.data_tape_rows(invoices, debtors)
    if tape_rows:
        writer = csv.DictWriter(csv_buffer, fieldnames=list(tape_rows[0].keys()))
        writer.writeheader()
        writer.writerows(tape_rows)

    st.download_button(
        label="Export data tape (CSV)",
        data=csv_buffer.getvalue(),
        file_name="polaris_data_tape.csv",
        mime="text/csv",
    )


def display_back_office():
    """Factoring back-office tab: payment matching, collections, portfolio monitor."""
    initialize_back_office()
    st.markdown("## Factoring Back Office")
    st.caption("Payment Matching / Collections / Portfolio Monitor")
    if DEMO_MODE:
        st.markdown(
            '<div class="demo-caption">Demo mode: LLM responses are canned templates. '
            'Matching, portfolio math, and FSM logic run for real.</div>',
            unsafe_allow_html=True,
        )

    display_payment_matching()
    st.markdown("---")
    display_collections()
    st.markdown("---")
    display_portfolio_monitor()

    st.markdown("---")
    if st.button("Reset Back Office Data"):
        for key in ("bo_data", "bo_recon", "bo_audit_trail", "bo_cases", "bo_case_log", "bo_agent"):
            st.session_state.pop(key, None)
        st.rerun()


def main():
    """Main application entry point."""
    initialize_session()
    display_sidebar()
    tab_back_office, tab_loans = st.tabs(["Factoring Back Office", "Loan Origination"])
    with tab_back_office:
        display_back_office()
    with tab_loans:
        display_chat()


if __name__ == "__main__":
    main()
