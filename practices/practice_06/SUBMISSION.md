# Практика 6: что где лежит

| Критерий | Баллы | Где |
|---|---:|---|
| Модель угроз | 2 | `THREAT_MODEL.md` (описание системы, границы доверия, STRIDE + угрозы LLM T1–T17, меры, проверки), схема `THREAT_MODEL.png` |
| Кастомный промпт LLM-судьи | 1 | `judge-system-prompt.md`; прогоны судьи — `judge-output-round1.txt` (9/10, замечания учтены) и `judge-output.txt` (финальный) |
| REPORT_01 — все найденные проблемы | 2 | `REPORT_01.md`, доказательства `lab/evidence/before/` |
| Исправления, `make step6` и `make test` | 2 | `lab/service.py`, регрессии `lab/test_security.py` (21 тест: до — 26 падений, после — OK); `make step6` → 37 tests OK |
| REPORT_02 — проверка после фикса | 2 | `REPORT_02.md`, доказательства `lab/evidence/after/` |
| PR и выводы | 1 | `PR.md` |

Скрипты: `lab/attacks/check_hypotheses.py` (T1–T13, T15, T16; `before`/`after`), `lab/attacks/run_planner.py` (prompt injection на реальной модели через `shop-planner`), `lab/attacks/build_reports.py` (сборка REPORT_01/02 из evidence).

Кто что делал: модель угроз, проверки гипотез, исправления, тесты и отчёты — агент Claude по решению студента (вместо OpenCode: агент не может набирать текст в терминале OpenCode); прогоны модели под тестом (локальная Qwen 3.5, `ollama/itmo-agent`) и судьи — студент, командами из `PR.md`.
