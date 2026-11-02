# Проверка правила OpenSpec `rules.design` (часть 2, шаги 7–8)

## Правило

`openspec/config.yaml`:

```yaml
rules:
  design:
    - Объясни взаимодействие диаграммой Mermaid.
```

Агент получил правило через `openspec instructions design --change request-observability --json` и процитировал его до правки.

## Фрагмент

- «До»: `docs/sdd/04-design-before.md` — design.md, сгенерированный в отдельной сессии без правила и без упоминания диаграмм (83 строки, Mermaid нет).
- «После»: `openspec/changes/request-observability/design.md`.

Первая попытка «до» была отброшена: правило попало в тот же промпт, что и генерация design, и модель добавила диаграмму заранее — сравнивать было не с чем. Design перегенерирован в новой сессии при временно убранном правиле.

## Diff до → после

```diff
77a78,98
>  
> ## Interaction Diagram
> 
> ```mermaid
> sequenceDiagram
>     participant C as Client
>     participant M as Middleware (/api/reviews)
>     participant H as Handler POST /api/reviews
>     participant S as ReviewService / LLM
>     participant L as Logger
> 
>     C->>M: POST /api/reviews {diff}
>     M->>M: generate request_id; start timer
>     M->>H: call_next(request)
>     H->>S: process diff (no logging of payload)
>     S-->>H: result / errors (502/504 possible)
>     H-->>M: Response (200/400/413/422/502/504)
>     M->>M: stop timer; compute duration_ms
>     M->>L: log {request_id, duration_ms, status}
>     M-->>C: Response (unchanged)
> ```
```

Изменение — только добавление раздела `## Interaction Diagram` (21 строка). Context, Goals/Non-Goals, Decisions, Risks, Migration Plan, Open Questions не изменены: смысл и границы сохранены.

Отрисованная диаграмма (OpenCode): `docs/sdd/05-mermaid-rendered.png`.

## Наблюдение

Агент первый раз прислал патч, где строки диаграммы были помечены `-` вместо `+`; при буквальном применении получился бы пустой блок. Ошибка найдена при ревью diff до подтверждения — подтверждение человека на этом шаге не формальность.

`openspec validate request-observability --type change --strict --no-interactive` → valid. Код не менялся; change остаётся черновиком (apply не выполнялся — по условию части 2).
