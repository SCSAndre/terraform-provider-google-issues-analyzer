"""Tests for secrets provider backends and fallback behavior."""

import os
import unittest
from unittest.mock import patch

from secrets_provider import clear_secret_cache, get_secret


class TestSecretsProvider(unittest.TestCase):
    """Validate non-breaking env defaults and backend fallback behavior."""

    def tearDown(self):
        clear_secret_cache()

    def test_env_backend_reads_environment(self):
        with patch.dict(os.environ, {"SECRET_BACKEND": "env", "MY_SECRET": "abc123"}, clear=False):
            clear_secret_cache()
            self.assertEqual(get_secret("MY_SECRET"), "abc123")

    def test_unknown_backend_falls_back_to_env(self):
        with patch.dict(
            os.environ,
            {"SECRET_BACKEND": "unknown", "MY_SECRET": "fallback-value"},
            clear=False,
        ):
            clear_secret_cache()
            self.assertEqual(get_secret("MY_SECRET"), "fallback-value")

    def test_gcp_backend_without_project_id_falls_back_to_env(self):
        with patch.dict(
            os.environ,
            {
                "SECRET_BACKEND": "gcp",
                "GCP_PROJECT_ID": "",
                "MY_SECRET": "env-value",
            },
            clear=False,
        ):
            clear_secret_cache()
            self.assertEqual(get_secret("MY_SECRET"), "env-value")

    def test_backend_fallback_can_be_disabled(self):
        with patch.dict(
            os.environ,
            {
                "SECRET_BACKEND": "gcp",
                "GCP_PROJECT_ID": "",
                "SECRET_FALLBACK_TO_ENV": "false",
                "MY_SECRET": "env-value",
            },
            clear=False,
        ):
            clear_secret_cache()
            self.assertIsNone(get_secret("MY_SECRET"))


if __name__ == "__main__":
    unittest.main()

