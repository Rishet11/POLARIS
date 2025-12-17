"""
POLARIS Master Agent
Main orchestrator implementing the finite-state machine.
Controls conversation lifecycle and enforces terminal states.
"""

from typing import Optional, Tuple
from state import ConversationState, Stage, Decision, TerminalState
from agents import SalesAgent, VerificationAgent, UnderwritingAgent, SanctionAgent
from offer_mart import get_preapproved_offer, lookup_customer_by_phone
from config import get_model, MAX_AGENT_CALLS


class MasterAgent:
    """
    Master Agent - The central orchestrator.
    
    Responsibilities:
    - Control conversation lifecycle
    - Decide which Worker Agent to invoke
    - Validate outputs from Worker Agents
    - Enforce exit conditions
    - Prevent loops and quota exhaustion
    """
    
    def __init__(self):
        self.model = get_model()
        
        # Initialize worker agents
        self.sales_agent = SalesAgent()
        self.verification_agent = VerificationAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.sanction_agent = SanctionAgent()
        
        # Conversation state
        self.state: Optional[ConversationState] = None
    
    def initialize(self) -> ConversationState:
        """Initialize a new conversation."""
        self.state = ConversationState()
        return self.state
    
    def get_state(self) -> ConversationState:
        """Get current conversation state."""
        if not self.state:
            self.state = ConversationState()
        return self.state
    
    def _check_safeguards(self) -> Optional[str]:
        """
        Check anti-loop safeguards.
        Returns error message if safeguard triggered, None otherwise.
        """
        if self.state.is_terminal():
            return f"Conversation ended: {self.state.terminal_state.value}"
        
        if self.state.total_agent_calls >= MAX_AGENT_CALLS:
            self.state.terminal_state = TerminalState.CUSTOMER_DROPPED
            self.state.stage = Stage.END
            return "Maximum agent calls exceeded. Conversation ended."
        
        return None
    
    def _generate_response(self, system_prompt: str, user_message: str) -> str:
        """Generate a response using Gemini."""
        full_prompt = f"{system_prompt}\n\nCustomer message: {user_message}"
        response = self.model.generate_content(full_prompt)
        return response.text
    
    def process_message(self, user_message: str) -> Tuple[str, ConversationState]:
        """
        Process a user message and return response.
        This is the main entry point for the conversation.
        
        Returns:
            Tuple of (response_text, updated_state)
        """
        if not self.state:
            self.initialize()
        
        # Store user message
        self.state.add_message("user", user_message)
        
        # Check safeguards
        safeguard_error = self._check_safeguards()
        if safeguard_error:
            return safeguard_error, self.state
        
        # Route to appropriate stage handler
        response = self._route_to_handler(user_message)
        
        # Store assistant response
        self.state.add_message("assistant", response)
        
        return response, self.state
    
    def _route_to_handler(self, user_message: str) -> str:
        """Route message to appropriate stage handler."""
        handlers = {
            Stage.INTRO: self._handle_intro,
            Stage.NEED_DISCOVERY: self._handle_need_discovery,
            Stage.OFFER_PRESENTATION: self._handle_offer_presentation,
            Stage.KYC_VERIFICATION: self._handle_kyc_verification,
            Stage.UNDERWRITING: self._handle_underwriting,
            Stage.DOCUMENT_COLLECTION: self._handle_document_collection,
            Stage.SANCTION: self._handle_sanction,
            Stage.REJECTION: self._handle_rejection,
            Stage.END: self._handle_end,
        }
        
        handler = handlers.get(self.state.stage, self._handle_intro)
        return handler(user_message)
    
    def _handle_intro(self, user_message: str) -> str:
        """
        INTRO Stage: Greet and ask for interest.
        """
        # Generate greeting
        response = (
            "Hello! Welcome to Polaris Personal Loans. I'm here to help you with a quick and easy loan today.\n\n"
            "May I know your **mobile number** so I can check if you have a pre-approved offer waiting for you?"
        )
        
        # Check if user already provided phone number
        phone = self._extract_phone_number(user_message)
        if phone:
            self.state.customer_phone = phone
            self.state.stage = Stage.NEED_DISCOVERY
            return self._handle_need_discovery(user_message)
        
        # Move to need discovery
        self.state.stage = Stage.NEED_DISCOVERY
        return response
    
    def _handle_need_discovery(self, user_message: str) -> str:
        """
        NEED_DISCOVERY Stage: Get phone and loan requirements.
        """
        # Try to extract phone number if not already captured
        if not self.state.customer_phone:
            phone = self._extract_phone_number(user_message)
            if phone:
                self.state.customer_phone = phone
            else:
                return "I didn't catch your mobile number. Could you please share your **10-digit mobile number**?"
        
        # Look up customer in Offer Mart
        offer = get_preapproved_offer(self.state.customer_phone)
        
        if not offer:
            # Customer not found or not eligible
            customer = lookup_customer_by_phone(self.state.customer_phone)
            if customer and customer.credit_score < 700:
                self.state.terminal_state = TerminalState.LOAN_REJECTED
                self.state.stage = Stage.END
                return (
                    "I'm sorry, but I wasn't able to find a pre-approved offer for you at this time. "
                    "Our loan products require a minimum credit score. "
                    "You may want to work on improving your credit score and try again in a few months. "
                    "Thank you for your interest in Polaris!"
                )
            else:
                self.state.terminal_state = TerminalState.CUSTOMER_DROPPED
                self.state.stage = Stage.END
                return (
                    "I'm sorry, but I couldn't find your profile in our system. "
                    "You may need to register with us first. Thank you for your interest in Polaris!"
                )
        
        # Store customer details
        self.state.customer_id = offer["customer_id"]
        self.state.customer_name = offer["customer_name"]
        self.state.preapproved_limit = offer["preapproved_limit"]
        self.state.credit_score = offer["credit_score"]
        self.state.interest_rate = offer["interest_rate"]
        
        # Move to offer presentation
        self.state.stage = Stage.OFFER_PRESENTATION
        
        return (
            f"Great news, **{self.state.customer_name}**! 🎉\n\n"
            f"You have a **pre-approved personal loan offer** of up to **₹{self.state.preapproved_limit:,.0f}**!\n\n"
            f"📊 **Your Offer Details:**\n"
            f"- Maximum Amount: ₹{self.state.preapproved_limit:,.0f}\n"
            f"- Interest Rate: {offer['interest_rate']}% per annum\n"
            f"- Maximum Tenure: {offer['max_tenure_months']} months\n\n"
            f"How much would you like to borrow, and for how many months?"
        )
    
    def _handle_offer_presentation(self, user_message: str) -> str:
        """
        OFFER_PRESENTATION Stage: Get loan amount and tenure.
        """
        # Check for rejection/decline keywords
        decline_keywords = ["no", "not interested", "decline", "cancel", "don't want", "nevermind", "forget it"]
        if any(keyword in user_message.lower() for keyword in decline_keywords):
            self.state.terminal_state = TerminalState.CUSTOMER_DROPPED
            self.state.stage = Stage.END
            return (
                "I understand. Thank you for considering Polaris Personal Loans. "
                "If you change your mind, our pre-approved offer will be available for 30 days. "
                "Have a great day!"
            )
        
        # Call Sales Agent to extract loan requirements
        input_hash = self.sales_agent.compute_input_hash({"message": user_message})
        
        if not self.state.can_call_agent("SALES_AGENT", input_hash):
            # Already called with same input - ask differently
            return (
                "I need to understand your loan requirement better. "
                "Could you please tell me:\n"
                "1. **How much** do you want to borrow? (in rupees)\n"
                "2. **How many months** would you like to repay it in?"
            )
        
        self.state.record_agent_call("SALES_AGENT", input_hash)
        
        # Get conversation context
        context = ""
        for msg in self.state.messages[-4:]:  # Last 4 messages for context
            context += f"{msg['role']}: {msg['content']}\n"
        
        result = self.sales_agent.process({
            "customer_message": user_message,
            "conversation_context": context
        })
        
        # Store extracted values
        if result.get("requested_amount"):
            self.state.requested_amount = result["requested_amount"]
        if result.get("tenure_months"):
            self.state.tenure_months = result["tenure_months"]
        if result.get("purpose"):
            self.state.purpose = result["purpose"]
        
        # Check if we have enough information
        if not self.state.requested_amount:
            return "What **amount** would you like to borrow? Please specify in rupees."
        
        if not self.state.tenure_months:
            return f"Got it, ₹{self.state.requested_amount:,.0f}. For **how many months** would you like the loan?"
        
        # We have both - move to KYC and process immediately
        self.state.stage = Stage.KYC_VERIFICATION
        
        # Process KYC and underwriting in one flow
        processing_msg = (
            f"Perfect! You want **₹{self.state.requested_amount:,.0f}** for **{self.state.tenure_months} months**.\n\n"
            f"Let me verify your details and process this request...\n\n"
        )
        
        # Immediately run KYC verification
        kyc_result = self._handle_kyc_verification(user_message)
        
        return processing_msg + kyc_result
    
    def _handle_kyc_verification(self, user_message: str) -> str:
        """
        KYC_VERIFICATION Stage: Verify customer KYC.
        """
        # Call Verification Agent
        input_hash = self.verification_agent.compute_input_hash({"phone": self.state.customer_phone})
        
        if not self.state.can_call_agent("VERIFICATION_AGENT", input_hash):
            self.state.terminal_state = TerminalState.LOAN_REJECTED
            self.state.stage = Stage.END
            return "There was an issue with the verification process. Please try again later."
        
        self.state.record_agent_call("VERIFICATION_AGENT", input_hash)
        
        result = self.verification_agent.process({"phone": self.state.customer_phone})
        
        if not result.get("kyc_verified"):
            self.state.terminal_state = TerminalState.LOAN_REJECTED
            self.state.stage = Stage.END
            return (
                f"I'm sorry, but we couldn't verify your details. {result.get('error', '')}\n\n"
                "Please ensure your KYC is complete and try again. Thank you!"
            )
        
        # KYC verified - update state with profile info
        profile = result.get("customer_profile", {})
        self.state.kyc_verified = True
        if profile.get("monthly_salary"):
            self.state.salary = profile["monthly_salary"]
        if profile.get("employer"):
            self.state.employer = profile["employer"]
        
        # Move to underwriting
        self.state.stage = Stage.UNDERWRITING
        return self._handle_underwriting(user_message)
    
    def _handle_underwriting(self, user_message: str) -> str:
        """
        UNDERWRITING Stage: Make credit decision.
        """
        # Prepare inputs for underwriting
        underwriting_inputs = {
            "requested_amount": self.state.requested_amount,
            "tenure_months": self.state.tenure_months,
            "preapproved_limit": self.state.preapproved_limit,
            "credit_score": self.state.credit_score,
            "interest_rate": self.state.interest_rate,
            "salary": self.state.salary if self.state.salary_slip_received else None
        }
        
        input_hash = self.underwriting_agent.compute_input_hash(underwriting_inputs)
        
        if not self.state.can_call_agent("UNDERWRITING_AGENT", input_hash):
            self.state.terminal_state = TerminalState.CUSTOMER_DROPPED
            self.state.stage = Stage.END
            return "We encountered an issue processing your application. Please try again later."
        
        self.state.record_agent_call("UNDERWRITING_AGENT", input_hash)
        
        result = self.underwriting_agent.process(underwriting_inputs)
        
        decision = result.get("decision")
        self.state.emi = result.get("emi")
        
        if decision == "APPROVED":
            self.state.decision = Decision.APPROVED
            self.state.stage = Stage.SANCTION
            return self._handle_sanction(user_message)
        
        elif decision == "NEED_SALARY_SLIP":
            self.state.decision = Decision.NEED_SALARY_SLIP
            self.state.stage = Stage.DOCUMENT_COLLECTION
            return (
                f"Almost there! Your requested amount of **₹{self.state.requested_amount:,.0f}** exceeds your pre-approved limit.\n\n"
                f"To process this, I need to verify your income. "
                f"Could you please **upload your latest salary slip** or confirm your monthly salary?"
            )
        
        else:  # REJECTED
            self.state.decision = Decision.REJECTED
            self.state.rejection_reason = result.get("reason", "Application not approved")
            self.state.stage = Stage.REJECTION
            return self._handle_rejection(user_message)
    
    def _handle_document_collection(self, user_message: str) -> str:
        """
        DOCUMENT_COLLECTION Stage: Collect salary slip.
        """
        # Check for decline/no response
        decline_keywords = ["no", "don't have", "can't provide", "later", "not now"]
        if any(keyword in user_message.lower() for keyword in decline_keywords):
            self.state.terminal_state = TerminalState.CUSTOMER_DROPPED
            self.state.stage = Stage.END
            return (
                "I understand. Without income verification, I'm unable to process this loan amount. "
                "You can still apply for a loan within your pre-approved limit of "
                f"₹{self.state.preapproved_limit:,.0f}. Thank you for your interest in Polaris!"
            )
        
        # Try to extract salary from message
        salary = self._extract_salary(user_message)
        
        if salary:
            self.state.salary = salary
            self.state.salary_slip_received = True
            
            # Re-run underwriting with salary
            self.state.stage = Stage.UNDERWRITING
            return self._handle_underwriting(user_message)
        
        # Check if they uploaded a document (simulated)
        if "uploaded" in user_message.lower() or "attached" in user_message.lower() or "salary slip" in user_message.lower():
            # Simulate salary extraction from document
            customer = lookup_customer_by_phone(self.state.customer_phone)
            if customer and customer.monthly_salary:
                self.state.salary = customer.monthly_salary
                self.state.salary_slip_received = True
                
                self.state.stage = Stage.UNDERWRITING
                return self._handle_underwriting(user_message)
        
        # Ask for salary if not provided
        self.state.terminal_state = TerminalState.ADDITIONAL_DOCUMENT_REQUIRED
        self.state.stage = Stage.END
        return (
            "I still need your salary details to proceed. "
            "Please share your **monthly salary amount** or **upload your salary slip**. "
            "You can reply later when you have the document ready."
        )
    
    def _handle_sanction(self, user_message: str) -> str:
        """
        SANCTION Stage: Generate sanction letter.
        """
        # Call Sanction Agent
        sanction_inputs = {
            "customer_name": self.state.customer_name,
            "customer_id": self.state.customer_id,
            "approved_amount": self.state.requested_amount,
            "tenure_months": self.state.tenure_months,
            "interest_rate": self.state.interest_rate,
            "emi": self.state.emi
        }
        
        input_hash = self.sanction_agent.compute_input_hash(sanction_inputs)
        self.state.record_agent_call("SANCTION_LETTER_GENERATOR", input_hash)
        
        result = self.sanction_agent.process(sanction_inputs)
        
        self.state.sanction_id = result.get("sanction_id")
        self.state.terminal_state = TerminalState.LOAN_SANCTIONED
        self.state.stage = Stage.END
        
        return (
            f"🎊 **Congratulations, {self.state.customer_name}!** 🎊\n\n"
            f"Your personal loan has been **APPROVED**!\n\n"
            f"📋 **Loan Details:**\n"
            f"- Sanction ID: `{self.state.sanction_id}`\n"
            f"- Approved Amount: **₹{self.state.requested_amount:,.0f}**\n"
            f"- Tenure: **{self.state.tenure_months} months**\n"
            f"- Interest Rate: **{self.state.interest_rate}% p.a.**\n"
            f"- Monthly EMI: **₹{self.state.emi:,.0f}**\n\n"
            f"💰 The loan amount will be disbursed to your registered bank account within **24 hours**.\n\n"
            f"Thank you for choosing **Polaris Personal Loans**! 🌟"
        )
    
    def _handle_rejection(self, user_message: str) -> str:
        """
        REJECTION Stage: Explain rejection politely.
        """
        self.state.terminal_state = TerminalState.LOAN_REJECTED
        self.state.stage = Stage.END
        
        reason = self.state.rejection_reason or "your application did not meet our criteria"
        
        return (
            f"I'm sorry, {self.state.customer_name or 'but'} we're unable to approve this loan at this time.\n\n"
            f"**Reason:** {reason}\n\n"
            f"📌 **What you can do:**\n"
            f"- Try applying for a smaller amount within your pre-approved limit\n"
            f"- Improve your credit score and reapply after 3-6 months\n"
            f"- Contact our customer support for more options\n\n"
            f"Thank you for considering Polaris Personal Loans."
        )
    
    def _handle_end(self, user_message: str) -> str:
        """
        END Stage: Conversation is over.
        """
        if self.state.terminal_state == TerminalState.LOAN_SANCTIONED:
            return (
                "Your loan has been sanctioned! Is there anything else I can help you with regarding your loan?"
            )
        else:
            return (
                "This conversation has ended. "
                "If you'd like to start a new loan application, please refresh and start again. "
                "Thank you!"
            )
    
    def _extract_phone_number(self, text: str) -> Optional[str]:
        """Extract 10-digit phone number from text."""
        import re
        # Remove common prefixes and clean
        text = text.replace("+91", "").replace("-", "").replace(" ", "")
        
        # Find 10 digit number
        match = re.search(r'\d{10}', text)
        if match:
            return match.group()
        return None
    
    def _extract_salary(self, text: str) -> Optional[float]:
        """Extract salary amount from text."""
        import re
        
        # Handle lakh notation
        lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b', text.lower())
        if lakh_match:
            return float(lakh_match.group(1)) * 100000
        
        # Handle k notation
        k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text.lower())
        if k_match:
            return float(k_match.group(1)) * 1000
        
        # Handle plain numbers (assume rupees if > 10000)
        number_match = re.search(r'(?:rs\.?|₹|inr)?\s*(\d{4,7})', text.lower())
        if number_match:
            return float(number_match.group(1))
        
        return None
