# Spec Delta: Request Observability (OBS-1)

## ADDED Requirements

### Requirement: Minimal logging for POST /api/reviews
The system SHALL write a single structured log record per POST /api/reviews request that contains only:
- request_id: a unique identifier per request
- duration_ms: end-to-end processing time in milliseconds
- status: HTTP status code of the response

#### Scenario: Successful request is logged
- WHEN POST /api/reviews returns 200
- THEN a log record is written with request_id, duration_ms, and status=200, and it does not include the diff or the model response

#### Scenario: Validation errors are logged without payloads
- WHEN POST /api/reviews returns 400, 413, or 422 due to input validation
- THEN a log record is written with request_id, duration_ms, and status (400/413/422), and it does not include the diff

#### Scenario: LLM dependency errors are logged without payloads
- WHEN POST /api/reviews returns 502 or 504 per llm-dependency-errors
- THEN a log record is written with request_id, duration_ms, and status (502/504), and it does not include the model response

### Requirement: No logging of diff or model response
The system SHALL NOT log the diff input or the model/LLM response content in any log related to POST /api/reviews.

#### Scenario: Sensitive fields are absent in logs
- WHEN a request contains a large diff and the model returns text
- THEN logs do not contain the diff text or the model response body

### Requirement: request_id presence
The system SHALL include request_id in the log record and ensure it is present for all outcomes.

#### Scenario: Every outcome has request_id
- WHEN any of the outcomes 200/400/413/422/502/504 happens
- THEN the written log line includes a non-empty request_id
