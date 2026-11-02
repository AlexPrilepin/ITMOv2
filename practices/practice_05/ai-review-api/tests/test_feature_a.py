"""Фича A: входная валидация POST /api/reviews (API-1).

Контракт: docs/requirements.md, раздел "Фича A".
Каждый тест называет ломку: какой неверный бранч/константа его уронит.
Ожидания выведены вручную из requirements, а не из кода.
"""
import unittest

from fastapi.testclient import TestClient

from app import api as api_module
from app.api import app

SMALL_DIFF = "diff --git a/app/x.py b/app/x.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n"
# Проверен через MCP check_diff: chars=59, within_limit=true, status 200, секретов нет.
LIMIT = 20000  # из docs/requirements.md: длина больше 20 000 -> 413


def make_exact_diff() -> str:
    # Ровно LIMIT символов, валидный unified diff (тот же заголовок, что SMALL_DIFF).
    return SMALL_DIFF + "+" + "x" * (LIMIT - len(SMALL_DIFF) - 1)


def make_big_diff() -> str:
    # Больше LIMIT символов, валидный unified diff.
    return SMALL_DIFF + "+" + "x" * LIMIT + "\n"


class SpyLLM:
    def __init__(self):
        self.calls = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        return "spy review"


class FeatureAValidationTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_missing_diff_returns_422_with_error(self):
        # Ломка: доступ к payload["diff"] без проверки -> KeyError -> 500 вместо 422.
        response = self.client.post("/api/reviews", json={})
        self.assertEqual(response.status_code, 422)
        self.assertIn("error", response.json())

    def test_non_string_diff_returns_422_with_error(self):
        # Ломка: нет isinstance-проверки -> int уходит в LLM и возвращается 200.
        response = self.client.post("/api/reviews", json={"diff": 123})
        self.assertEqual(response.status_code, 422)
        self.assertIn("error", response.json())

    def test_empty_diff_returns_400(self):
        # Ломка: нет проверки пустоты -> 200 и вызов LLM вместо 400.
        response = self.client.post("/api/reviews", json={"diff": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "diff is empty"})

    def test_whitespace_diff_returns_400(self):
        # Ломка: проверяют `not diff` вместо `not diff.strip()` -> пробелы проходят.
        response = self.client.post("/api/reviews", json={"diff": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "diff is empty"})

    def test_too_large_diff_returns_413(self):
        # Ломка: нет проверки длины или неверная константа -> 200 вместо 413.
        response = self.client.post("/api/reviews", json={"diff": make_big_diff()})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json(), {"error": "diff too large", "limit": 20000})

    def test_exact_limit_diff_is_accepted(self):
        # Ломка: off-by-one `>=` вместо `>` -> ровно 20000 отклоняется с 413.
        diff = make_exact_diff()
        self.assertEqual(len(diff), 20000)
        response = self.client.post("/api/reviews", json={"diff": diff})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        # Contract per specs/review-api-contract.md
        self.assertIn("summary", body)
        self.assertIn("risks", body)
        self.assertIsInstance(body["risks"], list)
        self.assertIn("checks", body)
        self.assertIsInstance(body["checks"], list)
        self.assertIn("secrets_masked", body)
        self.assertIsInstance(body["secrets_masked"], int)

    def test_llm_not_called_when_diff_missing(self):
        # Ломка: валидация после вызова LLM -> spy видит вызов.
        spy = SpyLLM()
        original = api_module.review_service.llm
        api_module.review_service.llm = spy
        try:
            response = self.client.post("/api/reviews", json={})
            self.assertEqual(response.status_code, 422)
            self.assertEqual(spy.calls, [])
        finally:
            api_module.review_service.llm = original

    def test_llm_not_called_when_diff_empty(self):
        spy = SpyLLM()
        original = api_module.review_service.llm
        api_module.review_service.llm = spy
        try:
            response = self.client.post("/api/reviews", json={"diff": ""})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(spy.calls, [])
        finally:
            api_module.review_service.llm = original

    def test_llm_not_called_when_diff_too_large(self):
        spy = SpyLLM()
        original = api_module.review_service.llm
        api_module.review_service.llm = spy
        try:
            response = self.client.post("/api/reviews", json={"diff": make_big_diff()})
            self.assertEqual(response.status_code, 413)
            self.assertEqual(spy.calls, [])
        finally:
            api_module.review_service.llm = original


if __name__ == "__main__":
    unittest.main()
