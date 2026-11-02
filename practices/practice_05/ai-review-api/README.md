# AI-review API: практика 4 (среда агента, skill, MCP, hook)

Маленький FastAPI-сервис помощника ревьюера PR из практик 1–2. Исходное состояние кода —
ровно то, что получилось после `docs/TRAINING_PR.diff`: `POST /api/reviews` и `GET /health`,
без валидации входа и без timeout.

## Среда агента

| Файл | Что это |
|---|---|
| `AGENTS.md` | Правила для агента: где контракт, как проверять, что нельзя трогать |
| `docs/requirements.md` | Контракт: правила `SEC-1`…`OBS-1`, фича A (и фича B по желанию) |
| `scripts/check.sh` | Единственный runner проверок (unittest) |
| `.opencode/plugins/check-after-edit.js` | Hook OpenCode 2: после правки запускает `check.sh`, возвращает PASS/FAIL агенту, пишет `logs/hook-runs.log` |
| `.opencode/skills/test-driven-development/` | Готовый skill TDD (obra/superpowers) |
| `mcp_server/diff_tools.py` | Собственный MCP-сервер, tool `check_diff` (`API-1` + `SEC-1`) |
| `scripts/mcp_demo.py` | Ручной вызов MCP-сервера: корректный вход, секрет, ошибочный вход |
| `opencode.json` | MCP-серверы `context7` и `diff-tools` |

Стартовый каркас (код из `TRAINING_PR.diff`, MCP-сервер, hook) подготовлен с помощью ИИ-ассистента
вне OpenCode; дальше вся работа шла через агента OpenCode.

## Запуск (Git Bash)

```bash
make install     # .venv + fastapi, httpx, mcp
make check       # тесты
make mcp-demo    # вызовы собственного MCP
opencode         # агент в этой папке
```

## Сдача

<!-- Этот раздел заполняется в конце: ссылки на подтверждения, обоснование подключений, skill-review.md, reflection.md -->
