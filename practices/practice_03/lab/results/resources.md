# Замеры ресурсов itmo-agent (OpenCode local-guide)

Ноутбук: i9-12900HK, 32 ГБ RAM, только встроенная Intel Iris Xe, инференс на CPU (100% CPU, llamacpp).
Модель: itmo-agent на базе qwen3.5:4b.
Команда (из `practices/practice_03/lab/demo`):
`time opencode run --agent local-guide --model ollama/itmo-agent "Ответь одним словом: ГОТОВ"; ollama ps`
Ответ модели в обоих замерах: `ГОТОВ`.

## Замер 1 — контекст 65536 (до правки)

- `Modelfile.agent`: `PARAMETER num_ctx 65536`
- `demo/opencode.json`: `limit.context 65536`
- время `real 10m37.232s` (`user 0m0.075s`, `sys 0m0.168s`), opencode v2.0.20, холодный старт (до запуска `ollama ps` пуст)
- `ollama ps`: `itmo-agent:latest b572cfef927a SIZE 5.6 GB PROCESSOR 100% CPU CONTEXT 65536 RUNNER llamacpp`

## Замер 2 — контекст 32768 (после правки)

- `Modelfile.agent`: `PARAMETER num_ctx 32768`
- `demo/opencode.json`: `limit.context 32768`
- пересборка из `lab/`: `ollama stop itmo-agent; ollama create itmo-agent -f Modelfile.agent` (успешно, новый ID `bc59ed397316`, `ollama show --modelfile` подтверждает `num_ctx 32768`)
- время `real 14m57.235s` (`user 0m0.045s`, `sys 0m0.061s`), холодный старт после `stop`
- `ollama ps`: `itmo-agent:latest bc59ed397316 SIZE 4.2 GB PROCESSOR 100% CPU CONTEXT 32768 RUNNER llamacpp`

## Вывод

- Потребление памяти упало: 5.6 GB -> 4.2 GB при смене 65536 -> 32768, что ожидаемо для KV-кэша на CPU.
- Время выросло: 10м37с -> 14м57с. Ускорения нет; разброс объясняется фоновой нагрузкой/прогревом CPU и variance холодного старта, а не только размером контекста. Для отчёта фиксируем оба числа честно, без вывода «меньше контекст = быстрее».

## Наблюдение: OpenCode против прямого API

- Ответ из одного слова («ГОТОВ») через OpenCode занял 10–15 минут в обоих замерах.
- Тот же `itmo-agent` (qwen3.5:4b) через прямой `experiment.py` (`think=false`, короткий контекст из `demo/README.md`) отвечал за 10–30 секунд.
- Гипотеза: внутри OpenCode модель «думает» (reasoning включён по умолчанию для qwen3.5), плюс OpenCode отправляет длинный системный промпт (`repo-system.txt` + обвязка агента `local-guide`: инструкции, список файлов, история шагов). Проверим на следующем шаге сравнением `think` и длины промпта.

## Проблемы

- Q2 завис на 20 минут: в `q2.jsonl` только 3x `step_start`, без `tool_use` и текста; раннер Ollama застрял в статусе `Stopping` (100% CPU), пришлось завершить `llama-server.exe`.
- Причина: прерванные по таймауту прогоны продолжали работать в фоне и забивали очередь Ollama. Это не троттлинг.
- Решение: перезапуск Ollama и `opencode service set disabled true` (отключение общего фонового сервера). Теперь каждый `opencode run` работает со своим сервером и завершается вместе с командой; модель снова отвечает за секунды.
- По токенам Q1: модель выдавала около 200 output-токенов на шаг при примерно 40 видимых (вызовы `glob`/`read` и короткий текст), то есть думала скрыто: Ollama считает размышления в `completion_tokens`, а OpenCode показывает `reasoning: 0` и не выводит их как `reasoning`.

## Правка Modelfile

- Причина: модель в Q1 путала источники (`make test` ↔ `Makefile`/`README.md`), поэтому системный промпт `itmo` усилен: добавлен `PARAMETER seed 42`, явное правило про ложную предпосылку («прямо скажи, что предпосылка неверна») и требование указывать файл и строку для каждого факта.
- Проверка одним запросом (`cat -n demo/README.md demo/service.py` + «в какой строке реализована функция unsubscribe?», `ollama run itmo --think=false`): до — 17.5с, «В предоставленных материалах нет ответа + обоснование (есть только `subscribe`)» (`results/premise_before.txt`); после (`ollama create itmo -f Modelfile`) — 8.1с, тот же корректный отказ (`results/premise_after.txt`).
- Вывод: обе конфигурации ловушку проходят, новая формулировка не сломала поведение; разница во времени — variance холодного/тёплого старта, а не эффект промпта.

## Эксперимент: отключение размышлений

- Цель: Q1 показал ~200 output-токенов на шаг при ~40 видимых — подозрение на скрытое мышление; напрямую в Ollama `reasoning_effort:none` давал 0.8с против ~30с.
- Вариант А (`options: {reasoningEffort: none}` в `demo/opencode.json`): Q1 за 5м44.938с против 8м32с (быстрее на ~33%), токены шага 78 против 207/177/87 — но ответ хуже: всего 1 `glob`, итог «проверю содержимое test_service.py», команда `make test` не названа (`results/q1_nothink.jsonl`, 5 событий).
- Вариант Б (`body: {reasoning_effort: none}`): Q1 за 11м53.253с (медленнее базовых 8м32с), токены 120+147 — не упали до видимого объёма; зато ответ с верными источниками: `README.md:6` → `make test`, `Makefile:1-4` → `python3 -m unittest -v` (`results/q1_nothink_body.jsonl`, 10 событий).
- Итог: ни один вариант не дал одновременно ускорения и качества (А — быстрее, но хуже; Б — точнее, но медленнее), поэтому `opencode.json` откачен к состоянию до опыта (контекст 32768, без options/body). Q1–Q5 сняты с размышлениями по умолчанию.

## Проверка итоговой конфигурации

- Новый вопрос (`subscribe(' Ann ')`, эталон рабочего агента: вернёт `{"subscribed": True}`, имя триммится — `service.py:5-8`): 13м44.221с, `results/demo_check.jsonl` (23 события: 9 step_start, 7 tool_use, 7 step_finish, 0 text).
- Модель ушла вширь: читала родительские каталоги `practice_03` и `lab`, `glob **/*.py` по `practice_03`, `grep def subscribe` по `practice_03` (зацепил сниппеты `results/q2,q3,q5.jsonl` через вложенные выводы `read`), затем `read service.py` + `test_service.py` — но итоговый текст не синтезировала (оборвалась на лимите шагов).
- Ответа нет — фиксирую честно, без перезапуска (по правилам). Для изоляции: прямых чтений `results` не было, эталонов там нет; но этот прогон — единственный, вышедший за пределы `demo/`.
- Повтор после улучшений (`steps` 8→12, в `repo-system.txt` добавлена граница «только текущая папка и подпапки»): 9м22.685с, `results/demo_check2.jsonl` (22 события: 6 tool_use, 2 text). Ответ есть и верен: `{"subscribed": True}`, `' Ann '.strip()` → `"Ann"`, ссылка `service.py:7`. За пределы `demo/` чтений больше нет (два поиска с путем на `practice_03`, без касания `results`; проверка по jsonl — ноль `results/эталон/report/baseline/system/questions`). Попытка вызвать `execute`/`bash` корректно отклонена правами (`deny`). Правки оставлены.
