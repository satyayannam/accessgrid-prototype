# AccessGrid Integration Playground

A local Python / Streamlit prototype for walking through mobile credential issuance, lifecycle commands, webhook delivery and partner-side state recovery. It demonstrates API contract literacy, integration debugging and operational reasoning with a deterministic support assistant.

**SYNTHETIC DEMO — NO PRODUCTION CREDENTIALS**

This project is not affiliated with AccessGrid and does not connect to AccessGrid production systems.

## Run locally

Requires Python 3.11+ (verified on Python 3.11.3 / Windows). From this directory:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>. No account, environment variables or API keys are needed. Streamlit is the only direct dependency. Tests use Python's built-in unittest and Streamlit's bundled AppTest.

An isolated environment is recommended. This workspace already contains a freshly installed `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

For a new checkout, create it first with `python -m venv .venv`. Run from this directory so `.streamlit/config.toml` applies. Do not start a second server on the same port; use `--server.port 8502` if necessary. Use Ctrl+C in the server terminal to stop it.

## What to explore

- **Pass workspace:** fill a synthetic identity, issue, inspect the exchange, simulate installation and manage lifecycle. Invalid transitions show feedback without emitting events.
- **Webhook console:** inspect CloudEvents, repeat deliveries, simulate failures, send a distinct older event, and export the synthetic trace.
- **Integration Assistant:** seven deterministic diagnostic playbooks. No LLM, inference service or AI API is called.
- **Architecture:** proposed command/event paths, trust boundaries and reliability tradeoffs.
- **What I Would Build Next:** retrieval-grounded support, preflight validation, trace exploration, integration health and authorized agent tools.

The top panel counts provider pass states and delivery attempts. Failed deliveries count historical failures, including subsequently recovered ones. Latencies are explicit synthetic samples, not measurements. Last event is an occurrence timestamp in UTC, not the last delivery attempt.

## Public contract mapping

Reviewed 13 October 2026 against [Access Pass API](https://accessgrid.com/docs/access-pass), [authentication](https://accessgrid.com/docs), [state transitions](https://accessgrid.com/guides/knowledgebase/how-the-state-transitions-work-for-passes-on-accessgrid), and [webhook guide](https://accessgrid.com/guides/knowledgebase/how-to-set-up-webhooks-on-accessgrid).

| Operation | Modeled request |
| --- | --- |
| Issue | `POST /v1/key-cards` |
| Suspend / resume / unlink / delete | `POST /v1/key-cards/{card_id}/{action}` with `card_id` in JSON |
| Wallet installation | Local device simulation, not an invented API endpoint |

Headers use literal placeholders. Preference selects a synthetic platform template. The request includes employee attributes, dates, metadata and synthetic H10301 values. Events use `ag.access_pass.issued`, `activated`, `suspended`, `resumed`, `unlinked` and `deleted` in a CloudEvents envelope. See source links above for the full contract.

### Explicit ambiguities and simplifications

- The issue sample returns `active`; the lifecycle guide says a new pass is `created` until installed. We follow the latter explanation.
- The state guide contradicts itself about resuming `unlink`; its reinstall description also differs from endpoint prose. This demo permits resume only from `suspended` and makes no reinstall guarantee. Confirm that edge case with AccessGrid.
- The wire state is `unlink`; the event suffix is `unlinked`.
- Device objects and expanded snapshot fields enrich the demo; they are not verified against every provider event schema. No remote schema is fetched at runtime.
- The envelope models customer events with `/accessgrid/customer`; it is generated locally. This does not simulate the provider console's special Send Test delivery mode.

## Architecture and reliability

```text
Streamlit UI → MockAccessGrid → immutable event snapshots
                                  ↓
                              EventProcessor
                                  ↓
                 deduplication inbox + partner projection
                                  ↓
                     delivery log / health / timeline
```

Provider state and partner state are intentionally separate. A failed delivery can leave them different. Select the failed event and retry it to recover. A simulated failure returns 500 before committing anything. A duplicate receives 200 and does not repeat the business action. The duplicate button delivers twice so it can demonstrate a repeat even for an unprocessed event.

The processor deduplicates `(source, id)`. An older or equal timestamp is logged and acknowledged without replacing newer state. A deliberately delayed fixture gets a **new ID** so it exercises ordering, not just deduplication. This timestamp guard is a demo heuristic: production should reconcile against current provider state, especially for equal timestamps or missing events.

Sequential mock actions receive strictly increasing logical timestamps, even if the host clock repeats. This is a simulator convenience, not a provider ordering guarantee.

The webhook guide specifies 200/201 for successful acknowledgement. Documented retries use backoff, with a six-hour window; this app uses manual delivery controls and has no background retry scheduler. It does not implement an HTTPS receiver, challenge handshake, bearer validation or mTLS. Those belong in a production adapter, not in a pretend live integration.

## Why all data is synthetic

There are no AccessGrid credentials available for this prototype, and no production connection is implied. Names default to `Demo Employee 001`, emails must use `@example.invalid`, IDs use demo prefixes, and install links use the reserved `.invalid` domain. The app contains no outbound API client, signing secret, credential entry box or wallet provisioning code. Documentation links open only if clicked by the viewer.

Data lives in the current Streamlit session, not a persistent database. Reset clears the session. Refresh, disconnection or restart may lose data; generate the meeting trace live. Do not enter real personal information.

## Production requirements

Use an official SDK or tested server-side signing helper and a secret manager. Add tenant isolation, authorization and audit logs; validate real template and platform constraints. Authenticate webhook deliveries, validate schemas, and acknowledge only after durable acceptance. Commit inbox uniqueness and state changes atomically in a database, queue slower processing, use an outbox for external effects, add dead-letter handling and reconcile periodically. Redact sensitive payloads in traces. Verify schema versions and lifecycle ambiguities with AccessGrid before implementing them.

The deterministic assistant is a support demonstration. A future LLM should retrieve cited, versioned documentation, be evaluated on real support tasks, abstain on uncertainty and require authorization before taking sensitive actions.

## Project structure

```text
accessgrid_demo/
  app.py                      # Streamlit workflow and session state
  mock_accessgrid.py           # Mock commands, validation and event snapshots
  event_processor.py          # Delivery, deduplication and local projection
  integration_assistant.py    # Deterministic support playbooks
  models.py                   # Typed pass and delivery models
  ui_content.py               # Theme, architecture and next-step content
  requirements.txt
  README.md
  DEMO_SCRIPT.md
  VERIFICATION.md
  .streamlit/config.toml
  tests/
    test_lifecycle.py
    test_webhooks.py
    test_ui.py
```

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the exact meeting clicks and talking points, and [VERIFICATION.md](VERIFICATION.md) for executed checks and limits.
