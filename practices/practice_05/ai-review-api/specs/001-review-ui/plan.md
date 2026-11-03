# Implementation Plan: Review Assistant Web UI

**Branch**: `[001-review-ui]` | **Date**: 2026-11-02 | **Spec**: specs/001-review-ui/spec.md

**Input**: Feature specification from `specs/001-review-ui/spec.md`

**Note**: This plan follows the brownfield constraints and the shared contract specs/review-api-contract.md.

## Summary

Одностраничный UI помощника ревьюера, отдаваемый тем же FastAPI по GET /. Пользователь вставляет unified diff (до 20 000 символов) и отправляет POST /api/reviews. UI отображает summary, до 3 рисков (title + evidence), список checks (строки), и отметку, если secrets_masked > 0. Ошибки отображаются по статусам 400/413/422/502/504 согласно контракту specs/review-api-contract.md. Без сторонних библиотек: один index.html со встроенным CSS и vanilla JS (fetch); без хранения diff и логов.

## Technical Context

**Language/Version**: Python 3.11 (проект), HTML/CSS/JavaScript для UI страницы

**Primary Dependencies**: FastAPI (существующий), без новых зависимостей для UI

**Storage**: N/A (нет хранения на клиенте)

**Testing**: pytest; добавим tests/test_ui_page.py для GET / и сценариев UI (описаны в quickstart.md)

**Target Platform**: Локальная среда разработки; FastAPI app

**Project Type**: Web-service с одной статической страницей

**Performance Goals**: Рендер страницы < 200ms локально; без ощутимой задержки валидации счётчика; один сетевой запрос на отправку

**Constraints**: Без сборщиков/библиотек; одна HTML-страница; строгое соблюдение SEC-1 и OBS-1; не менять контракт POST /api/reviews

**Scale/Scope**: Одна страница, один API вызов; ограничение diff до 20 000 символов

## Constitution Check

- Принцип V: простота — один index.html, без зависимостей; UI в том же процессе FastAPI.
- SEC-1/OBS-1: не хранить diff, не логировать содержимое diff/ответов; вывод данных через textContent.
- Разделение обязанностей: UI добавляет только GET / (app/api.py), POST /api/reviews не меняется.

## Project Structure

### Documentation (this feature)

```text
specs/001-review-ui/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md (via /speckit.tasks)
```

### Source Code (repository root)

```text
app/
├── api.py              # существующий FastAPI; UI добавит только маршрут GET /
└── static/
    └── index.html      # новая статическая страница (HTML + inline CSS + vanilla JS)

tests/
└── test_ui_page.py     # тесты UI маршрута и DOM-элементов
```

**Structure Decision**: Brownfield в существующем FastAPI: добавляем один статический файл app/static/index.html и маршрут GET / в app/api.py. Контракт POST /api/reviews остаётся неизменным (specs/review-api-contract.md).

## Complexity Tracking

N/A — нарушений конституции нет.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Добавить статическую страницу app/static/index.html (HTML + inline CSS + vanilla JS) с формой: textarea[id=diff], счётчик id=counter, кнопки id=submit и id=clear, блоки id=result и id=error.
2. Добавить маршрут GET / в app/api.py, отдающий app/static/index.html (FileResponse/HTMLResponse), без новых зависимостей.
3. Реализовать в JS: валидация длины 20 000, блокировка кнопки при in-flight, fetch POST /api/reviews с JSON {diff}, вставка результатов только через textContent, обработка ошибок по HTTP-статусу.
4. Успешный рендер: summary; риски (title; для diff_line — file:line и proof; для rule — rule); checks (строки); отметка при secrets_masked > 0.

### Incremental Delivery

- US1 (P1): успешный сценарий 200 и базовая валидация/блокировка.
- US2 (P2): ошибки 400/413/422/502/504 и сетевая ошибка.
- US3 (P3): очистка и отсутствие хранения.

### Parallel Team Strategy

- Параллельные задачи только по документации/тестам; реализация UI — одна страница, конфликты минимальны.

## Notes

- Избегать innerHTML для данных; только textContent.
- Не добавлять сторонние библиотеки/сборщики.
- contracts/: использовать только specs/review-api-contract.md.

## Research (Phase 0)

- Контракт: specs/review-api-contract.md (решения D1–D10). UI следует ему строго.
- Ограничения: один HTML с inline CSS и vanilla JS (fetch).

## Data Model (Phase 1)

- UI-модель ответа: { summary: string, risks: { title: string, evidence: { diff_line | rule } }[], checks: string[], secrets_masked: number }
- Ошибки: HTTP 400/413/422/502/504 с телом { error: string } (+ limit для 413). Сообщения — по статусу.

## Quickstart (Phase 1)

Быстрые проверки в браузере (сквозные):

1) Загрузка страницы
 - Открыть GET /. Проверить наличие: textarea[id=diff], span[id=counter] «0/20000», кнопки id=submit, id=clear, блоки id=result и id=error.

2) Валидный запрос (P1)
 - Вставить короткий unified diff. Кнопка активна. Нажать «Получить ревью». Во время запроса кнопка disabled. При 200 мок-ответе отобразить summary, не более 3 рисков (title; для diff_line — file:line и proof; для rule — rule), список checks (строки). Если secrets_masked > 0 — показать «Секреты в diff были замаскированы».

3) Ошибки (P2)
 - 400: показать «Пустой diff…». 413: «Слишком большой diff…». 422: «Неверный запрос…». 502: «LLM недоступен…». 504: «LLM не ответил вовремя…». Сетевая ошибка: «Сетевая ошибка…».

4) Лимит (P2)
 - При длине >20000 кнопка отключена; 20000 — включена. Счётчик корректно показывает N/20000.

5) Очистка (P3)
 - Нажать «Очистить»: поле пусто, счётчик 0/20000, скрыть результат/ошибку.

6) Безопасность
 - Не используется localStorage/sessionStorage; в консоли нет логов с содержимым diff/ответа; вставка данных через textContent.

## Contracts (Phase 1)

- Использовать существующий контракт: specs/review-api-contract.md. Не добавлять новые поля/энумов/метаданные от себя.
