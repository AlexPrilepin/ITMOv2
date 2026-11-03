import unittest

from app.review_service import ReviewService


class RecordingLLM:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "{}"  # minimal JSON to pass parsing


class PromptMaskingTest(unittest.TestCase):
    def test_prompt_contains_secret_markers_not_raw_values(self):
        llm = RecordingLLM()
        diff = (
            "diff --git a/app/x.py b/app/x.py\n"
            "--- a/app/x.py\n"
            "+++ b/app/x.py\n"
            "@@ -0,0 +1,5 @@\n"
            "+-----BEGIN PRIVATE KEY-----\n"
            "+MIIEvQIBADANBgkqh...\n"
            "+-----END PRIVATE KEY-----\n"
            "+password = \"supersecret\"\n"
            "+API_TOKEN = \"sk-live-abc123def456\"\n"
            "+Authorization: Bearer ABCDEFGHIJKLMNOPQRST\n"
        )
        ReviewService(llm).review(diff)
        self.assertEqual(len(llm.prompts), 1)
        prompt = llm.prompts[0]
        self.assertIn("[SECRET]", prompt)
        self.assertNotIn("MIIEvQIBADANBgkqh...", prompt)
        self.assertNotIn("supersecret", prompt)
        self.assertNotIn("sk-live-abc123def456", prompt)
        self.assertNotIn("Bearer ABCDEFGHIJKLMNOPQRST", prompt)


if __name__ == "__main__":
    unittest.main()
