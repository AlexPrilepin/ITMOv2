# Feature Specification: Review Assistant Web UI

**Feature Branch**: `[001-review-ui]`

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Веб-страница помощника ревьюера для существующего сервиса ai-review-api. Страница открывается по GET / (тот же FastAPI). Пользователь вставляет diff в текстовое поле и нажимает «Получить ревью»; страница вызывает POST /api/reviews. Экраны/действия: поле diff, счётчик символов (лимит 20 000), кнопки «Получить ревью» и «Очистить». Состояния: пусто, ввод, загрузка (кнопка заблокирована, нет повторного запроса), успех, ошибка. Успех: summary, до 3 рисков (title + evidence), список checks, отметка, что секреты замаскированы. Ошибки: сообщения для 400/413/422/502/504 и сетевой ошибки; при 502/504 — подсказка продолжить ревью вручную. Страница не хранит diff и не показывает секреты."

## User Scenarios & Testing (mandatory)

### User Story 1 - Получить ревью для валидного diff (Priority: P1)

Как пользователь, я хочу вставить корректный unified diff и получить полезный результат ревью, чтобы быстро понять суть изменений и риски.

**Why this priority**: Это основной поток, обеспечивающий ценность фичи.

**Independent Test**: Может быть протестирован автономно через мок ответов API: один успешный POST /api/reviews возвращает 200 и UI показывает summary/risks/checks.

**Acceptance Scenarios**:

1. Given страница "/" загружена и поле diff содержит непустой текст длиной ≤ 20000, When пользователь нажимает «Получить ревью», Then отправляется ровно один POST /api/reviews, кнопка блокируется до ответа, затем отображаются summary, до трёх risks (с title), список checks (строки), и отметка о маскировании секретов, если secrets_masked > 0.
2. Given поле diff содержит ровно 20000 символов, When пользователь нажимает «Получить ревью», Then запрос принимается и обрабатывается, UI переходит в состояние loading и далее — success при ответе 200.

---

### User Story 2 - Понятные сообщения об ошибках (Priority: P2)

Как пользователь, я хочу видеть понятные сообщения для ошибок сервиса и сети, чтобы быстро исправить ввод или понять, что делать дальше.

**Why this priority**: Улучшает UX и снижает число повторных попыток и обращений в поддержку.

**Independent Test**: Может быть протестирован через заглушки API для кодов 400/413/422/502/504 и симуляцию сетевой ошибки.

**Acceptance Scenarios**:

1. Given поле пустое, When нажать «Получить ревью», Then кнопка неактивна и запрос не отправляется.
2. Given поле содержит >20000 символов, When нажать «Получить ревью», Then кнопка неактивна и показывается предупреждение о лимите; при обходе проверки сервер вернёт 413 и UI покажет «Слишком большой diff. Лимит — 20 000 символов.»
3. Given сервер возвращает 400, When пользователь отправляет запрос, Then UI показывает «Пустой diff. Вставьте содержимое diff и повторите попытку.»
4. Given сервер возвращает 422, When пользователь отправляет запрос, Then UI показывает «Неверный запрос. Проверьте формат diff.»
5. Given сервер возвращает 502 или 504, When пользователь отправляет запрос, Then UI показывает соответствующее сообщение и подсказку «Продолжите ревью вручную».
6. Given сетевая ошибка, When отправить запрос, Then UI показывает «Сетевая ошибка. Проверьте соединение и попробуйте ещё раз.»

---

### User Story 3 - Очистка и отсутствие хранения (Priority: P3)

Как пользователь, я хочу быстро сбросить состояние и быть уверен, что мои данные не сохраняются в браузере.

**Why this priority**: Важная составляющая приватности и удобства.

**Independent Test**: Тестируется локально без сервера — кнопка «Очистить» сбрасывает поле и результат, localStorage/sessionStorage не используются.

**Acceptance Scenarios**:

1. Given введён diff и отображён результат, When нажать «Очистить», Then поле очищено, счётчик 0/20000, результат скрыт, состояние возвращается к idle.
2. Given страница перезагружена, When открыть DevTools Application Storage, Then localStorage и sessionStorage не содержат ключей, связанных с диффом или результатами.

### Edge Cases

- Пустая строка/только пробелы — кнопка «Получить ревью» неактивна.
- Ровно 20000 символов — допустимо; 20001 — недопустимо (кнопка неактивна, предупреждение).
- Длительный ответ сервера — состояние loading до завершения; повторные клики не отправляют второй запрос.
- secrets_masked = 0 — отметка «Секреты в diff были замаскированы» не показывается.
- Список checks пуст — UI показывает «Нет дополнительных проверок».
- Неизвестные поля в ответе — игнорируются безопасно.
- Длинный proof (>300 символов) — UI обрезает и показывает «…».
- Пустая summary от модели — UI показывает "review summary unavailable" (из ответа сервиса).

## Requirements (mandatory)

### Functional Requirements

