"""Deterministic support playbooks, not an LLM."""
PLAYBOOKS = {
    "Webhook keeps retrying": (
        "The receiver timed out or returned a status other than 200/201.",
        "Correlate event ID with attempts, response codes, receiver logs and queue health.",
        "Authenticate, durably enqueue, then return 200 or 201 quickly. Retry the same event ID safely.",
        "Use a transactional inbox, queue workers, dead-letter handling and structured traces. Generic 2xx advice is insufficient: these docs specify 200/201."),
    "API authentication/signature error": (
        "The account identifier or signature does not match the transmitted payload.",
        "Check X-ACCT-ID; serialize once and sign base64 of those exact JSON bytes with HMAC-SHA256, using the hex digest. GET/DELETE use sig_payload.",
        "Use the official SDK or a shared signing helper server-side. Never log secrets or signature material.",
        "Add redacted request traces, secret rotation and fixture-based signing tests. Webhook bearer/mTLS auth is separate from API HMAC."),
    "Credential is suspended": (
        "An administrative action or device-loss flow disabled the credential.",
        "Inspect the latest pass state, suspension event and authorized operator intent.",
        "After authorization, resume a suspended pass using the documented endpoint.",
        "Add scoped operator roles, audit logs and incident links; do not automatically resume lost-device credentials."),
    "Pass issued but user hasn't activated it": (
        "Issuance produced an install link; the holder may not have completed wallet installation.",
        "Check created state, install-link delivery, compatible template/platform and activation events.",
        "Guide the synthetic holder through installation; here use Simulate wallet install.",
        "Measure time to activation and offer privacy-conscious reminders. Do not equate issued with usable."),
    "Local database state does not match AccessGrid": (
        "A failed, delayed or missed delivery may have left the projection behind.",
        "Compare authoritative GET state with local state, event timestamps and delivery history.",
        "Retry failed events; reconcile the current resource before applying ambiguous historical events.",
        "Run periodic reconciliation and commit deduplication plus business changes atomically. Timestamp ordering alone is only a demo heuristic."),
    "Duplicate webhook": (
        "At-least-once delivery or a lost acknowledgement caused a redelivery.",
        "Compare CloudEvents source and id, attempt history and committed business effects.",
        "Acknowledge the duplicate with 200 without repeating the business action.",
        "Persist a unique (source, id) inbox key; use an outbox for external effects and retain IDs beyond the retry horizon."),
    "Unknown integration error": (
        "There is insufficient evidence to identify a cause.",
        "Collect redacted endpoint, method, status, event ID, timestamp and a minimal reproduction.",
        "Consult the linked documentation and escalate with the trace; do not invent a fix.",
        "A retrieval-grounded copilot could cite sources, express uncertainty and hand off to a human."),
}


def diagnose(scenario: str) -> dict[str, str]:
    values = PLAYBOOKS.get(scenario, PLAYBOOKS["Unknown integration error"])
    return dict(zip(("LIKELY CAUSE", "WHAT I WOULD CHECK", "RECOMMENDED FIX", "PRODUCTION IMPROVEMENT"), values))
