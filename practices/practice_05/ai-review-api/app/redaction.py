import re
from typing import Tuple


# Minimal secret detectors aligned with project MCP server, but local and using [SECRET]
SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    # Loosen length to cover shorter examples used in tests
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{12,20}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    # Bearer anywhere in the line
    "bearer_any": re.compile(r"(?i)Bearer\s+[A-Za-z0-9._\-/]{8,}"),
}


# Assignments `KEY = value`, `KEY: value`, `"key": "value"`.
# Review fix (ReDoS): the key is anchored to the start of an identifier and the
# secret word is checked in Python, so the scan is linear in the line length.
ASSIGNMENT = re.compile(
    r"(?<![A-Za-z0-9_\-])(?P<key>[A-Za-z0-9_\-]+)(?P<kq>[\"']?)[ \t]*[:=][ \t]*(?P<vq>[\"']?)(?P<value>[^\s'\"]{6,})"
)
SECRET_KEY_WORDS = (
    "password", "passwd", "pwd", "secret", "token",
    "api_key", "apikey", "private_key", "access_key",
)
MARKER = "[SECRET]"


def _is_secret_assignment(match: re.Match[str]) -> bool:
    key = match.group("key").lower().replace("-", "_")
    return match.group("value") != MARKER and any(word in key for word in SECRET_KEY_WORDS)


def _secret_assignments(content: str):
    return [m for m in ASSIGNMENT.finditer(content) if _is_secret_assignment(m)]


def _mask_assignments(content: str) -> tuple[str, int]:
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        if not _is_secret_assignment(match):
            return match.group(0)
        count += 1
        return _mask_assignment(match)

    return ASSIGNMENT.sub(repl, content), count


def _mask_assignment(match: re.Match[str]) -> str:
    if "value" not in match.re.groupindex:
        return "[SECRET]"
    start, end = match.span("value")
    text = match.group(0)
    offset = match.start()
    # Remove wrapping quotes around the value if present
    left = text[: start - offset]
    right = text[end - offset :]
    if left.endswith('"') or left.endswith("'"):
        left = left[:-1]
    if right.startswith('"') or right.startswith("'"):
        right = right[1:]
    return left + "[SECRET]" + right


def redact_diff(diff: str) -> Tuple[str, int]:
    """
    Returns a masked copy of the diff and the number of replacements performed.
    Masking uses the literal marker [SECRET].
    """
    masked_lines = []
    count = 0
    in_pem = False
    for line in diff.splitlines():
        # Handle unified diff line prefix
        prefix = ""
        content = line
        if line[:1] in {" ", "+", "-"}:
            prefix = line[0]
            content = line[1:]

        # Handle PEM private key blocks: keep BEGIN/END markers, mask body lines. BEGIN can be anywhere in the line
        if not in_pem and ("-----BEGIN " in content and "PRIVATE KEY-----" in content):
            masked_lines.append(prefix + content)
            in_pem = True
            continue
        if in_pem:
            if ("-----END " in content and "PRIVATE KEY-----" in content):
                masked_lines.append(prefix + content)
                in_pem = False
            else:
                masked_lines.append(prefix + "[SECRET]")
                count += 1
            continue

        clean = content
        for kind, pattern in SECRET_PATTERNS.items():
            if kind == "bearer_any":
                # Replace token after "Bearer "
                def repl_bearer(m: re.Match[str]) -> str:
                    return "Bearer [SECRET]"
                clean, n = pattern.subn(repl_bearer, clean)
            else:
                clean, n = pattern.subn("[SECRET]", clean)
            count += n
        clean, n = _mask_assignments(clean)
        count += n
        # Normalize quotes around [SECRET]
        clean = (
            clean.replace('"[SECRET]"', '[SECRET]')
                 .replace("'[SECRET]'", '[SECRET]')
                 .replace('= [SECRET]"', '= [SECRET]')
                 .replace("= [SECRET]'", '= [SECRET]')
        )
        masked_lines.append(prefix + clean)
    return "\n".join(masked_lines), count


def extract_secret_values(diff: str) -> set[str]:
    """Collect raw secret values that would be masked from the given diff."""
    values: set[str] = set()
    in_pem = False
    for line in diff.splitlines():
        content = line[1:] if line[:1] in {" ", "+", "-"} else line
        if not in_pem and ("-----BEGIN " in content and "PRIVATE KEY-----" in content):
            in_pem = True
            continue
        if in_pem:
            if ("-----END " in content and "PRIVATE KEY-----" in content):
                in_pem = False
            else:
                if content.strip():
                    values.add(content.strip())
            continue
        # Assignments
        for m in _secret_assignments(content):
            values.add(m.group("value"))
        # Bearer
        m = re.search(r"(?i)Bearer\s+([A-Za-z0-9._\-/]{8,})", content)
        if m:
            values.add(m.group(1))
        # AWS AKIA
        for m in SECRET_PATTERNS["aws_access_key"].finditer(content):
            values.add(m.group(0))
        # GitHub token
        for m in SECRET_PATTERNS["github_token"].finditer(content):
            values.add(m.group(0))
    return values
