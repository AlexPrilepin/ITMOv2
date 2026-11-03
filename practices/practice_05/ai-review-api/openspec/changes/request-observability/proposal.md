# Proposal: Request Observability (OBS-1)

## Why

We must comply with OBS-1 from docs/requirements.md: logs for POST /api/reviews should include only request_id, duration, and response status. The diff content and the LLM/model response must not be logged. This reduces data exposure risk and aligns with privacy and minimal logging principles. Additionally, per the accepted llm-dependency-errors spec, statuses 200/400/413/422/502/504 must be covered by logging.

## What Changes

- Introduce minimal request-scoped logging for POST /api/reviews that records:
  - request_id (correlation id)
  - duration (end-to-end processing time)
  - HTTP status code of the response
- Ensure logs explicitly do not include the diff payload or the LLM/model output.
- Cover all relevant outcome codes from API-1 and llm-dependency-errors: 200, 400, 413, 422, 502, 504.
- Keep existing API behavior and responses unchanged.

## Capabilities

### New Capabilities
- Request observability (OBS-1): minimal structured log for POST /api/reviews without sensitive payloads.

### Modified Capabilities
- None beyond adding logging side-effects; no API surface changes.

## Impact

- Affects request handling around POST /api/reviews (likely via FastAPI middleware or function-scoped timing).
- Requires a request_id generator or propagation; may reuse existing context if present or generate per-request UUID.
- No changes to responses or tests outside the new logging expectations.
