# Data Model: Review Assistant Web UI (Phase 1)

## Entities

- ReviewRequest
  - diff: string (≤ 20000)

- ReviewResult
  - summary: string (non-empty)
  - risks: Risk[0..3]
  - checks: string[]
  - secrets_masked: number (integer ≥ 0)

- Risk
  - title: string
  - evidence: Evidence

- Evidence (union)
  - diff_line: { type: "diff_line", file: string, line: number (1-based, new file), proof: string }
  - rule: { type: "rule", rule: 'SEC-1'|'API-1'|'REL-1'|'OUT-1'|'SCOPE-1'|'QA-1'|'OBS-1' }

- ErrorModel
  - error: string
  - limit?: number (only for 413)

## Notes

- checks — строки; статусов/цветов нет.
- proof — подстрока замаскированного diff; содержит только [SECRET] вместо значений.
- UI показывает отметку маскирования, если secrets_masked > 0.
