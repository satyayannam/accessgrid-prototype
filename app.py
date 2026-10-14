from dataclasses import asdict
from html import escape
import json
import streamlit as st
from mock_accessgrid import MockAccessGrid, make_payload
from event_processor import EventProcessor
from integration_assistant import PLAYBOOKS, diagnose
from ui_content import CSS, architecture, next_steps

st.set_page_config(page_title="AccessGrid Integration Playground", page_icon="▦", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
if "api" not in st.session_state:
    st.session_state.api = MockAccessGrid()
    st.session_state.processor = EventProcessor()
api = st.session_state.api
processor = st.session_state.processor

with st.sidebar:
    st.markdown("## ▦ Integration lab")
    st.caption("ACCESSGRID / INDEPENDENT PROTOTYPE")
    st.divider()
    st.markdown("**Meeting mode**")
    st.write("01  Issue a credential\n\n02  Exercise its lifecycle\n\n03  Break delivery safely\n\n04  Explain the architecture")
    st.divider()
    st.caption("RUNTIME")
    st.markdown("● Local simulation\n\n● No API credentials\n\n● Session-only data")
    st.caption("Refresh or restart may clear the session. Use only obvious synthetic examples.")
    if st.button("Reset demo", width="stretch"):
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.markdown("[Public API docs](https://accessgrid.com/docs/access-pass)")
    st.caption("Contract reviewed 13 Oct 2026")

left, right = st.columns([3, 2])
with left:
    st.markdown('<div class="eyebrow">DEVELOPER INFRASTRUCTURE / WORKING PROTOTYPE</div>', unsafe_allow_html=True)
    st.title("AccessGrid Integration Playground")
    st.markdown('<div class="subtle">Issue a pass. Follow the event. Understand the failure.</div>', unsafe_allow_html=True)
with right:
    st.markdown('<div style="text-align:right;padding-top:15px"><span class="demo-badge">SYNTHETIC DEMO — NO PRODUCTION CREDENTIALS</span></div>', unsafe_allow_html=True)
st.write("")
metrics = st.columns(6)
latencies = [d.latency_ms for d in processor.deliveries]
values = [sum(p.state == "active" for p in api.passes.values()),
          sum(p.state == "suspended" for p in api.passes.values()),
          sum(d.outcome == "failed" for d in processor.deliveries),
          sum(d.outcome == "duplicate" for d in processor.deliveries),
          f"{sum(latencies)/len(latencies):.0f} ms" if latencies else "—",
          max((e["time"] for e in api.events), default="")[11:19] or "—"]
for col, label, value in zip(metrics, ["Active passes", "Suspended", "Failed deliveries", "Duplicates", "Avg. simulated latency", "Last event / UTC"], values):
    col.metric(label, value)
st.write("")
tabs = st.tabs(["Pass workspace", "Webhook console", "Integration Assistant", "Architecture", "What I Would Build Next"])

with tabs[0]:
    form_col, detail_col = st.columns([1, 1.2], gap="large")
    with form_col:
        st.subheader("01 / Issue an access pass")
        st.caption("Corporate credential • synthetic H10301 values: site 42 / card 1001")
        with st.form("issue_pass"):
            name = st.text_input("Full name", "Demo Employee 001")
            email = st.text_input("Email", "demo001@example.invalid")
            c1, c2 = st.columns(2)
            employee_id = c1.text_input("Employee ID", "DEMO-001")
            department = c2.selectbox("Department", ["Engineering", "Operations", "Demo Support"])
            title = st.text_input("Job title", "Demo Engineer")
            site = st.selectbox("Site / building", ["Demo Lab A", "Demo Lab B"])
            c1, c2 = st.columns(2)
            classification = c1.selectbox("Credential classification", ["full_time", "contractor"])
            platform = c2.selectbox("Wallet preference", ["Apple Wallet", "Google Wallet"])
            template = st.text_input("Card template ID", "tpl_demo_employee")
            st.caption("A platform suffix is added to the template ID. No wallet preference parameter is sent to the API.")
            if st.form_submit_button("Issue Pass", type="primary", width="stretch"):
                try:
                    platform_id = "apple" if platform == "Apple Wallet" else "android"
                    card, event = api.issue(make_payload(name, email, employee_id, department, title, site, classification, template + "_" + platform_id), platform_id)
                    processor.deliver(event)
                    st.session_state.selected_pass = card.id
                    st.session_state.notice = "Pass issued. Simulate wallet installation to activate it."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with detail_col:
        st.subheader("02 / Credential lifecycle")
        if not api.passes:
            st.markdown('<div class="wallet"><span class="tag">READY TO PROVISION</span><h2>Your first synthetic pass</h2><p class="subtle">Issue a credential to inspect the contract,<br>simulate wallet installation, and follow its lifecycle.</p></div>', unsafe_allow_html=True)
            st.info("No seeded successes. Every event in this workspace comes from an action you take.")
        else:
            selected = st.selectbox("Selected credential", list(api.passes), key="selected_pass",
                                    format_func=lambda x: f"{api.passes[x].payload['employee_id']} · {x}")
            card = api.passes[selected]
            local_state = processor.local.get(selected, {}).get("state", "missing")
            st.markdown(f'<div class="wallet"><span class="tag">{escape(card.platform.upper())} / {escape(card.state.upper())}</span><h2>{escape(card.payload["full_name"])}</h2><p>{escape(card.payload["department"])} · {escape(card.payload["site_name"])}</p><small>{escape(card.id)}</small></div>', unsafe_allow_html=True)
            st.caption(f"Simulated provider: {card.state}  ·  Partner projection: {local_state}")
            if card.state != local_state:
                st.warning("State mismatch — inspect deliveries and retry the failed event.")
            if "notice" in st.session_state:
                st.info(st.session_state.notice)
            fail_next = st.checkbox("Fail lifecycle webhook deliveries (HTTP 500)", key="fail_next")
            actions = [("Simulate wallet install", "activate"), ("Suspend", "suspend"), ("Resume", "resume"), ("Unlink", "unlink"), ("Delete", "delete")]
            action_columns = [st.container(), *st.columns(4)]
            for col, (label, action) in zip(action_columns, actions):
                if col.button(label, width="stretch"):
                    try:
                        event = api.transition(selected, action)
                        result = processor.deliver(event, fail=fail_next)
                        st.session_state.notice = f"{event['type']} · HTTP {result.http_status} · {result.message}"
                    except ValueError as exc:
                        st.session_state.notice = str(exc)
                    st.rerun()
            st.caption("Invalid actions return local validation feedback. Delete is terminal. Unlink recovery is deliberately conservative; see Architecture.")
            with st.expander("Pass timeline", expanded=True):
                for event in [e for e in api.events if e["data"]["id"] == selected]:
                    stale = any(d.event_id == event["id"] and d.outcome == "out_of_order" for d in processor.deliveries)
                    marker = " ⚠ OUT OF ORDER" if stale else ""
                    st.markdown(f'<div class="timeline"><b>{escape(event["type"].split(".")[-1].title())}{marker}</b><br><small>{escape(event["time"])}<br>{escape(event["id"])}</small></div>', unsafe_allow_html=True)
    st.divider()
    st.subheader("Developer exchange")
    st.caption("Display only. No network requests are sent. Response includes synthetic snapshot enrichments.")
    if api.last_exchange:
        a, b = st.columns(2)
        with a:
            st.markdown("**REQUEST**")
            st.json(api.last_exchange["request"], expanded=True)
        with b:
            st.markdown("**MOCK RESPONSE**")
            st.json(api.last_exchange["mock_response"], expanded=True)

with tabs[1]:
    st.subheader("Webhook console")
    st.caption("CloudEvents 1.0 • separate event occurrence and delivery attempts • all transport is simulated")
    if not api.events:
        st.info("Issue a pass to generate the first event.")
    else:
        event_id = st.selectbox("Event", [e["id"] for e in reversed(api.events)],
                                format_func=lambda x: next(f"{e['type']} · {x}" for e in api.events if e["id"] == x))
        event = next(e for e in api.events if e["id"] == event_id)
        c1, c2, c3, c4 = st.columns(4)
        result = None
        if c1.button("Deliver / retry · 200", width="stretch"):
            result = processor.deliver(event)
        if c2.button("Consumer failure · 500", width="stretch"):
            result = processor.deliver(event, fail=True)
        if c3.button("Duplicate delivery", width="stretch"):
            processor.deliver(event)
            result = processor.deliver(event)
        if c4.button("Delayed / out-of-order", width="stretch"):
            result = processor.deliver(api.delayed_event(event["data"]["id"]))
        if result:
            st.session_state.delivery_notice = f"HTTP {result.http_status} · {result.message}"
            st.rerun()
        if "delivery_notice" in st.session_state:
            st.info(st.session_state.delivery_notice)
        a, b = st.columns([1.1, 1])
        with a:
            st.markdown("**EVENT PAYLOAD**")
            st.json(event, expanded=True)
        with b:
            st.markdown("**PROCESSOR STATE**")
            st.metric("Committed business actions", processor.business_actions)
            st.caption(f"{len(processor.processed_ids)} unique source / event IDs recorded")
            st.json({"provider_state": api.passes[event["data"]["id"]].state,
                     "partner_state": processor.local.get(event["data"]["id"], {}).get("state", "missing"),
                     "watermark": str(processor.watermarks.get(event["data"]["id"], "none"))})
            st.markdown("**DELIVERY CONTRACT**")
            st.code('Content-Type: application/cloudevents+json\nAuthorization: Bearer <WEBHOOK_TOKEN>', language="http")
            st.write("200/201 acknowledge delivery. Failure is recorded before deduplication and commits nothing. A duplicate is acknowledged without repeating work; an older event is logged without rolling state back.")
            st.caption("Retry controls are manual. Synthetic latency is illustrative, not a benchmark. Duplicate delivery sends twice to guarantee a redelivery example.")
        st.markdown("**DELIVERY ATTEMPTS · NEWEST FIRST**")
        st.dataframe([asdict(d) for d in reversed(processor.deliveries)], width="stretch", hide_index=True)
        st.download_button("Export synthetic trace", json.dumps({"events": api.events, "deliveries": [asdict(d) for d in processor.deliveries]}, indent=2), "synthetic_trace.json", "application/json")

with tabs[2]:
    st.subheader("Integration Assistant")
    st.caption("DETERMINISTIC PLAYBOOKS / NOT AN LLM")
    scenario = st.selectbox("What are you investigating?", list(PLAYBOOKS))
    for label, text in diagnose(scenario).items():
        with st.container(border=True):
            st.markdown(f"**{label}**")
            st.write(text)
    st.markdown("[API authentication](https://accessgrid.com/docs) · [Webhook delivery guide](https://accessgrid.com/guides/knowledgebase/how-to-set-up-webhooks-on-accessgrid)")
with tabs[3]:
    architecture()
with tabs[4]:
    next_steps()
st.divider()
st.caption("This project is not affiliated with AccessGrid and does not connect to AccessGrid production systems.")
