# Requirements Checklist: Review Assistant Web UI

**Purpose**: Reviewer-owned checklist to verify requirements quality for the Review Assistant Web UI.
**Created**: 2026-11-02
**Feature**: specs/001-review-ui/spec.md

## Functional Requirements Coverage

- [ ] CHK-FR-001: GET / serves the UI via the same FastAPI application (same-origin confirmed).
- [ ] CHK-FR-002: Textarea input with live counter enforces 20 000 char limit; UX warning shown when exceeded.
- [ ] CHK-FR-003: Submit disables during in-flight request; single POST per click is verified.
- [ ] CHK-FR-004: POST /api/reviews uses JSON body { diff: string } and correct headers.
- [ ] CHK-FR-005: Success rendering includes summary, up to 3 risks (file, line, evidence), checks list, and redaction notice.
- [ ] CHK-FR-006: Error mapping covers 400, 413, 422, 502, 504 and network errors with specified RU messages.
- [ ] CHK-FR-007: "Очистить" resets input/results; returns to idle state.
- [ ] CHK-FR-008: No localStorage/sessionStorage usage; no console logging of diff or response contents.
- [ ] CHK-FR-009: All texts escaped before DOM rendering.
- [ ] CHK-FR-010: Evidence truncation (~300 chars) implemented.

## Security & Privacy (SEC-1, OBS-1)

- [ ] CHK-SEC-001: UI does not display raw diff in results; only masked evidence is shown.
- [ ] CHK-SEC-002: UI avoids storing sensitive data in browser storage; verifies none present.
- [ ] CHK-SEC-003: UI avoids logging diff and responses; console is clean of sensitive content.

## Error Contract

- [ ] CHK-ERR-001: Client-side validation prevents empty input and >20000 length submissions.
- [ ] CHK-ERR-002: UI messages match required copy per status code; fallback for unknown 5xx present.

## Success Criteria Validation

- [ ] CHK-SC-001: Single-request guarantee and button disabling within 100ms validated.
- [ ] CHK-SC-002: Success rendering verified with stubbed 200; truncation works.
- [ ] CHK-SC-003: Error scenarios validated for all specified codes and network errors.
- [ ] CHK-SC-004: Redaction indicator behavior validated for both presence and absence.
- [ ] CHK-SC-005: Reset behavior verified; counter returns to 0/20000.
- [ ] CHK-SC-006: No storage/logging validated.

## Notes

- Mark items "[x]" only after reviewer confirms the requirement-quality criterion is satisfied.
- Items track requirements quality, not implementation completeness.
