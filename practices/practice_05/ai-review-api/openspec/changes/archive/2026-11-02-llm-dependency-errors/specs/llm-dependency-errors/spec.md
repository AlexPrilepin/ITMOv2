# Spec Delta

## ADDED Requirements

### Requirement: LLM call is time-bound
The system SHALL bound the execution time of the LLM call within ReviewService by a configurable timeout (default 10 seconds via the timeout parameter).

#### Scenario: LLM exceeds timeout
- **WHEN** the LLM call exceeds the configured timeout
- **THEN** the service raises a timeout error that maps to HTTP 504 with body {"error": "llm_timeout"}

#### Scenario: LLM responds within timeout
- **WHEN** the LLM call returns within the configured timeout
- **THEN** the API responds 200 with body containing {"comment": ...}

### Requirement: LLM non-timeout failures are controlled
The system SHALL map non-timeout LLM failures to a controlled unavailable error.

#### Scenario: LLM raises an exception
- **WHEN** the LLM call raises any exception other than timeout
- **THEN** the service raises an unavailable error that maps to HTTP 502 with body {"error": "llm_unavailable"}

### Requirement: No HTTP 500 or stack traces
The system SHALL NOT return HTTP 500 or include stack traces in responses for LLM dependency errors.

#### Scenario: No stack traces
- **WHEN** the LLM call fails (timeout or other error)
- **THEN** the response contains only the specified error JSON and no stack traces

### Requirement: Invalid input bypasses LLM
The system SHALL NOT call the LLM when input validation fails.

#### Scenario: Empty diff returns 400 without LLM call
- **WHEN** the diff is empty or whitespace-only
- **THEN** the API responds 400 with {"error": "diff is empty"} and the LLM is not called, even if the LLM would fail

### Requirement: Executor shutdown without waiting
The system SHALL ensure the executor does not block waiting on a hung LLM call by shutting down without waiting or using a shared service executor.

#### Scenario: Timed-out call returns promptly
- **WHEN** the LLM sleeps for 2 seconds and timeout is 0.1 seconds
- **THEN** the API returns 504 faster than 1 second
