# Feature Specification: Review Assistant Web UI

**Feature Branch**: `[001-review-ui]`

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Веб-страница помощника ревьюера для существующего сервиса ai-review-api. Страница открывается по GET / (тот же FastAPI). Пользователь вставляет diff в текстовое поле и нажимает «Получить ревью»; страница вызывает POST /api/reviews. Экраны/действия: поле diff, счётчик символов (лимит 20 000), кнопки «Получить ревью» и «Очистить». Состояния: пусто, ввод, загрузка (кнопка заблокирована, нет повторного запроса), успех, ошибка. Успех: summary, до 3 рисков (file, line, evidence), список проверок, отметка, что секреты замаскированы. Ошибки: сообщения для 400/413/422/502/504 и сетевой ошибки; при 502/504 — подсказка продолжить ревью вручную. Страница не хранит diff и не показывает секреты."

## User Scenarios & Testing (mandatory)

### User Story 1 - Получить ревью для валидного diff (Priority: P1)

Как пользователь, я хочу вставить корректный unified diff и получить полезный результат ревью, чтобы быстро понять суть изменений и риски.

**Why this priority**: Это основной поток, обеспечивающий ценность фичи.

**Independent Test**: Может быть протестирован автономно через мок ответов API: один успешный POST /api/reviews возвращает 200 и UI показывает summary/risks/checks.

**Acceptance Scenarios**:

1. Given страница "/" загружена и поле diff содержит непустой текст длиной ≤ 20000, When пользователь нажимает «Получить ревью», Then отправляется ровно один POST /api/reviews, кнопка блокируется до ответа, затем отображаются summary, до трёх risks, список checks, и заметка о маскировании секретов (если указано в ответе).
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
5. Given сервер возвращает 502 или 504, When пользователь отправляет запрос, Then UI показывает соответствующее сообщение и подсказку «Продовжите ревью вручную».
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
- Отсутствует поле redactionsApplied в ответе 200 — UI показывает нейтральную фразу «Если в diff были секреты, сервис их маскирует».
- Список checks пуст — UI показывает «Нет дополнительных проверок».
- Неизвестные поля в ответе — игнорируются безопасно.
- Длинное evidence (>300 символов) — UI обрезает и показывает «…».

## Requirements (mandatory)

### Functional Requirements

- FR-001: UI MUST be served at GET / by the same FastAPI application (same-origin).
- FR-002: UI MUST provide a textarea for unified diff input with a live character counter (N/20000).
- FR-003: UI MUST enforce a client-side limit of 20000 characters; when exceeded, disable «Получить ревью» and show a warning.
- FR-004: UI MUST send POST /api/reviews with JSON body { diff: string } and headers Accept: application/json, Content-Type: application/json.
- FR-005: UI MUST prevent duplicate submissions by disabling the submit button during in-flight requests and ensuring exactly one POST per click.
- FR-006: UI MUST render success results: summary, up to three risks (file, line, evidence), checks list, and a redaction notice.
- FR-007: UI MUST map specific errors to messages (400, 413, 422, 502, 504) and a generic network error message.
- FR-008: UI MUST provide a «Очистить» action that resets input and results to the idle state.
- FR-009: UI MUST NOT store diff or results in localStorage/sessionStorage and MUST NOT log diff or response contents (SEC-1, OBS-1).
- FR-010: UI MUST escape all texts from the API before rendering in the DOM.
- FR-011: UI SHOULD truncate overly long evidence to ~300 characters with an ellipsis.
- FR-012: UI SHOULD display status colors for checks: pass (green), warn (yellow), fail (red).
- FR-013: [NEEDS CLARIFICATION: 200 OK response schema — fields, types, and semantics for summary, risks (file, line base), checks (status vocabulary), and any extra metadata]
- FR-014: [NEEDS CLARIFICATION: Error body schema — presence of { code, message, details? } for 4xx/5xx, consistency across codes]
- FR-015: [NEEDS CLARIFICATION: Redaction indicator — field name (e.g., redactionsApplied: boolean) and whether maskedCount is provided]

### Key Entities

- ReviewRequest: { diff: string }
- ReviewResult: { summary: string, risks: Risk[], checks: Check[], redactionsApplied?: boolean, maskedCount?: number }
- Risk: { file: string, line: number, evidence: string }
- Check: { name: string, status: 'pass'|'warn'|'fail', details?: string }
- ErrorModel: { code?: string, message: string, details?: any }

## Success Criteria (mandatory)

### Measurable Outcomes

- SC-001: For any non-empty diff with length ≤ 20000, clicking «Получить ревью» triggers exactly one POST /api/reviews and disables the button within 100ms until the response completes (verified in browser DevTools).
- SC-002: With a stubbed 200 response, UI displays: summary text, up to three risks (showing file:line and evidence), and a checks list; evidence over 300 chars is truncated with an ellipsis.
- SC-003: With server responses 400/413/422/502/504 and a simulated network error, UI shows the specified RU messages and does not retry automatically.
- SC-004: When response includes redactionsApplied=true, UI shows the note «Секреты в diff были замаскированы»; when the field is absent, UI shows the neutral note «Если в diff были секреты, сервис их маскирует».
- SC-005: The «Очистить» action resets the form and results; after reset, the submit button is disabled and counter shows 0/20000.
- SC-006: No usage of localStorage/sessionStorage and no console logging of diff or response content (verified via DevTools Application and Console tabs).
- SC-007: For input length 20001, the submit button remains disabled and the limit warning is visible; for length 20000, the button is enabled.

## Assumptions

- API returns JSON responses; all server-side secrets are already masked; UI never receives raw secrets.
- Risk line numbers are 1-based and refer to the new version (post-change) unless otherwise specified by backend.
- Checks status vocabulary is {'pass','warn','fail'}; unknown statuses are rendered as neutral.
- The UI and API are same-origin; no CORS or CSRF token management is required for this feature.
- The UI does not display the original diff in results and ignores unknown fields in the response.
- Error responses include a human-readable message string; UI uses provided message when available.
- Accessibility and i18n beyond RU copy are out of scope for v1.
