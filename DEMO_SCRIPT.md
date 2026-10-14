# Founder demo — 3 to 5 minutes

## Before the meeting

Start the app from the project directory and open <http://localhost:8501>. Click **Reset demo**. Keep **Pass workspace** open. Use the default synthetic fields. Nothing needs an API account or internet access once installed.

## 0:00–0:25 · Set the context

Say exactly:

> I went through your API docs because I wanted to understand the developer surface before we met. Obviously I don't have AccessGrid credentials, so instead of pretending this was a production integration, I modeled the public contract with synthetic data.

Point to the synthetic badge. Say: “I treated this as an evening-sized learning exercise: understand the contract, make state visible, and explore a few integration failures.”

## 0:25–0:55 · Issue and inspect

**Tab:** Pass workspace. **Click:** Issue Pass. Scroll to **Developer exchange**.

Say: “This is the modeled request and mock response. The account and signature are placeholders. The platform chooses a template, and the response gives us an inert install link.”

Emphasize: the payload is separate from UI preferences; secrets belong on the backend. Scroll back to the credential.

## 0:55–1:15 · Activate and suspend

**Click:** Simulate wallet install, then Suspend.

Say: “Issuance and installation are distinct. This button represents the device flow; it isn't an invented activation endpoint. Once installed, I can suspend the pass and inspect the resulting event.”

Emphasize: guarded transitions, explicit `created → active → suspended` state, immutable timeline. Optionally click Suspend again to show useful validation.

## 1:15–1:40 · Duplicate delivery

**Tab:** Webhook console. The newest event should be `ag.access_pass.suspended`.
**Click:** Duplicate delivery.

Say: “The same event can arrive more than once. I acknowledge it, but the committed business-action count stays at three. In production I'd commit the inbox record and state change in one database transaction.”

Point to the duplicate notice, unchanged count and delivery attempts.

## 1:40–2:00 · Failure and diagnosis

**Click:** Consumer failure · 500.
**Tab:** Integration Assistant. **Select:** Webhook keeps retrying.

Say: “A consumer failure must remain retryable. This assistant is explicitly rule-based. It explains what evidence to collect and recommends durable acceptance followed by quick acknowledgement and asynchronous processing.”

Emphasize: deterministic support first; no claim of an LLM. The guide specifically calls for 200/201, so avoid saying every 2xx is accepted.

## 2:00–2:30 · Architecture

**Tab:** Architecture.

Say: “Commands and events cross different trust boundaries. Signing stays server-side; webhook authentication is separate. Shared helpers should serve multiple customer adapters, while tenant policy remains isolated. The prototype uses memory; production needs durable storage, transactional processing and reconciliation.”

Point to the two paths. Mention: “I also noted a docs ambiguity around unlink recovery rather than guessing.”

## 2:30–3:00 · What comes next

**Tab:** What I Would Build Next.

Say: “I'd start with traceability and deterministic preflight checks. Then I'd add a retrieval-grounded copilot that cites the docs and connects an error to an event trace. Agent tools would use scoped wrappers, audit logs and confirmation for sensitive actions. These are proposals for this prototype, not claims about what AccessGrid does or doesn't have.”

Finish with one question from the list below.

## Optional extension to 5 minutes · Show recovery and stale events

1. **Pass workspace:** check **Fail lifecycle webhook deliveries (HTTP 500)**; click **Resume**. Provider becomes active; partner projection remains suspended. Uncheck the failure control.
2. **Webhook console:** select the newest resumed event; click **Deliver / retry · 200**. The projection catches up. This is a meaningful recovery example, unlike replaying an event already processed successfully.
3. Click **Delayed / out-of-order**. The older event has a distinct ID; it is flagged without rolling state back. Check **Pass timeline** to see the warning.
4. Explain: “Timestamp ordering is a teaching heuristic. Production should reconcile current resource state when ordering is ambiguous.”
5. Optionally click **Export synthetic trace** to show the events and attempt log as a portable debugging artifact.

## 30-second explanation

“This is a synthetic integration playground built around AccessGrid's public API concepts. It issues a mock pass, models wallet activation and lifecycle changes, and keeps provider state separate from a partner's webhook-driven projection. I can replay duplicates, fail delivery and inject stale events to explain idempotency and recovery. The support assistant is deterministic; the AI proposal is a cited, retrieval-grounded extension. Nothing connects to production.”

## Five questions for the founder

1. Where do customer integrations most often stall: template configuration, wallet activation, credential encoding, or keeping downstream systems synchronized?
2. What is the recommended recovery flow after unlinking? I noticed different descriptions of resume and reinstall behavior in the public docs.
3. When webhook ordering is ambiguous, do you recommend fetching the current pass, and is there a resource version or sequence marker customers can rely on?
4. Which integration components have become reusable across customers, and which mappings or workflows still need hands-on engineering?
5. Which developer-support task would be most valuable to automate first, and what evidence would make you trust an AI assistant's answer or proposed action?
