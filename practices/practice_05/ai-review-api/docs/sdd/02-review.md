# Ревью предложения `llm-dependency-errors` (шаг 3 OpenSpec)

Ревьюер: отдельный агент (Claude, вне сессии OpenCode, которая писала предложение). Файлы change не менялись.
Прочитано: `openspec/changes/llm-dependency-errors/*`, `app/api.py`, `app/review_service.py`, `app/dependencies.py`, `tests/test_feature_a.py`, `AGENTS.md`.

## Замечания

| # | Где | Проблема | Почему важно | Предложение |
|---|---|---|---|---|
| R1 | design.md, решение 2; tasks 1.2 | Не указано, как завершать `ThreadPoolExecutor`. Типичная запись `with ThreadPoolExecutor() as ex: ex.submit(...).result(timeout)` при timeout вызывает `shutdown(wait=True)` в `__exit__` и ждёт зависший `generate`. | Запрос висит столько же, сколько LLM: REL-1 формально «реализован», но 504 приходит только после завершения LLM. | Явно: executor завершается через `shutdown(wait=False, cancel_futures=True)` (или общий executor на сервис). Добавить сценарий и тест: LLM спит 2 с, timeout 0.1 с, ответ 504 приходит быстрее 1 с. |
| R2 | specs/reliability/llm-dependency-errors/spec.md | Вложенное имя capability `reliability/llm-dependency-errors`. | В OpenSpec capability — один каталог `specs/<capability>/spec.md`; вложенность ломает sync/archive в main specs. | Перенести в `specs/llm-dependency-errors/spec.md`, капабилити `llm-dependency-errors`; поправить proposal.md. |
| R3 | spec.md | Нет сценария успешного пути: LLM ответил в пределах timeout → HTTP 200 `{"comment": ...}`. Нет упоминания значения по умолчанию 10 с. | Условие приёмки «успешный ответ не меняется» не проверяемо по спеке; дефолт из REL-1 не зафиксирован. | Добавить Requirement/Scenario на успех и указать «по умолчанию 10 секунд, задаётся параметром `timeout`». |
| R4 | spec.md | Нет сценария, что невалидный вход (фича A) не вызывает LLM и не превращается в 502/504. | Фича B не должна менять порядок «сначала валидация, потом LLM». | Scenario: пустой diff → 400, LLM не вызывается, даже если LLM «сломан». |
| R5 | tasks.md | Тесты (2.3) идут после реализации. | `AGENTS.md` требует skill TDD: сначала падающий тест. | Переставить: сначала тесты REL-1 (падают), затем реализация. Задача 1.1 «verify tests import and instantiate» — непроверяемая формулировка, убрать. |
| R6 | design.md | Если `generate` сам бросает `TimeoutError` (например, сетевой timeout клиента), `future.result()` пробросит его как `TimeoutError`. | Неочевидно, это 504 или 502. | Зафиксировать решение: любой `TimeoutError` → `llm_timeout` (504). |

Мелочь: заголовок `# Spec Delta` и раздел `## Purpose` в delta-spec не нужны, достаточно `## ADDED Requirements`.

## Вердикт

Цель, границы и non-goals верны и совпадают с решениями из `01-explore.md`. R1 — существенная ошибка дизайна, R2 — формат OpenSpec; R3–R6 — полнота. После исправления через `/opsx-update` и `openspec validate --strict` можно разрешать apply.
