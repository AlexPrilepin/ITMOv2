"""Команда UI (specs/001-review-ui): GET / отдаёт страницу помощника ревьюера.

Серверная часть приёмки; поведение в браузере проверяется сквозными сценариями
(specs/001-review-ui/quickstart.md, docs/sdd/speckit/e2e/).
"""
import re
import unittest

from fastapi.testclient import TestClient

from app.api import app


class UiPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.response = TestClient(app).get("/")
        cls.html = cls.response.text

    def test_root_serves_html(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.headers["content-type"], "text/html; charset=utf-8")

    def test_page_has_required_elements(self):
        for pattern in (
            r'<textarea[^>]*id="diff"',
            r'<span[^>]*id="counter"[^>]*>0/20000</span>',
            r'<button[^>]*id="submit"[^>]*>Получить ревью</button>',
            r'<button[^>]*id="clear"[^>]*>Очистить</button>',
            r'<div[^>]*id="result"',
            r'<div[^>]*id="error"',
        ):
            with self.subTest(pattern=pattern):
                self.assertRegex(self.html, pattern)

    def test_page_calls_reviews_api(self):
        self.assertIn('fetch("/api/reviews"', self.html)

    def test_error_messages_follow_contract(self):
        for text in (
            "Пустой diff. Вставьте содержимое diff и повторите попытку.",
            "Слишком большой diff. Лимит — 20 000 символов.",
            "Неверный запрос. Проверьте формат diff.",
            "LLM недоступен. Попробуйте позже или продолжайте ревью вручную.",
            "LLM не ответил вовремя. Попробуйте ещё раз или продолжайте ревью вручную.",
            "Сетевая ошибка. Проверьте соединение и попробуйте ещё раз.",
            "Внутренняя ошибка сервиса. Попробуйте позже.",
            "Секреты в diff были замаскированы",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.html)

    def test_page_does_not_store_or_inject_data(self):
        # SEC-1 / OBS-1 / XSS: данные API только через textContent, без хранения и логов.
        for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write",
                          "localStorage", "sessionStorage", "console."):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.html)

    def test_page_has_no_external_resources(self):
        # Конституция V: без библиотек и сборщиков — ничего не грузим со сторонних адресов.
        self.assertIsNone(re.search(r'(src|href)="https?://', self.html))

    def test_reviews_api_unchanged(self):
        response = TestClient(app).post("/api/reviews", json={"diff": "  "})
        self.assertEqual((response.status_code, response.json()), (400, {"error": "diff is empty"}))


if __name__ == "__main__":
    unittest.main()
