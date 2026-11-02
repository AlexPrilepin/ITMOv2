import unittest

from mcp_server.diff_tools import DIFF_LIMIT, DiffInputError, analyze_diff

CLEAN_DIFF = "diff --git a/app/x.py b/app/x.py\n@@ -1 +1 @@\n-a = 1\n+a = 2\n"


class AnalyzeDiffTest(unittest.TestCase):
    def test_clean_diff_within_limit(self):
        result = analyze_diff(CLEAN_DIFF)
        self.assertTrue(result["within_limit"])
        self.assertEqual(result["expected_http_status"], 200)
        self.assertEqual(result["secrets_found"], [])
        self.assertTrue(result["safe_to_send_to_llm"])

    def test_oversized_diff_maps_to_413(self):
        big = CLEAN_DIFF + "+" + "x" * DIFF_LIMIT + "\n"
        result = analyze_diff(big)
        self.assertFalse(result["within_limit"])
        self.assertEqual(result["expected_http_status"], 413)

    def test_exact_limit_is_allowed(self):
        padded = CLEAN_DIFF + "+" + "x" * (DIFF_LIMIT - len(CLEAN_DIFF) - 1)
        self.assertEqual(len(padded), DIFF_LIMIT)
        self.assertTrue(analyze_diff(padded)["within_limit"])

    def test_secret_is_found_and_redacted(self):
        diff = CLEAN_DIFF + '+API_KEY = "sk-test-1234567890"\n'
        result = analyze_diff(diff)
        self.assertEqual(result["secrets_found"], [{"line": 5, "kind": "assignment"}])
        self.assertFalse(result["safe_to_send_to_llm"])
        self.assertIn("[REDACTED]", result["redacted_diff"])
        self.assertNotIn("sk-test-1234567890", result["redacted_diff"])

    def test_empty_input_is_an_error(self):
        with self.assertRaises(DiffInputError):
            analyze_diff("   ")

    def test_non_diff_text_is_an_error(self):
        with self.assertRaises(DiffInputError):
            analyze_diff("please review my code")

    def test_non_string_is_an_error(self):
        with self.assertRaises(DiffInputError):
            analyze_diff(None)


if __name__ == "__main__":
    unittest.main()
