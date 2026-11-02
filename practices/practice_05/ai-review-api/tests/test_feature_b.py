"""Фича B: контролируемая обработка ошибок зависимости LLM (REL-1).

Контракт: docs/requirements.md, раздел "Фича B" и согласованное решение в
openspec/changes/llm-dependency-errors/*.

Тесты пишутся по TDD: сначала красные тесты (эти), затем реализация.
"""

import time
import unittest

from fastapi.testclient import TestClient

from app import api as api_module
from app.api import app


SMALL_DIFF = "diff --git a/app/x.py b/app/x.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n"


class SlowLLM:
    def __init__(self, sleep_seconds: float = 2.0, result: str = "slow"):
        self.sleep_seconds = sleep_seconds
        self.result = result

    def generate(self, prompt: str) -> str:
        time.sleep(self.sleep_seconds)
        return self.result


class RaisingLLM:
    def __init__(self, exc: Exception | None = None):
        self.exc = exc or ValueError("boom")
        self.calls = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        raise self.exc


class FeatureBReliabilityTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_llm_timeout_returns_504_quickly(self):
        # LLM спит 2 секунды; ожидаем 504 быстрее 1 секунды при timeout=0.1
        slow = SlowLLM(sleep_seconds=2.0)
        original_llm = api_module.review_service.llm
        # Попробуем задать малый timeout атрибутом сервиса (будет использован реализацией)
        had_timeout_attr = hasattr(api_module.review_service, "timeout")
        original_timeout = getattr(api_module.review_service, "timeout", None)
        api_module.review_service.llm = slow
        try:
            api_module.review_service.timeout = 0.1  # используется после реализации; сейчас тест красный
            start = time.monotonic()
            response = self.client.post("/api/reviews", json={"diff": SMALL_DIFF})
            duration = time.monotonic() - start
            self.assertEqual(response.status_code, 504)
            self.assertLess(duration, 1.0)
            self.assertEqual(response.json(), {"error": "llm_timeout"})
        finally:
            api_module.review_service.llm = original_llm
            if had_timeout_attr:
                api_module.review_service.timeout = original_timeout
            else:
                if hasattr(api_module.review_service, "timeout"):
                    delattr(api_module.review_service, "timeout")

    def test_llm_other_exception_returns_502(self):
        broken = RaisingLLM(exc=RuntimeError("llm broke"))
        original_llm = api_module.review_service.llm
        api_module.review_service.llm = broken
        try:
            response = self.client.post("/api/reviews", json={"diff": SMALL_DIFF})
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json(), {"error": "llm_unavailable"})
        finally:
            api_module.review_service.llm = original_llm

    def test_success_within_timeout_returns_200_comment(self):
        fast = SlowLLM(sleep_seconds=0.0, result="ok")
        original_llm = api_module.review_service.llm
        api_module.review_service.llm = fast
        try:
            response = self.client.post("/api/reviews", json={"diff": SMALL_DIFF})
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertIn("comment", body)
        finally:
            api_module.review_service.llm = original_llm

    def test_invalid_input_bypasses_llm_even_if_broken(self):
        broken = RaisingLLM()
        original_llm = api_module.review_service.llm
        api_module.review_service.llm = broken
        try:
            response = self.client.post("/api/reviews", json={"diff": "   "})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), {"error": "diff is empty"})
            # LLM не должен вызываться
            self.assertEqual(broken.calls, [])
        finally:
            api_module.review_service.llm = original_llm


if __name__ == "__main__":
    unittest.main()
