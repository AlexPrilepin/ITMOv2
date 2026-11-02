# Tasks

# Tasks

## 1. Tests-first (REL-1)

- [x] 1.1 Add failing tests: LLM timeout maps to 504 {"error":"llm_timeout"} with small timeout; slow LLM (sleep 2s) with timeout 0.1s returns < 1s
- [x] 1.2 Add failing tests: non-timeout LLM exception maps to 502 {"error":"llm_unavailable"}
- [x] 1.3 Add test: successful LLM response within timeout → 200 {"comment": ...}
- [x] 1.4 Add test: invalid input (empty diff) → 400 and LLM not called even if LLM is broken

## 2. Service-level implementation

- [x] 2.1 Introduce exceptions LLMTimeoutError and LLMUnavailableError in app/review_service.py
- [x] 2.2 Update ReviewService to accept timeout param and wrap llm.generate via ThreadPoolExecutor + future.result(timeout); ensure executor shutdown does not wait (shutdown(wait=False, cancel_futures=True))
- [x] 2.3 Classify any TimeoutError from the wrapped call as llm_timeout (504); map other exceptions to LLMUnavailableError

## 3. API mapping and dependencies

- [x] 3.1 Update app/api.py to catch LLMTimeoutError → 504 {"error":"llm_timeout"}; catch LLMUnavailableError → 502 {"error":"llm_unavailable"}
- [x] 3.2 Set default timeout=10.0 in app/dependencies.py; keep Feature A behavior intact

## 4. Validation and baseline

- [x] 4.1 Run sh scripts/check.sh; verify all existing 19 tests and new tests pass
- [x] 4.2 Ensure no new logs and no stack traces in responses; Feature A scenarios unchanged
