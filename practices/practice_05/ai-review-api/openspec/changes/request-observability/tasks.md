# Tasks

## 1. Tests-first (OBS-1)

- [ ] 1.1 Add tests to assert a minimal log entry is produced for POST /api/reviews outcomes 200/400/413/422/502/504.
- [ ] 1.2 Tests verify the log record contains only fields: request_id (non-empty), duration_ms (>=0), status (matches response).
- [ ] 1.3 Tests verify diff content and model response are absent from logs.

## 2. Implementation

- [ ] 2.1 Add FastAPI middleware dedicated to POST /api/reviews that measures duration and assigns a request_id.
- [ ] 2.2 Emit a structured log line with only request_id, duration_ms, and status after response is generated.
- [ ] 2.3 Ensure exception handlers (422/400/413 and 502/504) still result in a single log record.

## 3. Validation and Baseline

- [ ] 3.1 Run sh scripts/check.sh and ensure all tests (existing and new) pass.
- [ ] 3.2 Review logs during tests to ensure no diff or model response text is present.
