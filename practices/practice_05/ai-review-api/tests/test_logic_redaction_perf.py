"""SEC-1 + API-1: маскирование не должно становиться узким местом (ReDoS).

Ревью (независимый проверяющий): регулярки присваиваний с `[A-Za-z0-9_]*?(...)[A-Za-z0-9_]*`
давали кубический перебор — строка из 20 000 символов (ровно лимит API-1) обрабатывалась > 60 с,
до вызова LLM, то есть timeout REL-1 не защищал.
"""
import time
import unittest

from fastapi.testclient import TestClient

from app import api as api_module
from app.api import app
from app.redaction import extract_secret_values, redact_diff

LIMIT = 20000
BUDGET_SECONDS = 1.0


class RedactionPerformanceTest(unittest.TestCase):
    def assert_fast(self, func, text):
        start = time.perf_counter()
        func(text)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, BUDGET_SECONDS, f"{func.__name__} took {elapsed:.2f}s on {len(text)} chars")

    def test_long_identifier_line_is_linear(self):
        for line in ("+" + "a_" * (LIMIT // 2 - 1), "+" + "x" * (LIMIT - 1), "+" + "secret_" * (LIMIT // 7 - 1)):
            with self.subTest(sample=line[:12]):
                self.assert_fast(redact_diff, line)
                self.assert_fast(extract_secret_values, line)

    def test_api_exact_limit_request_is_fast(self):
        class EchoLLM:
            def generate(self, prompt):
                return "{}"

        original = api_module.review_service.llm
        api_module.review_service.llm = EchoLLM()
        try:
            client = TestClient(app)
            start = time.perf_counter()
            response = client.post("/api/reviews", json={"diff": "+" + "a_" * (LIMIT // 2 - 1) + "b"})
            elapsed = time.perf_counter() - start
        finally:
            api_module.review_service.llm = original
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 2 * BUDGET_SECONDS)


if __name__ == "__main__":
    unittest.main()
