# Design

## Context

The API currently calls a synchronous LLM dependency via ReviewService without timeout or error-class mapping, risking hung requests and HTTP 500s. Feature A validation must remain intact.

## Goals / Non-Goals

**Goals:**
- Add ReviewService timeout to bound LLM call duration (default 10.0s) and make it test-configurable.
- Use ThreadPoolExecutor with future.result(timeout) to enforce timeout for the synchronous generate call.
- Map service exceptions to HTTP: timeout → 504 {"error":"llm_timeout"}; other exceptions → 502 {"error":"llm_unavailable"}.
- Preserve existing behavior for valid requests and health endpoint.

**Non-Goals:**
- OUT-1 response structure changes (summary/risks/checks).
- SEC-1 enhancements or redaction behavior.
- Async refactor, retries, ENV/config files, logging changes.

## Decisions

1. Boundary for timeout: only around llm.generate in ReviewService to keep validation logic unchanged and minimize API surface impact.
2. Concurrency mechanism: ThreadPoolExecutor to wrap synchronous generate with future.result(timeout) for cross-platform behavior.
3. Exception taxonomy: introduce LLMTimeoutError and LLMUnavailableError in service layer; api.py translates them to 504/502.
4. Dependency injection: ReviewService(llm, timeout=10.0) with default set in app/dependencies.py; tests pass smaller timeouts.
5. Timeout classification: any TimeoutError observed in the wrapped call is classified as llm_timeout and mapped to 504.

## Risks / Trade-offs

- ThreadPoolExecutor introduces thread overhead per call: acceptable given short critical section and low cost during tests.
- Blanket mapping of non-timeout errors to 502 may hide diagnostics; acceptable per REL-1 to avoid leaking internals and stack traces.
- Ensuring that Feature A tests still bypass LLM when invalid input: enforced by keeping validation before service call.
