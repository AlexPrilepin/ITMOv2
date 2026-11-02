"""Ручная проверка собственного MCP-сервера без OpenCode.

Запускает mcp_server/diff_tools.py по stdio, как это делает OpenCode,
и вызывает tool check_diff на трёх входах: корректный diff, diff с секретом
и ошибочный вход. Вывод можно сохранить как подтверждение:

    make mcp-demo | tee evidence/mcp-demo.txt
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# В Git Bash на Windows вывод по умолчанию не в UTF-8 — русский текст ломается.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

CASES = {
    "корректный diff": "diff --git a/app/x.py b/app/x.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n",
    "diff с секретом": 'diff --git a/app/x.py b/app/x.py\n@@ -1 +1 @@\n+API_KEY = "sk-test-1234567890"\n',
    "ошибочный вход": "please review my code",
}


def _text(result) -> str:
    return "\n".join(getattr(block, "text", str(block)) for block in result.content)


def _is_error(result) -> bool:
    return bool(getattr(result, "is_error", getattr(result, "isError", False)))


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable, args=[str(ROOT / "mcp_server" / "diff_tools.py")], cwd=str(ROOT)
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools:", [tool.name for tool in tools.tools])
            for title, diff in CASES.items():
                result = await session.call_tool("check_diff", {"diff": diff})
                status = "ERROR" if _is_error(result) else "OK"
                print(f"\n=== {title}: {status}\n{_text(result)}")


if __name__ == "__main__":
    asyncio.run(main())
