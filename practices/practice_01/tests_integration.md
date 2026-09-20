# Integration-проверки

| Связь компонентов | Что может сломаться | Как воспроизводим | Ожидаемый результат | Подтверждение |
|---|---|---|---|---|
| API ↔ ReviewService | `payload["diff"]` падает с `KeyError`, если поля нет | POST `/api/reviews` с телом `{}` | HTTP 422, не 500 | curl + pytest: `test_api_review_missing_diff` |
| API ↔ ReviewService | Пустой diff не отсекается валидацией | POST `/api/reviews` с `{"diff": ""}` | HTTP 400 | curl + pytest: `test_api_review_empty_diff` |
| API ↔ ReviewService | diff больше 20 000 символов доходит до LLM | POST `/api/reviews` с diff 20 001 символ | HTTP 413 (`API-1`), LLM не вызван | pytest: `test_api_review_too_large` |
| ReviewService ↔ LLM | Провайдер недоступен или отвечает медленнее 10 с | мок LLM с задержкой 15 с | Timeout перехвачен (`REL-1`), контролируемый ответ, не 500 | pytest: `test_review_llm_timeout` |
| ReviewService ↔ LLM | Провайдер вернул ошибку | мок LLM, бросающий `RuntimeError` | Контролируемый ответ (`REL-1`), не «сырое» исключение | pytest: `test_review_llm_error` |
| ReviewService ↔ LLM | Провайдер вернул невалидный JSON вместо структуры | мок LLM с текстом `"не json"` | HTTP 502, ревьюер видит понятное сообщение | pytest: `test_review_bad_llm_output` |
| ReviewService ↔ Sanitizer | diff уходит в LLM без санитизации | мок LLM перехватывает prompt | В prompt нет токенов/паролей, только `[REDACTED]` (`SEC-1`) | pytest: `test_prompt_sanitized` |
| ReviewService ↔ Storage | Отчёт не сохраняется или сохраняется не туда | POST, затем проверка файла `results/<pr_id>.json` | Файл создан, содержимое совпадает с ответом | pytest: `test_report_saved` |
| ReviewService ↔ Storage | Директория `results/` отсутствует | удалить `results/`, POST | Директория создаётся автоматически или 500 с понятным сообщением | pytest: `test_results_dir_autocreate` |
| Logging ↔ ReviewService | В лог попадает содержимое diff или ответа модели | один вызов `review` с секретом в diff | В логе нет ни diff, ни ответа LLM (`OBS-1`) | pytest: `test_logs_no_sensitive_data` |
| Полный путь | PR с diff среднего размера (≈ 500 строк) | POST `/api/reviews` с реальным diff | 200, ответ содержит `summary`, `risks` (≤ 3), `checks` (`OUT-1`) | pytest: `test_review_happy_path` |

## Как использовали AI

- Строка в `prompts.md`: P1-02.
- Что проверил студент: проверки `API-1` (413 на 20 001 символе), `REL-1` (timeout 10 с), `SEC-1` (санитизация prompt), `OBS-1` (логи без содержимого) сверены с `CASE.md`; `KeyError` и пустой diff — из рисков P1-02 и `TRAINING_PR.diff`.