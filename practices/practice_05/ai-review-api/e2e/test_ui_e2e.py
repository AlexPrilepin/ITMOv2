"""Сквозные проверки UI ↔ логика в настоящем браузере (specs/001-review-ui/quickstart.md).

Не входит в `sh scripts/check.sh` (нужен Playwright с Chromium). Запуск из папки проекта:

    pip install playwright && python -m playwright install chromium
    python e2e/test_ui_e2e.py

Скрипт сам поднимает сервис (uvicorn в фоновом потоке), подменяет LLM для сценариев 502/504
и пишет отчёт и скриншоты в docs/sdd/speckit/e2e/.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from app import api as api_module  # noqa: E402
from app.dependencies import StubLLM  # noqa: E402

OUT = ROOT / "docs" / "sdd" / "speckit" / "e2e"
PORT = 8077
BASE = f"http://127.0.0.1:{PORT}"
SECRET = "sk-live-abc123def456"
DIFF_WITH_SECRET = (
    "diff --git a/app/config.py b/app/config.py\n"
    "--- a/app/config.py\n+++ b/app/config.py\n"
    "@@ -10,3 +10,4 @@ class Config:\n"
    "     DEBUG = False\n"
    "-    TIMEOUT = 5\n"
    "+    TIMEOUT = 50\n"
    f'+    API_TOKEN = "{SECRET}"\n'
    '     NAME = "svc"\n'
)
CLEAN_DIFF = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n"

service = api_module.review_service
results: list[dict] = []


class ScriptedLLM:
    """LLM для сценариев: отдаёт заранее заданный JSON, может спать или падать."""

    def __init__(self, answer: dict | None = None, sleep: float = 0.0, fail: bool = False):
        self.answer, self.sleep, self.fail = answer, sleep, fail

    def generate(self, prompt: str) -> str:
        if self.sleep:
            time.sleep(self.sleep)
        if self.fail:
            raise RuntimeError("llm is down")
        return json.dumps(self.answer)


def use_llm(llm, timeout: float = 10.0) -> None:
    service.llm, service.timeout = llm, timeout


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append({"scenario": name, "passed": bool(condition), "detail": detail})
    print(("PASS " if condition else "FAIL ") + name + (f" — {detail}" if detail else ""))


def fulfill_with(status: int, body: dict):
    def handler(route, request=None):
        route.fulfill(status=status, content_type="application/json", body=json.dumps(body))
    return handler


def start_server() -> uvicorn.Server:
    server = uvicorn.Server(uvicorn.Config(api_module.app, host="127.0.0.1", port=PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started:
            return server
        time.sleep(0.05)
    raise RuntimeError("server did not start")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    server = start_server()
    console: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.on("console", lambda msg: console.append(msg.text))
        requests: list[str] = []
        page.on("request", lambda req: requests.append(req.url) if req.url.endswith("/api/reviews") else None)

        # 1. Загрузка страницы (idle)
        page.goto(BASE + "/")
        check("idle: элементы, счётчик 0/20000, кнопка неактивна",
              page.locator("#counter").inner_text() == "0/20000" and page.locator("#submit").is_disabled()
              and page.locator("#form").get_attribute("data-state") == "idle")
        page.screenshot(path=str(OUT / "01-idle.png"), full_page=True)

        # 2. Успех с секретом через настоящую логику и StubLLM (P1, SEC-1, D3, D7)
        use_llm(StubLLM())
        page.fill("#diff", DIFF_WITH_SECRET)
        page.click("#submit")
        page.wait_for_selector("#result:not([hidden])")
        text = page.locator("#result").inner_text()
        check("успех: summary, риски, проверки", "Краткое описание изменения" in text and "Проверки" in text)
        check("SEC-1/D3: отметка о маскировании при secrets_masked > 0", "Секреты в diff были замаскированы" in text)
        check("SEC-1: риск по правилу SEC-1 показан меткой", page.locator(".rule", has_text="SEC-1").count() == 1)
        check("D7: исходного секрета нет на странице", SECRET not in page.content())
        page.screenshot(path=str(OUT / "02-success-secret.png"), full_page=True)

        # 3. Риск diff_line (D1, D5): file:line и proof из замаскированного diff
        use_llm(ScriptedLLM({
            "summary": "Таймаут увеличен в 10 раз, токен вынесен в конфиг.",
            "risks": [
                {"title": "Таймаут 50 с может подвесить воркеры",
                 "evidence": {"type": "diff_line", "file": "app/config.py", "line": 11, "proof": "TIMEOUT = 50"}},
                {"title": "Токен в коде", "evidence": {"type": "diff_line", "file": "app/config.py", "line": 12,
                                                      "proof": "API_TOKEN = [SECRET]"}},
                {"title": "Выдуманный риск", "evidence": {"type": "diff_line", "file": "app/other.py", "line": 3,
                                                         "proof": "nothing"}},
                {"title": "<img src=x onerror=alert(1)>", "evidence": {"type": "rule", "rule": "QA-1"}},
            ],
            "checks": ["Проверить значение TIMEOUT под нагрузкой", "Перенести токен в секреты окружения"],
        }))
        page.click("#submit")
        page.wait_for_selector("#result:not([hidden])")
        where = page.locator(".where").all_inner_texts()
        check("D1/D5: diff_line показан как file:line", where == ["app/config.py:11", "app/config.py:12"], str(where))
        check("QA-1: неподтверждённый риск не показан", "Выдуманный риск" not in page.locator("#result").inner_text())
        check("XSS: HTML из ответа модели выводится текстом",
              page.locator("#result img").count() == 0 and "<img src=x onerror=alert(1)>" in page.locator("#result").inner_text())
        check("checks: список строк", page.locator("#result li").count() == 2)
        page.screenshot(path=str(OUT / "03-success-diff-line.png"), full_page=True)

        # 4. Ошибки от настоящего сервиса: 502 и 504 (REL-1)
        use_llm(ScriptedLLM(fail=True))
        page.fill("#diff", CLEAN_DIFF)
        page.click("#submit")
        page.wait_for_selector("#error:not([hidden])")
        err = page.locator("#error").inner_text()
        check("502: сообщение и подсказка о ручном ревью", "LLM недоступен" in err and "ручную проверку" in err, err)
        page.screenshot(path=str(OUT / "04-error-502.png"), full_page=True)

        use_llm(ScriptedLLM({"summary": "late"}, sleep=1.0), timeout=0.2)
        page.click("#submit")
        page.wait_for_selector("#error:not([hidden])")
        err = page.locator("#error").inner_text()
        check("504: сообщение и подсказка о ручном ревью", "LLM не ответил вовремя" in err and "ручную проверку" in err, err)

        # 5. Ошибки, до которых UI не пускает (400/413/422), сеть и 500 — подменой ответа
        for status, body, expected in (
            (400, {"error": "diff is empty"}, "Пустой diff"),
            (413, {"error": "diff too large", "limit": 20000}, "Слишком большой diff"),
            (422, {"error": "diff is required"}, "Неверный запрос"),
            (500, {"error": "boom"}, "Внутренняя ошибка сервиса"),
        ):
            page.route("**/api/reviews", fulfill_with(status, body))
            page.click("#submit")
            page.wait_for_selector("#error:not([hidden])")
            got = page.locator("#error").inner_text()
            check(f"{status}: сообщение по HTTP-статусу", expected in got, got)
            page.unroute("**/api/reviews")
        page.route("**/api/reviews", lambda route: route.abort())
        page.click("#submit")
        page.wait_for_selector("#error:not([hidden])")
        check("сеть: сообщение о сетевой ошибке", "Сетевая ошибка" in page.locator("#error").inner_text())
        page.unroute("**/api/reviews")

        # 6. Блокировка повторной отправки (loading)
        use_llm(ScriptedLLM({"summary": "ok", "risks": [], "checks": []}, sleep=0.8))
        before = len(requests)
        page.click("#submit")
        state = page.locator("#form").get_attribute("data-state")
        disabled = page.locator("#submit").is_disabled()
        page.locator("#submit").click(force=True)
        page.locator("#form").dispatch_event("submit")
        page.wait_for_selector("#result:not([hidden])")
        check("loading: кнопка заблокирована, ровно один запрос",
              state == "loading" and disabled and len(requests) - before == 1,
              f"state={state}, disabled={disabled}, requests={len(requests) - before}")

        # 7. Лимит 20 000 на клиенте
        page.fill("#diff", "+" + "x" * 19999)
        at_limit = (page.locator("#counter").inner_text(), page.locator("#submit").is_enabled())
        page.fill("#diff", "+" + "x" * 20000)
        over = (page.locator("#counter").inner_text(), page.locator("#submit").is_disabled(),
                page.locator("#limit-warning").is_visible())
        check("лимит: 20000 — можно отправить, 20001 — нельзя и есть предупреждение",
              at_limit == ("20000/20000", True) and over == ("20001/20000", True, True), f"{at_limit} {over}")
        page.screenshot(path=str(OUT / "05-limit.png"), full_page=True)

        # 8. Пустой и пробельный ввод
        page.fill("#diff", "   \n  ")
        check("пробелы: кнопка неактивна", page.locator("#submit").is_disabled())

        # 9. Очистить
        use_llm(StubLLM())
        page.fill("#diff", CLEAN_DIFF)
        page.click("#submit")
        page.wait_for_selector("#result:not([hidden])")
        page.click("#clear")
        check("очистить: поле пустое, 0/20000, результат скрыт, idle",
              page.locator("#diff").input_value() == "" and page.locator("#counter").inner_text() == "0/20000"
              and page.locator("#result").is_hidden() and page.locator("#form").get_attribute("data-state") == "idle")

        # 10. Приватность: нет хранения и логов
        storage = page.evaluate("() => [localStorage.length, sessionStorage.length]")
        check("приватность: localStorage и sessionStorage пусты", storage == [0, 0], str(storage))
        # Chromium сам пишет «Failed to load resource: <код>» на ответы с ошибкой — это не данные.
        # Требование FR-009/SC-006: в консоли нет diff, секретов и содержимого ответов.
        leaked = [m for m in console if any(s in m for s in (SECRET, "diff --git", "TIMEOUT", "Учебная заглушка",
                                                            "Таймаут", "[SECRET]"))]
        own = [m for m in console if not m.startswith("Failed to load resource")]
        check("приватность: в консоли нет diff, секретов и ответов; страница ничего не пишет",
              leaked == [] and own == [], f"сообщений браузера о статусах: {len(console) - len(own)}")

        browser.close()
    server.should_exit = True
    passed = sum(r["passed"] for r in results)
    (OUT / "e2e-report.json").write_text(json.dumps(
        {"passed": passed, "total": len(results), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
