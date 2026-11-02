---

description: "Tasks for 002-review-logic (Structured Review & Secret Masking)"
---

# Tasks: 002-review-logic

Input: specs/002-review-logic/spec.md, plan.md; contract specs/review-api-contract.md

Prerequisites: plan.md (required), spec.md (required)

Organization: Tasks grouped by user story; tests first (TDD). Paths are concrete for this repository.

## Format: [ID] [P?] [Story] Description

- [P]: Can run in parallel (different files, no dependencies)
- [Story]: US1 (masking), US2 (structured response), US3 (QA-1 filtering)

---

## Phase 0: Foundational

- [ ] T000 Ensure single verification command works: sh scripts/check.sh
- [ ] T001 [P] Review mcp_server/diff_tools.py for secret detectors; decide reuse vs new module per plan.md

---

## Phase 1: User Story 1 - Secrets are masked before LLM (P1)

Goal: SEC-1 masking before any LLM call; LLM receives only masked diff; count secrets_masked.

Tests (write first):
- [ ] T010 tests/unit/test_redaction.py: detects and masks secrets; returns (masked_diff, secrets_masked); preserves non-secret content.
- [ ] T011 tests/unit/test_review_service_prompt.py: LLM prompt contains [SECRET] and never raw secrets; secrets_masked included in API response.

Implementation:
- [ ] T012 app/redaction.py: implement redaction (if reuse not possible without MCP dependency); API: redact(diff)->(masked_diff, secrets_masked)
- [ ] T013 app/review_service.py: integrate redaction; ensure only masked_diff is used in prompt; plumb secrets_masked to result.

---

## Phase 2: User Story 2 - Structured response summary/risks/checks (P2)

Goal: Return structured JSON with summary, risks<=3, checks, secrets_masked per contract; remove legacy comment.

Tests (write first):
- [ ] T020 tests/test_api.py: update success path to assert fields summary, risks(list), checks(list), secrets_masked(int>=0); remove assertions about comment.
- [ ] T021 tests/test_feature_b.py (success path): update to new contract (if present); errors 502/504 unchanged.
- [ ] T022 tests/unit/test_stub_llm.py: StubLLM returns deterministic JSON matching contract.

Implementation:
- [ ] T023 app/dependencies.py: StubLLM: deterministic JSON per contract.
- [ ] T024 app/review_service.py: parse LLM JSON; fallback summary per D8; assemble structured response including secrets_masked.

---

## Phase 3: User Story 3 - Unconfirmed risks are dropped (P3)

Goal: QA-1 filtering using masked diff; numbering per D5; cap to three risks preserving model order (D6); proof from masked diff (D7).

Tests (write first):
- [ ] T030 tests/unit/test_risk_validation.py: include valid diff_line risk (kept), invalid file/line (dropped), rule evidence (kept if allowed), >3 risks (capped to 3).
- [ ] T031 tests/unit/test_proof_masking.py: when proof line contains secrets, returned proof uses masked line and never reveals secrets; secrets_masked > 0.

Implementation:
- [ ] T032 app/review_service.py: risk validation against masked diff; implement D5 numbering; filter & cap risks; ensure proof substring is taken from masked diff.

---

## Phase N: Polish & Cross-Cutting

- [ ] T040 [P] docs/specs cross-check: ensure spec aligns with specs/review-api-contract.md (no requestId/model/elapsedMs).
- [ ] T041 [P] Ensure OBS-1 compliance: no logging of diff or model response.
