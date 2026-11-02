# Приёмка `llm-dependency-errors` (шаг 5 OpenSpec)

Проверяющий: отдельный агент (Claude), не автор кода. Отчёт автора (OpenCode) не считается проверкой.
Команда проверки проекта: `sh scripts/check.sh` → `Ran 23 tests ... OK` (19 прежних + 4 новых в `tests/test_feature_b.py`).
Дополнительно — независимые пробы через `TestClient` с подменой `review_service.llm` и `timeout`.

| Сценарий (spec) | Ожидание | Факт | Доказательство |
|---|---|---|---|
| LLM превышает timeout | 504 `{"error":"llm_timeout"}` | 504 `{"error":"llm_timeout"}` | проба `slow 2s, timeout 0.1`; тест `test_llm_timeout_returns_504_quickly` |
| Исполнитель не ждёт зависший вызов | ответ < 1 с при LLM 2 с и timeout 0.1 с | 0.13 с | та же проба; `shutdown(wait=False, cancel_futures=True)` в `app/review_service.py` |
| Любой `TimeoutError` из вызова → 504 (решение R6) | 504 | 504 | проба `generate raises TimeoutError` (теста в наборе нет — см. ниже) |
| Прочая ошибка LLM | 502 `{"error":"llm_unavailable"}` | 502 для `RuntimeError` и `KeyError` | пробы; тест `test_llm_other_exception_returns_502` |
| Нет 500 и стека | тело — только JSON ошибки | текст исключения `secret-trace` в ответ не попал | проба `RuntimeError("secret-trace")` |
| Успех в пределах timeout | 200 `{"comment": ...}` | 200 `{"comment":"fine"}` | проба; тест `test_success_within_timeout_returns_200_comment` |
| Невалидный вход не вызывает LLM (старое поведение) | 400 / 422 / 413 при сломанном LLM | 400 `diff is empty`, 422 `diff is required`, 413 `limit 20000` | пробы; тест `test_invalid_input_bypasses_llm_even_if_broken`; `tests/test_feature_a.py` зелёный |
| Значение по умолчанию | `timeout=10.0` | 10.0 | `app/dependencies.py` |
| Границы | не тронуты `docs/requirements.md`, `scripts/check.sh`, `.opencode/plugins/`, логи | не тронуты | `git diff --stat`: изменены только `app/*.py`, `tests/test_feature_b.py`, `tasks.md` |

## Замечания, не блокирующие приёмку

- Для решения R6 нет отдельного unit-теста; поведение подтверждено пробой.
- При timeout поток с зависшим `generate` продолжает работать в фоне до завершения LLM (Python не умеет прерывать поток). Принято как компромисс REL-1: ограничено время ответа клиенту, а не жизнь потока.

## Решение человека

Принято. Можно выполнять sync и archive.
