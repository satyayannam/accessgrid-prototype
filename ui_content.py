"""Static presentation and architecture content."""
import streamlit as st

DOCS = "https://accessgrid.com/docs/access-pass"
WEBHOOKS = "https://accessgrid.com/guides/knowledgebase/how-to-set-up-webhooks-on-accessgrid"
STATES = "https://accessgrid.com/guides/knowledgebase/how-the-state-transitions-work-for-passes-on-accessgrid"

CSS = """
<style>
.block-container {max-width:1440px;padding-top:2.8rem;padding-bottom:3rem}
h1 {font-size:2.6rem!important;letter-spacing:-1.3px;font-weight:720!important}
h2 {letter-spacing:-.6px} h3 {font-size:1.15rem!important}
[data-testid="stSidebar"] {background:#0e1520;border-right:1px solid #253043}
[data-testid="stMetric"] {background:#121c2a;border:1px solid #253248;border-radius:12px;padding:15px}
[data-testid="stMetricValue"] {font-size:1.65rem}
[data-testid="stMetricLabel"] {color:#9aacc5;font-size:.8rem}
[data-testid="stExpander"] {border-color:#293549}
.eyebrow {font:600 11px monospace;letter-spacing:2px;color:#65e0c2;margin-bottom:8px}
.demo-badge {display:inline-block;border:1px solid #48634e;background:#172b24;color:#a3e7b8;padding:7px 11px;border-radius:6px;font:600 10px monospace;letter-spacing:1px}
.subtle {color:#9baac0;font-size:14px;line-height:1.7}
.wallet {border:1px solid #4d6886;border-radius:18px;background:linear-gradient(135deg,#233a52,#131e2e);padding:25px;margin:10px 0 20px;min-height:230px}
.wallet h2 {font-size:25px!important;margin:22px 0 4px}.wallet .tag{color:#83edd0;font:12px monospace}
.flow {border:1px solid #334057;border-radius:12px;padding:22px;background:#121c2a;color:#b2e7dc;font:14px monospace;line-height:2.4;margin:12px 0}
.timeline {border-left:2px solid #365363;padding:2px 0 16px 18px;margin-left:5px}
.timeline b{font-size:14px}.timeline small{color:#a5b4c9;font:11px monospace}
button {border-radius:7px!important} [data-testid="stTabs"] button {font-size:14px}
</style>
"""


def architecture():
    st.subheader("Two paths. One consistent integration.")
    st.caption("Proposed production architecture • the working demo runs entirely in session memory")
    st.markdown('<div class="eyebrow">COMMAND PATH</div><div class="flow">Partner App → Partner Backend → AccessGrid API → Mobile Credential / Wallet</div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">EVENT PATH</div><div class="flow">AccessGrid → Webhook → Partner Receiver → Durable Queue / Processor → Application DB / Downstream Systems</div>', unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        with st.container(border=True):
            st.markdown("### Protect the boundary")
            st.write("API signing belongs on the backend. Use scoped access, a secret manager and redacted logs. Webhook authentication uses bearer tokens or mTLS; it is distinct from API HMAC.")
            st.write("Verify endpoint ownership with the documented challenge handshake. Validate event shape before accepting it.")
    with b:
        with st.container(border=True):
            st.markdown("### Make delivery recoverable")
            st.write("Acknowledge with 200/201 after durable acceptance. Process slower work asynchronously. Commit the inbox ID and local state together; use an outbox for downstream effects.")
            st.write("Log event IDs, attempts and state changes. Share SDK/signing helpers across customer adapters; isolate tenant policy and mappings.")
    with st.expander("Contract notes & documented ambiguities", expanded=True):
        st.markdown(f"Reviewed **13 October 2026**: [API contract]({DOCS}), [authentication](https://accessgrid.com/docs), [webhooks]({WEBHOOKS}), [state guide]({STATES}).")
        st.write("The issue-response example shows active, but the state guide says created until installation; this demo follows the explicit lifecycle explanation. The guide contradicts itself on resuming unlink, and disagrees with the endpoint prose on reinstall behavior. We only allow resume from suspended and make no reinstall guarantee. Confirm unlink recovery with AccessGrid.")
        st.write("Wallet preference selects a synthetic platform-specific template; it is not an invented API parameter. Device fields and expanded event data are demo enrichments, not a claim of exact schema validation. IDs, HTTP results and latencies are synthetic. Local validation messages are not quoted server errors.")
        st.write("Production ordering needs reconciliation with current resource state. Timestamps alone are not a resource version. This demo uses an explicit timestamp guard and treats equal timestamps as ambiguous.")


def next_steps():
    st.subheader("What I Would Build Next")
    st.caption("Proposals for extending this prototype • no claim that these are missing from AccessGrid")
    items = [
        ("01 / Integration Copilot", "Retrieve versioned docs and return cited API examples, error explanations and state guidance. Evaluate against known support cases; abstain when evidence is insufficient."),
        ("02 / Preflight Validator", "Validate schemas, platform-specific fields and template constraints before a request. Offer corrected examples; keep validation deterministic and require review before sending."),
        ("03 / Webhook Trace Explorer", "Connect an event to response codes, retry attempts, local mutations and downstream workflows. Make a single event ID the entry point for debugging."),
        ("04 / Customer Integration Health", "Detect passes stuck before activation, repeated delivery failures and state mismatches. Establish baselines and actionable alerts before adding anomaly models."),
        ("05 / MCP & authorized agents", "Wrap narrowly scoped actions with deterministic tools, tenant boundaries, least privilege, audit records and explicit confirmation for sensitive actions. An assistant can explain an action before an authorized operator commits it."),
    ]
    for title, body in items:
        with st.container(border=True):
            st.markdown("### " + title)
            st.write(body)
    st.info("Start with traceability and deterministic validation. Add AI where retrieval and explanation help a developer resolve a real issue.")
