from typing import Optional
from factoring.mock_data import get_back_office_dataset


class DemoStore:
    def __init__(self):
        self.reset()

    def reset(self):
        self.debtors, self.invoices, self.payments = get_back_office_dataset()
        self.recon_result = None          # last ReconciliationAgent.process() output
        self.audit_trail: list = []       # accumulated audit entries (system + human)
        self.cases = None                 # dict[case_id, CollectionCase] after build-queue
        self.collections_agent = None
        self.case_logs: dict = {}         # case_id -> list of {role, message, channel, ts}


store = DemoStore()
