# Unit-проверки

| Требование или правило | Что проверяем изолированно | Вход | Ожидаемый результат | Подтверждение |
|---|---|---|---|---|
| `SEC-1` — секреты удаляются до отправки в LLM | `sanitize(diff)` вырезает токены, пароли, приватные ключи | diff со строкой `token = "sk-abc..."` | В prompt вместо значения `[REDACTED]` | pytest: `test_strip_secrets_before_llm` |
| `SEC-1` — отрицательный кейс | Санитизация не удаляет обычный код | diff со строкой `x = 1` | Строка остаётся без изменений | pytest: `test_strip_secrets_keeps_plain_code` |
| `API-1` — лимит размера diff | `create_review` отклоняет diff длиннее 20 000 символов | POST с diff 20 001 символ | HTTP 413 | pytest: `test_create_review_too_large_diff` |
| `API-1` — граница | diff ровно 20 000 символов принимается | POST с diff 20 000 символов | HTTP 200, не 413 | pytest: `test_create_review_boundary_size` |
| `REL-1` — timeout на LLM | `ReviewService.review` ограничивает вызов 10 секундами | мок LLM с задержкой 15 с | `TimeoutError` перехвачен, возвращён контролируемый ответ | pytest: `test_llm_timeout` |
| `REL-1` — ошибка LLM не пробрасывается | `ReviewService.review` ловит исключение провайдера | мок LLM, бросающий `RuntimeError` | Контролируемый ответ, не «сырое» исключение | pytest: `test_llm_error_handled` |
| `OUT-1` — структура ответа | Ответ содержит `summary`, `risks`, `checks` | валидный diff | Все три ключа присутствуют и непусты | pytest: `test_review_response_shape` |
| `OUT-1` — ≤ 3 риска | `risks` содержит не больше трёх элементов | diff с 5 потенциальными рисками | len(risks) ≤ 3 | pytest: `test_max_three_risks` |
| `OUT-1` — формат риска | Каждый риск содержит `file`, `line`, `evidence`, `risk` | валидный diff с одним риском | Все четыре поля присутствуют и непусты | pytest: `test_risk_format` |
| `SCOPE-1` — сервис не действует в GitHub | `ReviewService` не вызывает GitHub API | валидный diff | Мок GitHub API не получил ни одного вызова | pytest: `test_no_github_actions` |
| `QA-1` — риск только с evidence | Риск без `file:line` отбрасывается | diff с «подозрительной» строкой без якоря | В `risks` такого элемента нет | pytest: `test_risk_without_evidence_dropped` |
| `OBS-1` — логи без содержимого | Логгер пишет только `request_id`, длительность, статус | один вызов `review` | В логе нет строк diff и ответа модели | pytest: `test_log_no_diff_content` |

## Как использовали AI

- Строка в `prompts.md`: P1-02.
- Что проверил студент: проверки `SEC-1`, `API-1`, `REL-1`, `OUT-1`, `SCOPE-1`, `QA-1`, `OBS-1` соответствуют правилам из `CASE.md`; проверки на границы (`20 000` / `20 001`, `10 с` таймаут) добавлены после сверки с формулировками правил.