import unittest

from fastapi.testclient import TestClient

from app.api import app

SMALL_DIFF = "diff --git a/app/x.py b/app/x.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n"


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_review_returns_structured_response(self):
        response = self.client.post("/api/reviews", json={"diff": SMALL_DIFF})
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


if __name__ == "__main__":
    unittest.main()
