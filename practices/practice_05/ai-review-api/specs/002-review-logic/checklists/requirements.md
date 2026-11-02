# Requirements Checklist — Structured Review & Secret Masking (002-review-logic)

This checklist is used to track readiness and coverage of the requirements for the feature.

## Functional Requirements

- [ ] FR-001 (SEC-1): Secrets in diff are masked with [SECRET] before any LLM call.
- [ ] FR-002 (SEC-1): Only redacted diff is sent to LLM; original diff is not sent externally.
- [ ] FR-003 (OUT-1): 200 response returns {summary, risks<=3, checks}; legacy {comment} is replaced.
- [ ] FR-004 (OUT-1): Each risk has evidence of type diff_line(file,line,proof) or rule(rule).
- [ ] FR-005 (QA-1): Only risks with valid evidence are included; others are excluded.
- [ ] FR-006 (OUT-1): Unparseable LLM output still yields 200 with fallback summary and empty risks/checks.
- [ ] FR-007: Risks capped at 3; selection policy applied consistently.
- [ ] FR-008: Errors 422/400/413/502/504 unchanged.

## User Scenarios

- [ ] P1: Secrets masked before LLM (SEC-1) — Given/When/Then accepted tests present.
- [ ] P2: Structured response summary/risks/checks (OUT-1) — acceptance tests present.
- [ ] P3: Unconfirmed risks dropped (QA-1) — acceptance tests present.

## Edge Cases

- [ ] Unparseable LLM output handled with fallback summary.
- [ ] >3 risks trimmed to 3.
- [ ] Invalid evidence references excluded.

## Success Criteria

- [ ] SC-001 secret masking verified via prompt capture.
- [ ] SC-002 structured response present in 100% of successes.
- [ ] SC-003 risk capping behavior verified.
- [ ] SC-004 evidence validation behavior verified.
- [ ] SC-005 fallback behavior verified.

## Assumptions & Clarifications

- [ ] FR-009: Line numbering scheme decided. [NEEDS CLARIFICATION]
- [ ] FR-010: Risk selection policy decided. [NEEDS CLARIFICATION]
- [ ] FR-011: Default fallback summary decided. [NEEDS CLARIFICATION]
