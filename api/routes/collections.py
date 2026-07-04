from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.state import store
from factoring import CollectionsAgent
from factoring.collections_fsm import CollectionOutcome

router = APIRouter(prefix="/api/collections")


def _case_dict(case) -> dict:
    d = case.to_dict()
    debtor = store.debtors.get(case.debtor_id)
    d["debtor_name"] = debtor.name if debtor else case.debtor_id
    return d


def _get_case(case_id: str):
    if store.cases is None or case_id not in store.cases:
        raise HTTPException(status_code=404, detail=f"Unknown case {case_id}")
    return store.cases[case_id]


class SendReminderBody(BaseModel):
    language: str = "en"


class ReplyBody(BaseModel):
    text: str
    promise_date: Optional[date] = None


@router.post("/build-queue")
def build_queue():
    """Prioritize past-due invoices into a fresh collections queue."""
    store.collections_agent = CollectionsAgent()
    cases = store.collections_agent.prioritize(store.invoices, store.debtors)
    store.cases = {c.case_id: c for c in cases}
    ordered = sorted(store.cases.values(), key=lambda c: c.priority_score, reverse=True)
    return [_case_dict(c) for c in ordered]


@router.get("/cases")
def list_cases():
    """List all cases in the current queue."""
    if store.cases is None:
        return []
    ordered = sorted(store.cases.values(), key=lambda c: c.priority_score, reverse=True)
    return [_case_dict(c) for c in ordered]


@router.get("/cases/{case_id}")
def case_detail(case_id: str):
    """Single case detail with recent history and message log."""
    case = _get_case(case_id)
    d = _case_dict(case)
    d["history"] = case.history[-10:]
    d["log"] = store.case_logs.get(case_id, [])[-8:]
    return d


@router.post("/cases/{case_id}/send-reminder")
def send_reminder(case_id: str, body: SendReminderBody):
    """Draft and send the next dunning reminder on the case."""
    case = _get_case(case_id)
    invoice = next((i for i in store.invoices if i.invoice_id == case.invoice_id), None)
    if invoice is None:
        raise HTTPException(status_code=404, detail=f"Invoice {case.invoice_id} not found")
    debtor = store.debtors.get(case.debtor_id)
    if debtor is None:
        raise HTTPException(status_code=404, detail=f"Debtor {case.debtor_id} not found")

    agent = store.collections_agent or CollectionsAgent()
    store.collections_agent = agent

    outcome, message = agent.run_outreach(case, invoice, debtor, language=body.language)

    log = store.case_logs.setdefault(case_id, [])
    channel = case.channel_history[-1] if case.channel_history else None
    if outcome is CollectionOutcome.OK:
        log.append({
            "role": "agent",
            "message": message,
            "channel": channel,
            "ts": datetime.now().isoformat(),
        })
    else:
        log.append({
            "role": "blocked",
            "message": f"Send blocked by FSM: {outcome.value}",
            "channel": None,
            "ts": datetime.now().isoformat(),
        })

    return {
        "outcome": outcome.value,
        "message": message,
        "channel": channel,
        "case": _case_dict(case),
    }


@router.post("/cases/{case_id}/retry-duplicate-send")
def retry_duplicate_send(case_id: str):
    """Reproduce app.py's 'Retry identical send' guard demo: re-send the
    last agent message verbatim, which the FSM must block as a duplicate."""
    case = _get_case(case_id)
    log = store.case_logs.setdefault(case_id, [])

    last_message = next(
        (entry["message"] for entry in reversed(log) if entry.get("role") == "agent"),
        None,
    )
    if not case.sent_message_hashes or last_message is None:
        log.append({
            "role": "blocked",
            "message": "Nothing sent yet - send a reminder first",
            "channel": None,
            "ts": datetime.now().isoformat(),
        })
        return {"outcome": None, "case": _case_dict(case)}

    case.start_outreach()
    outcome, _sent = case.send_message(last_message)

    log.append({
        "role": "blocked" if outcome is not CollectionOutcome.OK else "agent",
        "message": f"Duplicate send attempt: {outcome.value}",
        "channel": None,
        "ts": datetime.now().isoformat(),
    })

    return {"outcome": outcome.value, "case": _case_dict(case)}


@router.post("/cases/{case_id}/escalate")
def escalate(case_id: str):
    """Attempt to escalate a case to a human collector (gated)."""
    case = _get_case(case_id)
    outcome = case.escalate()

    log = store.case_logs.setdefault(case_id, [])
    log.append({
        "role": "blocked" if outcome is not CollectionOutcome.OK else "agent",
        "message": f"Escalation attempt: {outcome.value}",
        "channel": None,
        "ts": datetime.now().isoformat(),
    })

    return {"outcome": outcome.value, "case": _case_dict(case)}


@router.post("/cases/{case_id}/reply")
def reply(case_id: str, body: ReplyBody):
    """Simulate a debtor reply and route it through the FSM."""
    case = _get_case(case_id)
    agent = store.collections_agent or CollectionsAgent()
    store.collections_agent = agent

    outcome = agent.handle_response(case, body.text, body.promise_date)

    log = store.case_logs.setdefault(case_id, [])
    log.append({
        "role": "debtor",
        "message": body.text,
        "channel": None,
        "ts": datetime.now().isoformat(),
    })
    log.append({
        "role": "agent",
        "message": f"Response classified, case now in {case.stage.value}",
        "channel": None,
        "ts": datetime.now().isoformat(),
    })

    return {"outcome": outcome.value, "case": _case_dict(case)}
