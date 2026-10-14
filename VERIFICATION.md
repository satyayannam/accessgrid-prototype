# Verification

Verified locally on Windows with Python 3.11.3 and Streamlit 1.50.0.

- Created a fresh isolated `.venv` and installed `requirements.txt` successfully.
- Ran `python -m unittest discover -s tests -v`: **15 tests passed**.
- Lifecycle checks: issue contract, both platform options, validation, activate/suspend/resume, unlink and terminal deletion.
- Delivery checks: duplicate suppression, failed delivery without a commit, successful retry, stale/equal timestamps, distinct delayed fixture and state mismatch recovery.
- Streamlit AppTest: issuance, multiple passes, every lifecycle button, delivery/retry/failure/duplicate/delay controls, every assistant scenario and reset. No application exceptions.
- Started the actual Streamlit server on port 8501; `/_stcore/health` returned `ok`.

The first AppTest run exceeded its default three-second timeout during cold startup. The test harness now allows 15 seconds; the passing full suite completed in about three seconds after startup. A deprecated layout argument was replaced during verification.

A subsequent run exposed repeated Windows clock timestamps for very fast sequential actions. The mock generator now gives its events strictly increasing logical timestamps. A fixed-clock regression test covers this; the separate processor test still treats equal incoming timestamps as ambiguous. Dependency validation with `pip check` also passed.

## Verification limits

The Browser plugin reported no available browsers and an empty connection list. Consequently no screenshot or visual layout review was possible. AppTest checks application behavior, not browser rendering. The trace-download control is rendered, but an actual browser download was not exercised. There is no claim of live API, actual wallet installation, real webhook delivery, schema certification or production load testing.

The only runtime persistence is Streamlit session state. This is a deliberately bounded mock, not a deployable production receiver or durable queue.
