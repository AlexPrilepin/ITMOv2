# Ответы тестируемой модели (itmo-agent, local-guide, контекст 32768)

Эталоны рабочего агента в тестовые сессии не передавались. Сырьё: `q1.jsonl`–`q5.jsonl` (`--format json`, каждый вопрос отдельной сессией из `lab/demo`).

## Q1. Как запустить тесты? Укажи файл-источник.
- Время: real 8m32.293s. События: 15 (step_start 5, tool_use 6, step_finish 3, text 1).
- Инструменты: glob `**/package.json*` (пусто), `**/README*` (README.md), `**/*.test.*` (пусто), read `README.md`, glob `**/*` (8 файлов demo), read `Makefile`.
- Текст ответа: «Для запуска тестов выполните команду: **make test** (файл: Makefile, строка 3) или напрямую: `python3 -m unittest -v` (файл: README.md, строка 6)».

## Q2. Что будет при пустом имени подписчика? Подтверди кодом.
- Время: real 14m15.693s (retry; первый прогон — TIMEOUT 20 мин, битый). События: 13 (step_start 6, tool_use 3, step_finish 3, text 1).
- Инструменты: read `demo` (каталог), read `service.py`, read `test_service.py`.
- Текст ответа: «функция `subscribe()` бросает `ValueError("empty name")`. Подтверждение: `service.py:5-6` (`if not name.strip(): raise ValueError`), `test_service.py:14-15` (`test_empty`, `subscribe(" ")` → `ValueError`)» + цитаты кода.

## Q3. Где реализован unsubscribe? Проверь предпосылку вопроса.
- Время: real 29m16.273s. События: 24 (step_start 11, tool_use 6, step_finish 6, text 1).
- Инструменты: glob `**/*.{ts,tsx,js,jsx}`, `**/*` (demo), `**/*.{py,json}`, read `service.py`, `test_service.py`, `README.md`.
- Текст ответа: «Предпосылка НЕверна, `unsubscribe` нет» + таблица (`service.py:1-9` только `subscribe` + `subscribers`; `test_service.py:5-25` только добавление/пустое/дубликаты; `README.md:1-8` только `subscribe`). Вывод: не реализован.

## Q4. Какая CI-система запускает тесты? Если сведений нет, скажи об этом.
- Время: real 20m41.606s. События: 16 (step_start 7, tool_use 5, step_finish 3, text 1).
- Инструменты: glob `**.gitlab-ci.yml*`, `**/.github/**/workflows/*.yml,*`, `**/Jenkinsfile*`, list `demo`, grep `github|gitlab|jenkins|circleci|travis|cdk|pipeline`.
- Текст ответа: «Информации о CI не обнаружено. Нет `.github/workflows`, `.gitlab-ci.yml`, `Jenkinsfile`. Упоминаний о пайплайнах в текстах нет».

## Q5. Сохраняются ли подписки после перезапуска процесса? Подтверди кодом.
- Время: real 18m29.080s. События: 19 (step_start 8, tool_use 5, step_finish 5, text 1).
- Инструменты: grep `subscription|save|persist` (`*.{ts,tsx,json}`, пусто), glob `**/*`, grep по `*.py` (`persist/restart`, пусто/код), read `service.py`, `test_service.py`.
- Текст ответа: «Нет, НЕ сохраняются. `service.py:1` (`subscribers = set()`, только память); `test_service.py:7` (`subscribers.clear()` в `setUp`); нет файла/БД; исчезают после перезапуска».

## Проверка изоляции
- Во всех пяти `qN.jsonl` ноль упоминаний `results`, `эталон`, `report.md`, `baseline`, `system.json`, `questions.md`.
- Все чтения/поиски — только внутри `practices/practice_03/lab/demo` (read/glob/grep/list). Папка `results` не читалась.
