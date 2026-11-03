"""R5: учебная заглушка LLM отдаёт детерминированный JSON по specs/review-api-contract.md,
чтобы UI и сквозные проверки работали без внешней модели."""
import json
import unittest

from fastapi.testclient import TestClient

from app.api import app
from app.dependencies import StubLLM

SECRET_DIFF = (
    "diff --git a/app/config.py b/app/config.py\n--- a/app/config.py\n+++ b/app/config.py\n"
    "@@ -1,1 +1,2 @@\n DEBUG = False\n+API_TOKEN = \"sk-live-abc123def456\"\n"
)
CLEAN_DIFF = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n"


class StubLLMContractTest(unittest.TestCase):
    def test_stub_returns_contract_json_deterministically(self):
        stub = StubLLM()
        first = stub.generate("prompt " + CLEAN_DIFF)
        self.assertEqual(first, stub.generate("prompt " + CLEAN_DIFF))
        data = json.loads(first)
        self.assertIsInstance(data["summary"], str)
        self.assertTrue(data["summary"])
        self.assertIsInstance(data["risks"], list)
        self.assertIsInstance(data["checks"], list)
        self.assertTrue(all(isinstance(c, str) for c in data["checks"]))

    def test_api_with_stub_shows_rule_risk_for_masked_secret(self):
        response = TestClient(app).post("/api/reviews", json={"diff": SECRET_DIFF})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(body["secrets_masked"], 1)
        self.assertIn({"type": "rule", "rule": "SEC-1"}, [r["evidence"] for r in body["risks"]])
        self.assertTrue(body["checks"])
        self.assertNotIn("sk-live-abc123def456", response.text)

    def test_api_with_stub_clean_diff_has_no_secret_risk(self):
        body = TestClient(app).post("/api/reviews", json={"diff": CLEAN_DIFF}).json()
        self.assertEqual(body["secrets_masked"], 0)
        self.assertNotIn("SEC-1", [r["evidence"].get("rule") for r in body["risks"]])
        self.assertTrue(body["checks"])


if __name__ == "__main__":
    unittest.main()
