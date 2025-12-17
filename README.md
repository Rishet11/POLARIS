# POLARIS 🌟

**AI-Driven Personal Loan Sales System for NBFC**

A multi-agent loan sales system built for hackathon demonstration. Features a Master Agent orchestrating Worker Agents with strict state machine control and anti-loop safeguards.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file with your Gemini API key:

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Run the Application

```bash
streamlit run app.py
```

---

## 🏗️ Architecture

```
POLARIS/
├── app.py                    # Streamlit UI
├── master_agent.py           # Central orchestrator
├── state.py                  # State machine
├── config.py                 # API configuration
├── offer_mart.py             # Mock customer database
└── agents/
    ├── base_agent.py         # Abstract base class
    ├── sales_agent.py        # Loan requirement extraction
    ├── verification_agent.py # KYC verification
    ├── underwriting_agent.py # Credit decisions
    └── sanction_agent.py     # Sanction letter generation
```

---

## 🔄 State Machine

The system operates as a finite-state machine with these stages:

1. **INTRO** → Greet customer
2. **NEED_DISCOVERY** → Capture phone & lookup offers
3. **OFFER_PRESENTATION** → Present offer & capture loan requirements
4. **KYC_VERIFICATION** → Verify customer identity
5. **UNDERWRITING** → Make credit decision
6. **DOCUMENT_COLLECTION** → Request salary slip (if needed)
7. **SANCTION** → Generate sanction letter
8. **REJECTION** → Explain rejection
9. **END** → Terminal state

### Terminal States

- ✅ `LOAN_SANCTIONED` - Loan approved and sanctioned
- ❌ `LOAN_REJECTED` - Application rejected
- 📄 `ADDITIONAL_DOCUMENT_REQUIRED` - Waiting for documents
- ⚠️ `CUSTOMER_DROPPED` - Customer declined or timeout

---

## 🧪 Test Customers

| Phone | Name | Credit Score | Pre-approved Limit | Expected Outcome |
|-------|------|--------------|-------------------|------------------|
| 9876543210 | Rahul Sharma | 780 | ₹5,00,000 | Approve up to limit |
| 9876543211 | Priya Patel | 820 | ₹7,50,000 | Approve up to limit |
| 9876543212 | Amit Kumar | 750 | ₹3,00,000 | Approve up to limit |
| 9876543213 | Vikram Singh | 650 | ₹0 | **Reject (low score)** |
| 9876543214 | Sneha Reddy | 760 | ₹4,00,000 | **Reject (KYC pending)** |

---

## ⚙️ Underwriting Rules

1. **Reject** if credit score < 700
2. **Approve instantly** if amount ≤ pre-approved limit
3. **Require salary slip** if amount ≤ 2× pre-approved limit
4. **Reject** if amount > 2× pre-approved limit

---

## 🛡️ Anti-Loop Safeguards

- Maximum 6 agent calls per conversation
- Same agent cannot be called twice with identical inputs
- Automatic termination on safeguard breach

---

## 📄 License

Built for hackathon demonstration purposes.
