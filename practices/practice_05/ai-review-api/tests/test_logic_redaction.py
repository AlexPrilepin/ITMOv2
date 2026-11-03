import unittest

from app.redaction import redact_diff


class RedactionLogicTest(unittest.TestCase):
    def test_masks_pem_and_assignments_and_tokens(self):
        diff = (
            "diff --git a/secrets.pem b/secrets.pem\n"
            "--- a/secrets.pem\n"
            "+++ b/secrets.pem\n"
            "@@ -0,0 +1,8 @@\n"
            "+-----BEGIN PRIVATE KEY-----\n"
            "+MIIEvQIBADANBgkqh...\n"
            "+-----END PRIVATE KEY-----\n"
            "+password = \"supersecret\"\n"
            "+API_TOKEN = \"sk-live-abc123def456\"\n"
            "+aws_key = AKIA1234567890ABCD\n"
            "+Authorization: Bearer abcdefghijklmnopQRST\n"
            "+print(\"ok\")\n"
        )

        masked, count = redact_diff(diff)

        # PEM body line should not appear verbatim in masked diff
        self.assertNotIn("MIIEvQIBADANBgkqh...", masked)
        # BEGIN/END markers may remain, but body should be masked
        self.assertIn("-----BEGIN PRIVATE KEY-----", masked)
        self.assertIn("-----END PRIVATE KEY-----", masked)

        # Assignments and tokens are masked with [SECRET], keys/labels preserved
        self.assertIn("password = [SECRET]", masked)
        self.assertIn("API_TOKEN = [SECRET]", masked)
        # AWS Access Key ID masked; label remains (left-hand side)
        self.assertIn("aws_key = ", masked)
        self.assertIn("[SECRET]", masked)
        self.assertNotIn("supersecret", masked)
        self.assertNotIn("sk-live-abc123def456", masked)
        self.assertNotIn("AKIA1234567890ABCD", masked)
        self.assertNotIn("Bearer abcdefghijklmnopQRST", masked)

        # Non-secret code stays unchanged
        self.assertIn("print(\"ok\")", masked)

        # secrets_masked is the count of replacements; must be >= 4 here
        self.assertGreaterEqual(count, 4)

    def test_masks_additional_secret_patterns_and_preserves_normal_code(self):
        diff = (
            "diff --git a/app/settings.py b/app/settings.py\n"
            "--- a/app/settings.py\n"
            "+++ b/app/settings.py\n"
            "@@ -0,0 +1,12 @@\n"
            "+DB_PASSWORD=Sup3rS3cretPwd\n"
            "+SECRET_KEY = \"django-insecure-abc123xyz789\"\n"
            "+AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
            "+  \"password\": \"hunter2hunter2\",\n"
            "+headers = {\"Authorization\": \"Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig\"}\n"
            "+KEY = \"\"\"-----BEGIN RSA PRIVATE KEY-----\n"
            "+MIIEvQIBADANBgkqh...\n"
            "+-----END RSA PRIVATE KEY-----\n"
            "+def tokenize(text):\n"
            "+    return text.split()\n"
        )

        masked, count = redact_diff(diff)

        self.assertIn("DB_PASSWORD=[SECRET]", masked)
        self.assertIn("SECRET_KEY = [SECRET]", masked)
        self.assertNotIn("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", masked)
        self.assertIn("AWS_SECRET_ACCESS_KEY=[SECRET]", masked)
        self.assertIn("\"password\": [SECRET]", masked)
        self.assertIn("Bearer [SECRET]", masked)
        # PEM marker anywhere in the line is recognized; body masked
        self.assertIn("-----BEGIN RSA PRIVATE KEY-----", masked)
        self.assertNotIn("MIIEvQIBADANBgkqh...", masked)
        # Normal code unchanged
        self.assertIn("def tokenize(text):", masked)
        self.assertIn("return text.split()", masked)


if __name__ == "__main__":
    unittest.main()
