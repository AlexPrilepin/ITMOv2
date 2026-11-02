---

description: "Tasks for implementing Review Assistant Web UI (TDD order)"
---

# Tasks: Review Assistant Web UI

**Input**: specs/001-review-ui/spec.md, plan.md, quickstart.md, data-model.md

**Prerequisites**: plan.md (ready), spec.md (ready), research.md, data-model.md, contracts/

**Tests**: Follow TDD — write tests first (server-side), then implement UI page and route; end-to-end checks per quickstart.md.

**Organization**: Tasks are grouped by user story; include exact file paths.

## Phase 0: Contracts & Docs (Reviewer)

- [ ] T000 [P] [ALL] Ensure all UI expectations align with specs/review-api-contract.md (D1–D10). No new contracts.
- [ ] T001 [P] [ALL] Update/confirm quickstart.md covers P1–P3 scenarios and security checks.

---

## Phase 1: User Story 1 — Получить ревью для валидного diff (P1) — MVP

### Tests FIRST (must FAIL initially)

- [ ] T100 [US1] Create server-side test file tests/test_ui_page.py that asserts:
  - GET / returns 200 and text/html; charset=utf-8
  - Response contains elements: textarea#diff, span#counter (text "0/20000"), button#submit (text "Получить ревью"), button#clear (text "Очистить"), div#result, div#error

### Implementation (make tests PASS)

- [ ] T101 [US1] Add static page app/static/index.html (HTML + inline CSS + vanilla JS) with elements:
  - textarea id="diff"; span id="counter"
  - button id="submit" (label: "Получить ревью")
  - button id="clear" (label: "Очистить")
  - div id="result"; div id="error"
  - Insert all API-derived texts via textContent only (no innerHTML)
- [ ] T102 [US1] Add GET / route in app/api.py to serve app/static/index.html using FileResponse/HTMLResponse; same-origin, no new deps
- [ ] T103 [US1] Inline JS: live counter (N/20000), disable submit when empty or >20000; prevent double submit (disable during in-flight)
- [ ] T104 [US1] Inline JS: on submit, fetch POST /api/reviews with JSON body { diff }, headers Accept/Content-Type: application/json; render success:
  - summary (string)
  - risks (up to 3): show title; for evidence.type=diff_line show file:line and proof; for evidence.type=rule show rule label
  - checks: render string list
  - if secrets_masked > 0 show "Секреты в diff были замаскированы"

---

## Phase 2: User Story 2 — Понятные сообщения об ошибках (P2)

### Behavior & Rendering

- [ ] T200 [US2] Error mapping by HTTP status; choose message by status (ignore body text), per contract:
  - 400 → "Пустой diff. Вставьте содержимое diff и повторите попытку."
  - 413 → "Слишком большой diff. Лимит — 20 000 символов." (limit=20000 from body)
  - 422 → "Неверный запрос. Проверьте формат diff."
  - 502 → "LLM недоступен. Попробуйте позже или продолжайте ревью вручную."
  - 504 → "LLM не ответил вовремя. Попробуйте ещё раз или продолжайте ревью вручную."
  - network/other 5xx → "Сетевая ошибка…" / "Внутренняя ошибка сервиса…"
- [ ] T201 [US2] Clear previous error/result before new request; on completion, re-enable submit
- [ ] T202 [US2] Security: ensure no innerHTML for API data; only textContent
- [ ] T203 [US2] Security: ensure no localStorage/sessionStorage usage and no console logging of diff/response

---

## Phase 3: User Story 3 — Очистка и отсутствие хранения (P3)

- [ ] T300 [US3] Implement "Очистить": reset textarea, counter to "0/20000", clear result and error blocks, return to idle state

---

## Phase 4: End-to-End (Quickstart) — Manual/Exploratory

- [ ] T400 [US1] Quickstart P1: Valid request — verify summary, risks (title + diff_line/rule), checks (strings), secrets note when secrets_masked > 0
- [ ] T401 [US2] Quickstart P2: Errors 400/413/422/502/504 and network — verify correct messages
- [ ] T402 [US2] Quickstart P2: Limit — >20000 disables submit; 20000 enables
- [ ] T403 [US3] Quickstart P3: Clear — resets input/results; counter shows 0/20000
- [ ] T404 [SEC] Quickstart Security: no storage; no logs; textContent only
