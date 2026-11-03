# Research Notes: Review Assistant Web UI (Phase 0)

- Контракт: specs/review-api-contract.md (решения D1–D10) — формат ответа 200, рисков, checks, secrets_masked; ошибки и их тела.
- Архитектура UI: одна статическая страница app/static/index.html, inline CSS/vanilla JS, fetch.
- Безопасность: только textContent для данных, без innerHTML; не хранить diff; не логировать.
- Совместимость: UI добавляет только GET / в app/api.py; POST /api/reviews неизменен.
