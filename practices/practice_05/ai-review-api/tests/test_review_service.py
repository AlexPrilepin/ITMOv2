import unittest

from app.review_service import ReviewService


class RecordingLLM:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "looks fine"


class ReviewServiceTest(unittest.TestCase):
    def test_review_passes_masked_diff_to_llm_and_returns_structured(self):
        llm = RecordingLLM()
        result = ReviewService(llm).review("diff --git a/x b/x")
        # Structured response per contract
        self.assertIn("summary", result)
        self.assertIn("risks", result)
        self.assertIn("checks", result)
        self.assertIn("secrets_masked", result)
        self.assertEqual(len(llm.prompts), 1)
        # Prompt includes masked diff (no secrets in this case, but diff header present)
        self.assertIn("diff --git a/x b/x", llm.prompts[0])


if __name__ == "__main__":
    unittest.main()
