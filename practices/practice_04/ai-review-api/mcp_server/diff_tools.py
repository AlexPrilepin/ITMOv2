"""Собственный MCP-сервер проекта: tool check_diff.

Зачем он нужен агенту: перед работой с diff проверить его по правилам
проекта, не угадывая. Tool проверяет правило API-1 (лимит 20 000 символов)
и правило SEC-1 (секреты в diff), а для найденных секретов возвращает
номера строк и diff с заменой на [REDACTED].

Проверка вручную: make mcp-demo (корректный вход, секрет и ошибочный вход).
В OpenCode сервер запускается сам по настройке в opencode.json.
"""

from __future__ import annotations

import re

DIFF_LIMIT = 20_000  # API-1: diff длиннее 20 000 символов отклоняется

# SEC-1: что считаем секретом. Список намеренно короткий и проверяемый.
SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "bearer_token": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{16,}"),
    # Имя переменной оставляем, скрываем только значение.
    "assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"]?(?P<value>[^\s'\"]{6,})"
    ),
}


def _redact(match: re.Match[str]) -> str:
    if "value" not in match.re.groupindex:
        return "[REDACTED]"
    start, end = match.span("value")
    text = match.group(0)
    offset = match.start()
    return text[: start - offset] + "[REDACTED]" + text[end - offset :]


class DiffInputError(ValueError):
    """Вход не подходит для проверки: tool возвращает ошибку, а не результат."""


def _looks_like_diff(text: str) -> bool:
    return "diff --git" in text or ("--- " in text and "+++ " in text) or "@@" in text


def analyze_diff(diff: object) -> dict:
    """Чистая функция без MCP: её же проверяют unit-тесты."""
    if not isinstance(diff, str):
        raise DiffInputError("diff must be a string")
    if not diff.strip():
        raise DiffInputError("diff is empty")
    if not _looks_like_diff(diff):
        raise DiffInputError(
            "input is not a unified diff: expected 'diff --git', '---/+++' headers or '@@' hunks"
        )

    findings = []
    redacted_lines = []
    for number, line in enumerate(diff.splitlines(), start=1):
        clean = line
        for kind, pattern in SECRET_PATTERNS.items():
            if pattern.search(clean):
                findings.append({"line": number, "kind": kind})
                clean = pattern.sub(_redact, clean)
        redacted_lines.append(clean)

    chars = len(diff)
    return {
        "chars": chars,
        "limit": DIFF_LIMIT,
        "within_limit": chars <= DIFF_LIMIT,  # API-1
        "expected_http_status": 200 if chars <= DIFF_LIMIT else 413,
        "secrets_found": findings,  # SEC-1
        "safe_to_send_to_llm": not findings,
        "redacted_diff": "\n".join(redacted_lines) if findings else None,
    }


def main() -> None:
    try:  # mcp >= 2.0
        from mcp.server.mcpserver import MCPServer as Server
        from mcp.server.mcpserver.exceptions import ToolError
    except ImportError:  # mcp 1.x
        from mcp.server.fastmcp import FastMCP as Server
        from mcp.server.fastmcp.exceptions import ToolError

    server = Server("diff-tools")

    @server.tool()
    def check_diff(diff: str) -> dict:
        """Check a pull-request diff against project rules API-1 and SEC-1.

        Returns the diff size and whether it fits the 20 000 character limit
        (API-1, otherwise the API must answer HTTP 413), plus every line that
        looks like a secret (SEC-1) and a redacted copy of the diff.
        Fails with an error if the input is empty or not a unified diff.
        """
        try:
            return analyze_diff(diff)
        except DiffInputError as exc:
            # ToolError: понятная ошибка уходит агенту как is_error-результат,
            # а не как падение сервера.
            raise ToolError(str(exc)) from exc

    server.run()  # stdio


if __name__ == "__main__":
    main()
