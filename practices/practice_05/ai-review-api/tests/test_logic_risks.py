import json
import unittest

from app.review_service import ReviewService


class JsonLLM:
    def __init__(self, payload: dict):
        self.payload = payload

    def generate(self, prompt: str) -> str:
        return json.dumps(self.payload)


class RiskValidationTest(unittest.TestCase):
    def setUp(self):
        self.diff = (
            "diff --git a/app/x.py b/app/x.py\n"
            "--- a/app/x.py\n"
            "+++ b/app/x.py\n"
            "@@ -0,0 +1,3 @@\n"
            "+print(\"ok\")\n"
            "+API_TOKEN = \"sk-live-abc123def456\"\n"
            "+another = 1\n"
        )

    def test_invalid_file_and_line_and_proof_are_dropped(self):
        llm = JsonLLM(
            {
                "summary": "s",
                "checks": [],
                "risks": [
                    {  # non-existent file
                        "title": "bad file",
                        "evidence": {
                            "type": "diff_line",
                            "file": "app/other.py",
                            "line": 1,
                            "proof": "print(\"ok\")",
                        },
                    },
                    {  # non-existent line
                        "title": "bad line",
                        "evidence": {
                            "type": "diff_line",
                            "file": "app/x.py",
                            "line": 10,
                            "proof": "noop",
                        },
                    },
                    {  # proof not in masked line (original secret)
                        "title": "unmasked proof",
                        "evidence": {
                            "type": "diff_line",
                            "file": "app/x.py",
                            "line": 2,
                            "proof": "API_TOKEN = \"sk-live-abc123def456\"",
                        },
                    },
                ],
            }
        )
        res = ReviewService(llm).review(self.diff)
        self.assertEqual(res["risks"], [])

    def test_valid_diff_line_and_rule_are_kept_and_cap_to_three(self):
        # Build 4 valid risks: expect only 3 preserved in model order
        risks = [
            {
                "title": "valid diff 1",
                "evidence": {
                    "type": "diff_line",
                    "file": "app/x.py",
                    "line": 1,
                    "proof": "print(\"ok\")",
                },
            },
            {
                "title": "valid diff 2",
                "evidence": {
                    "type": "diff_line",
                    "file": "app/x.py",
                    "line": 3,
                    "proof": "another = 1",
                },
            },
            {
                "title": "rule ok",
                "evidence": {"type": "rule", "rule": "OBS-1"},
            },
            {
                "title": "unknown rule",
                "evidence": {"type": "rule", "rule": "FOO-BAR"},
            },
        ]
        llm = JsonLLM({"summary": "s", "checks": [], "risks": risks})
        res = ReviewService(llm).review(self.diff)
        kept = res["risks"]
        # unknown rule must be dropped; two diff_line + one rule kept; cap at 3
        self.assertEqual(len(kept), 3)
        self.assertEqual([r["title"] for r in kept], ["valid diff 1", "valid diff 2", "rule ok"])


if __name__ == "__main__":
    unittest.main()
