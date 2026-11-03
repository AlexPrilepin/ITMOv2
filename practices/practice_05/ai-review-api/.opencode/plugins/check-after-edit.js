// Hook для OpenCode 2: после каждой успешной правки файла (edit/write/patch)
// запускает доверенный runner scripts/check.sh и дописывает его результат
// в ответ инструмента. Так агент сразу видит PASS или FAIL и может исправиться.
// Каждый запуск также пишется в logs/hook-runs.log: это подтверждение для сдачи.
//
// Формат плагина OpenCode 2: default export с id и setup(ctx).
// Хуки V1 ("tool.execute.after") в OpenCode 2 не исполняются.

import { spawnSync } from "node:child_process"
import { appendFileSync, existsSync, mkdirSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const EDIT_TOOLS = new Set(["edit", "write", "patch"])
const MAX_LINES = 40
const RUNNER = path.join("scripts", "check.sh")

// Папка проекта: та, где лежит scripts/check.sh.
function findRoot(ctx) {
  const candidates = [ctx.location?.directory]
  try {
    // .opencode/plugins/check-after-edit.js -> корень проекта на два уровня выше
    candidates.push(path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", ".."))
  } catch {
    // import.meta.url может быть недоступен — тогда остаётся location.directory
  }
  return candidates.find((dir) => dir && existsSync(path.join(dir, RUNNER))) ?? ctx.location?.directory
}

function pythonFor(root) {
  const win = path.join(root, ".venv", "Scripts", "python.exe")
  const unix = path.join(root, ".venv", "bin", "python")
  if (existsSync(win)) return win
  if (existsSync(unix)) return unix
  return process.platform === "win32" ? "python" : "python3"
}

// Сначала доверенный runner через sh/bash; если их нет в PATH — тот же unittest напрямую.
function runCheck(root) {
  const options = { cwd: root, encoding: "utf8", timeout: 120_000 }
  const attempts = [
    ["sh", [RUNNER]],
    ["bash", [RUNNER]],
    [pythonFor(root), ["-m", "unittest", "discover", "-s", "tests", "-t", "."]],
  ]
  for (const [command, args] of attempts) {
    const run = spawnSync(command, args, options)
    if (run.error && run.error.code === "ENOENT") continue
    const output = `${run.stdout ?? ""}${run.stderr ?? ""}`.trim()
    return {
      status: run.status === 0 ? "PASS" : "FAIL",
      code: run.status,
      runner: `${path.basename(command)} ${args.join(" ")}`,
      tail: output.split("\n").slice(-MAX_LINES).join("\n"),
    }
  }
  return { status: "FAIL", code: null, runner: "none", tail: "Не найден ни sh, ни bash, ни python" }
}

function appendToResult(result, text) {
  const content = result?.content
  if (Array.isArray(content)) return { ...result, content: [...content, { type: "text", text }] }
  if (typeof content === "string") return { ...result, content: `${content}\n\n${text}` }
  return { ...result, content: text }
}

export default {
  id: "itmo.check-after-edit",
  async setup(ctx) {
    const root = findRoot(ctx)

    await ctx.tool.hook("execute.after", (event) => {
      if (!EDIT_TOOLS.has(event.tool) || event.status !== "completed") return

      const check = runCheck(root)
      const file = event.input?.path ?? event.input?.filePath ?? "?"
      const report =
        `[check-after-edit] ${check.runner} -> ${check.status} (exit ${check.code})\n` + check.tail

      try {
        mkdirSync(path.join(root, "logs"), { recursive: true })
        appendFileSync(
          path.join(root, "logs", "hook-runs.log"),
          `${new Date().toISOString()} ${event.tool} ${file} -> ${check.status}\n`,
        )
      } catch {
        // Лог нужен только как подтверждение; ошибка записи не должна ломать работу агента.
      }

      event.result = appendToResult(event.result, report)
    })
  },
}