- FR-001: UI MUST be served at GET / by the same FastAPI application (same-origin).
- FR-002: UI MUST provide a textarea for unified diff input with a live character counter (N/20000).
- FR-003: UI MUST enforce a client-side limit of 20000 characters; when exceeded, disable «Получить ревью» and show a warning.
- FR-004: UI MUST send POST /api/reviews with JSON body { diff: string } and headers Accept: application/json, Content-Type: application/json.
- FR-005: UI MUST prevent duplicate submissions by disabling the submit button during in-flight requests and ensuring exactly one POST per click.
- FR-006: UI MUST render success results: summary (непустая строка), до трёх risks с title; для evidence.type = "diff_line" отображать file:line и proof; для evidence.type = "rule" отображать rule; checks как массив строк; и отметку о маскировании, когда secrets_masked > 0.
- FR-007: UI MUST map specific errors to messages (400, 413, 422, 502, 504) and a generic network error message; сообщения выбираются по HTTP-статусу.
- FR-008: UI MUST provide a «Очистить» action that resets input and results to the idle state.
- FR-009: UI MUST NOT store diff or results in localStorage/sessionStorage and MUST NOT log diff or response contents (SEC-1, OBS-1).
- FR-010: UI MUST escape all texts from the API before rendering in the DOM.
- FR-011: UI SHOULD truncate overly long proof to ~300 characters with an ellipsis.
- FR-013: Success response schema is fixed by contract: { summary: string, risks: Risk[0..3], checks: string[], secrets_masked: integer ≥ 0 }. Risk.evidence is a union: {type: "diff_line", file: string, line: 1-based (new file), proof: string} | {type: "rule", rule: one of SEC-1, API-1, REL-1, OUT-1, SCOPE-1, QA-1, OBS-1}.
- FR-014: Error response schema is fixed by contract: body is {"error": string}; for 413 also {"limit": 20000}. UI chooses user-facing messages by HTTP status.
- FR-015: Redaction indicator is fixed by contract: secrets_masked is an integer; UI shows the note only when secrets_masked > 0.

### Key Entities

- ReviewRequest: { diff: string }
- ReviewResult: { summary: string, risks: Risk[], checks: string[], secrets_masked: number }
- Risk: { title: string, evidence: Evidence }
- Evidence (union):
  - Diff line: { type: "diff_line", file: string, line: number (1-based, new file), proof: string }
  - Rule: { type: "rule", rule: 'SEC-1'|'API-1'|'REL-1'|'OUT-1'|'SCOPE-1'|'QA-1'|'OBS-1' }
- ErrorModel: { error: string, limit?: number }

## Success Criteria (mandatory)

### Measurable Outcomes

- SC-001: For any non-empty diff with length ≤ 20000, clicking «Получить ревью» triggers exactly one POST /api/reviews and disables the button within 100ms until the response completes (verified in browser DevTools).
- SC-002: With a stubbed 200 response, UI displays: summary text, up to three risks (showing title; for diff_line — file:line и proof; for rule — rule label), and a checks list (strings); proof over 300 chars is truncated with an ellipsis.
- SC-003: With server responses 400/413/422/502/504 and a simulated network error, UI shows the specified RU messages and does not retry automatically.
- SC-004: When secrets_masked > 0, UI shows the note «Секреты в diff были замаскированы»; when secrets_masked = 0, the note is not shown.
- SC-005: The «Очистить» action resets the form and results; after reset, the submit button is disabled and counter shows 0/20000.
- SC-006: No usage of localStorage/sessionStorage and no console logging of diff or response content (verified via DevTools Application and Console tabs).
- SC-007: For input length 20001, the submit button remains disabled and the limit warning is visible; for length 20000, the button is enabled.

## Assumptions

- API returns JSON responses per contract; UI never receives raw secrets; proof text is derived from the masked diff (contains only [SECRET] where applicable).
- Risk line numbers are 1-based and refer to the new version (right side of hunk); diff_line evidence refers only to added or context lines; risks about deletions are confirmed via rule evidence.
- Checks are plain strings without statuses or coloring; UI does not assign or infer statuses.
- The UI and API are same-origin; no CORS or CSRF token management is required for this feature.
- The UI does not display the original diff in results and ignores unknown fields in the response; no requestId/model/elapsedMs metadata is present.
- UI preserves the order of risks as provided by the service and displays at most three.
- Accessibility and i18n beyond RU copy are out of scope for v1.

## Clarifications (Session 2026-11-02)

- Q: Каков точный формат риска и что показывать в UI? → A: Risk имеет поля title и evidence: для type=diff_line показывать file:line и proof; для type=rule показывать метку правила. UI также показывает title. Решение D1.
- Q: Каков формат поля checks? → A: checks — массив строк без статусов и цветов. Решение D2.
- Q: Как определить и показывать отметку о маскировании секретов? → A: В ответе есть secrets_masked (integer ≥ 0); UI показывает отметку только если secrets_masked > 0. Решение D3.
- Q: Каков формат тела ошибок и выбор пользовательского сообщения? → A: Тело ошибки — {"error": "..."}; у 413 дополнительно {"limit": 20000}. UI выбирает сообщение по HTTP-статусу. Решение D4.
- Q: Как интерпретировать line в evidence.type=diff_line? → A: 1-based номер строки в новой версии файла (правая сторона hunk); ссылаться можно на добавленные и контекстные строки. Решение D5.
- Q: Сколько рисков показывать и есть ли severity? → A: До 3, порядок как у модели; поля severity нет. Решение D6.
- Q: Можно ли утечь секрет через proof? → A: Нет; proof берётся из замаскированного diff и содержит только [SECRET]. Решение D7.
- Q: Что делать, если модель вернула пустую summary? → A: summary = "review summary unavailable"; риски и checks пустые. Решение D8.
- Q: Какие метаданные приходят в ответе? → A: Доп. метаданных (requestId, model, elapsedMs) нет. Решение D9.
- Q: Что с backward-compat полем comment? → A: Поле comment удалено; UI его не ожидает. Решение D10.
