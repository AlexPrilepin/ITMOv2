import json
import unittest

from app.review_service import ReviewService


class JsonLLM:
    def __init__(self, payload: dict):
        self.payload = payload

    def generate(self, prompt: str) -> str:
        return json.dumps(self.payload)


class ProofMaskingTest(unittest.TestCase):
    def test_unmasked_proof_is_rejected_and_masked_proof_is_kept(self):
        diff = (
            "diff --git a/app/x.py b/app/x.py\n"
            "--- a/app/x.py\n"
            "+++ b/app/x.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+API_TOKEN = \"sk-live-abc123def456\"\n"
            "+print(\"ok\")\n"
        )

        # First, LLM proposes risk with unmasked proof: should be dropped
        llm_bad = JsonLLM(
            {
                "summary": "s",
                "checks": [],
                "risks": [
                    {
                        "title": "secret leaks",
                        "evidence": {
                            "type": "diff_line",
                            "file": "app/x.py",
                            "line": 1,
                            "proof": "API_TOKEN = \"sk-live-abc123def456\"",
                        },
                    }
                ],
            }
        )
        res_bad = ReviewService(llm_bad).review(diff)
        self.assertEqual(res_bad["risks"], [])
        self.assertGreaterEqual(res_bad["secrets_masked"], 1)
        self.assertNotIn("sk-live-abc123def456", json.dumps(res_bad))

        # Then with masked proof: should be kept
        llm_ok = JsonLLM(
            {
                "summary": "s",
                "checks": [],
                "risks": [
                    {
                        "title": "secret masked",
                        "evidence": {
                            "type": "diff_line",
                            "file": "app/x.py",
                            "line": 1,
                            "proof": "API_TOKEN = [SECRET]",
                        },
                    }
                ],
            }
        )
        res_ok = ReviewService(llm_ok).review(diff)
        self.assertEqual(len(res_ok["risks"]), 1)
        self.assertEqual(res_ok["risks"][0]["title"], "secret masked")
        self.assertEqual(res_ok["risks"][0]["evidence"]["proof"], "API_TOKEN = [SECRET]")

    def test_secret_in_title_summary_checks_is_sanitized(self):
        diff = (
            "diff --git a/app/x.py b/app/x.py\n"
            "--- a/app/x.py\n"
            "+++ b/app/x.py\n"
            "@@ -0,0 +1,1 @@\n"
            "+API_TOKEN = \"sk-live-abc123def456\"\n"
        )
        llm = JsonLLM(
            {
                "summary": "found secret sk-live-abc123def456",
                "checks": [
                    "check token sk-live-abc123def456",
                ],
                "risks": [
                    {
                        "title": "secret in title sk-live-abc123def456",
                        "evidence": {"type": "rule", "rule": "SEC-1"},
                    }
                ],
            }
        )
        res = ReviewService(llm).review(diff)
        doc = json.dumps(res)
        self.assertNotIn("sk-live-abc123def456", doc)
        self.assertIn("[SECRET]", res["summary"])
        self.assertTrue(all("[SECRET]" in c for c in res["checks"]))
        self.assertIn("[SECRET]", res["risks"][0]["title"])


if __name__ == "__main__":
    unittest.main()
