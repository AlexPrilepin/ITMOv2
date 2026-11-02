import unittest

from app.review_service import ReviewService


class RecordingLLM:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "looks fine"


class ReviewServiceTest(unittest.TestCase):
    def test_review_passes_diff_to_llm_and_returns_comment(self):
        llm = RecordingLLM()
        result = ReviewService(llm).review("diff --git a/x b/x")
        self.assertEqual(result, {"comment": "looks fine"})
        self.assertEqual(len(llm.prompts), 1)
        self.assertIn("diff --git a/x b/x", llm.prompts[0])


if __name__ == "__main__":
    unittest.main()
