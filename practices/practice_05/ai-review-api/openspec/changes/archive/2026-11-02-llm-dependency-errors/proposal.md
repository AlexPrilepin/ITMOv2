# Proposal

## Why

Current API calls a synchronous LLM dependency without reliability guards. A slow or failing LLM can hang requests or leak 500s. We need controlled handling per REL-1: time-bound LLM calls and map failures to stable HTTP responses.

## What Changes

- Add timeout to ReviewService to bound LLM call duration.
- Map LLM timeout to HTTP 504 {"error": "llm_timeout"}.
- Map other LLM errors to HTTP 502 {"error": "llm_unavailable"}.
- Keep feature A behavior unchanged and preserve current success payload {"comment": ...}.

## Capabilities

### New Capabilities
- llm-dependency-errors: Controlled handling of LLM dependency errors (timeout and failures) with defined HTTP mappings per REL-1.

### Modified Capabilities


## Impact

- Affects ReviewService and app/api.py error mapping.
- app/dependencies.py provides default timeout=10.0; tests can pass smaller.
- No new logs and no ENV/config files.
