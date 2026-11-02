# Практика 5. Spec-Driven Development: OpenSpec в brownfield + ДЗ «две команды — одна фича» (Spec Kit)

Проект: `ai-review-api/` — сервис помощника ревьюера PR из практик 1–4 (FastAPI). Стартовая копия — из ЛР-4 (`practices/practice_04/ai-review-api`), сданная ЛР-4 не менялась.

## Быстрая проверка (Git Bash, Windows)

```bash
cd practices/practice_05/ai-review-api
make install PY=/c/Users/Alex/AppData/Local/Programs/Python/Python313/python.exe   # Windows-Python, не MSYS
make check                                                                          # 42 теста
.venv/Scripts/python.exe -m uvicorn app.api:app --port 8000                         # демо: http://127.0.0.1:8000/
```

Сквозные проверки в браузере (нужен Playwright): `python e2e/test_ui_e2e.py` → `docs/sdd/speckit/e2e/e2e-report.json` (22/22) и скриншоты.

## Часть занятия: OpenSpec (слайды 4–15)

| Шаг | Артефакт |
|---|---|
| Установка, `openspec init --profile core` | `ai-review-api/openspec/`, `.opencode/commands/opsx-*` |
| Explore фичи B (REL-1) | `docs/sdd/01-explore.md` |
| Propose → ревью → update → `validate --strict` | `docs/sdd/02-review.md`, архив `openspec/changes/archive/2026-11-02-llm-dependency-errors/` |
| Apply (TDD) и независимая приёмка | `app/review_service.py`, `tests/test_feature_b.py`, `docs/sdd/03-acceptance.md` |
| Sync + archive | `openspec/specs/llm-dependency-errors/spec.md` |
| Правило `rules.design` (Mermaid), фрагмент до/после | `openspec/config.yaml`, `docs/sdd/04-design-before.md`, `docs/sdd/05-rule-check.md`, `docs/sdd/05-mermaid-rendered.png`, change `openspec/changes/request-observability/` |

## ДЗ 5: две команды — одна фича (10 баллов)

| Критерий | Баллы | Где |
|---|---:|---|
| Другой SDD-фреймворк: применение и сравнение с OpenSpec | 2 | Spec Kit 1.2.1: `.specify/` (конституция `.specify/memory/constitution.md`), `specs/001-review-ui/`, `specs/002-review-logic/` (spec → clarify → plan → tasks → implement); сравнение — `docs/sdd/06-comparison-openspec-speckit.md` |
| Две спецификации (UI и логика), согласованные до кода | 2 | Спеки «до»: `docs/sdd/speckit/before/`; общий контракт с 10 решениями: `specs/review-api-contract.md`; спеки «после»: `docs/sdd/speckit/after/`, diff `docs/sdd/speckit/*.before-after.diff`, раздел Clarifications в каждой спеке |
| Реализация: работающие UI и логика, сквозные проверки | 5 | UI: `app/static/index.html`, `GET /`; логика: `app/redaction.py` (SEC-1), `app/review_service.py` (OUT-1, QA-1, D7), `app/dependencies.py` (StubLLM); `make check` — 42 теста; браузер: `e2e/test_ui_e2e.py`, `docs/sdd/speckit/e2e/` (22/22, скриншоты для демо) |
| Рефлексия | 1 | `docs/sdd/07-reflection.md` |

Демо: `docs/sdd/speckit/e2e/02-success-secret.png` (секрет замаскирован), `03-success-diff-line.png` (риски file:line, отброшен выдуманный, XSS выведен текстом), `04-error-502.png`, `05-limit.png`.

## Кто что делал

- Решения (контракт D1–D10, ответы на вопросы explore, приёмка) — человек; варианты предлагал ассистент Claude.
- Генерация артефактов OpenSpec и Spec Kit, реализация фичи B и логики SEC-1/OUT-1/QA-1 — агент OpenCode (gpt-5).
- Независимое ревью и приёмка (`02-review.md`, `03-acceptance.md`, журналы в `specs/*/tasks.md`) — Claude, вне сессии автора кода.
- Исправления по ревью, которые агент не довёл за два круга (ReDoS в маскировании, детерминированный StubLLM), и реализация UI по `/speckit.implement` — Claude, по TDD; помечено в `specs/002-review-logic/tasks.md` и `specs/001-review-ui/tasks.md`.
