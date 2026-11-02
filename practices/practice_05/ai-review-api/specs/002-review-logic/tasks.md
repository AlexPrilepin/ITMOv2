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

- [x] T000 Ensure single verification command works: sh scripts/check.sh
- [x] T001 [P] Review mcp_server/diff_tools.py for secret detectors; decide reuse vs new module per plan.md — решение: отдельный app/redaction.py (детекторы MCP имеют те же пробелы R6 и маскируют только значение присваивания)

---

## Phase 1: User Story 1 - Secrets are masked before LLM (P1)

Goal: SEC-1 masking before any LLM call; LLM receives only masked diff; count secrets_masked.

Tests (write first) — place tests under tests/ (unittest discovery expects tests/ root):
- [x] T010 tests/test_logic_redaction.py: detects and masks secrets; returns (masked_diff, secrets_masked); preserves non-secret content.
- [x] T011 tests/test_logic_prompt.py: LLM prompt contains [SECRET] and never raw secrets; secrets_masked included in API response.

Implementation:
- [x] T012 app/redaction.py: implement redaction (if reuse not possible without MCP dependency); API: redact(diff)->(masked_diff, secrets_masked)
- [x] T013 app/review_service.py: integrate redaction; ensure only masked_diff is used in prompt; plumb secrets_masked to result.

---

## Phase 2: User Story 2 - Structured response summary/risks/checks (P2)

Goal: Return structured JSON with summary, risks<=3, checks, secrets_masked per contract; remove legacy comment.

Tests (write first):
- [x] T020 tests/test_api.py: update success path to assert fields summary, risks(list), checks(list), secrets_masked(int>=0); remove assertions about comment.
- [x] T021 tests/test_feature_b.py: update success path; errors 502/504 unchanged.
- [x] T022 tests/test_feature_a.py: update exact-limit success path under new contract.
- [x] T023 tests/test_review_service.py: update to structured response under new contract.
- [x] T024 tests/test_logic_stub_llm.py: StubLLM returns deterministic JSON matching contract.

Implementation:
- [x] T030 app/dependencies.py: StubLLM: deterministic JSON per contract.
- [x] T031 app/review_service.py: parse LLM JSON; fallback summary per D8; assemble structured response including secrets_masked.

---

## Phase 3: User Story 3 - Unconfirmed risks are dropped (P3)

Goal: QA-1 filtering using masked diff; numbering per D5; cap to three risks preserving model order (D6); proof from masked diff (D7).

Tests (write first):
- [x] T040 tests/test_logic_risks.py: include valid diff_line risk (kept), invalid file/line (dropped), rule evidence (kept if allowed), >3 risks (capped to 3).
- [x] T041 tests/test_logic_proof_masking.py: when proof line contains secrets, returned proof uses masked line and never reveals secrets; secrets_masked > 0.

Implementation:
- [x] T050 app/review_service.py: risk validation against masked diff; implement D5 numbering; filter & cap risks; ensure proof substring is taken from masked diff.

---

## Phase N: Polish & Cross-Cutting

- [x] T060 [P] docs/specs cross-check: ensure spec aligns with specs/review-api-contract.md (no requestId/model/elapsedMs).
- [x] T061 [P] Ensure OBS-1 compliance: no logging of diff or model response.

---

## Журнал ревью (независимый проверяющий — Claude, вне сессии OpenCode)

| Круг | Найдено | Кто исправил | Доказательство |
|---|---|---|---|
| 1 | R1 тело PEM уходило в LLM; R2 diff_line-риск без сверки с diff (QA-1/D7); R3 реализация раньше тестов, отметок нет; R4 ослаблен test_review_service; R5 StubLLM не JSON | агент OpenCode (R1–R4) | tests/test_logic_redaction.py, test_logic_risks.py, test_logic_proof_masking.py, test_logic_prompt.py; hook-лог FAIL→PASS |
| 2 | R6 шесть форматов секретов не маскировались (DB_PASSWORD, SECRET_KEY, AWS_SECRET_ACCESS_KEY, JSON "password", Bearer в dict, PEM внутри строки); R7 секрет из ответа модели попадал в title/summary/checks | агент OpenCode | новые тесты в test_logic_redaction.py, test_logic_proof_masking.py |
| 3 | R8 ReDoS: регулярки присваиваний давали кубический перебор — строка 20 000 символов (лимит API-1) обрабатывалась > 600 с до вызова LLM, timeout REL-1 не защищал; R5 и отметки [x] так и не сделаны агентом за два круга | ревьюер (TDD: сначала красный тест) | tests/test_logic_redaction_perf.py (red: > 600 с; green: 0.04 с), tests/test_logic_stub_llm.py, app/redaction.py (ASSIGNMENT), app/dependencies.py (StubLLM) |

Итог: `sh scripts/check.sh` → 35 tests OK за 0.23 с; атакующие пробы — 10/10 форматов секретов замаскированы, 0 утечек в prompt и в ответ API.
