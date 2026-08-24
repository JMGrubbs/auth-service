"""Regression tests for token secret logging."""

import io
import unittest
from contextlib import redirect_stdout

from core.security import create_access_token, decode_access_token


class TokenLoggingTests(unittest.TestCase):
    def test_token_operations_do_not_write_sensitive_data_to_stdout(self) -> None:
        captured = io.StringIO()

        with redirect_stdout(captured):
            token = create_access_token("logging-regression-test")
            decoded = decode_access_token(token)

        self.assertEqual(decoded["sub"], "logging-regression-test")
        if captured.getvalue():
            self.fail("token operations wrote sensitive data to stdout")


if __name__ == "__main__":
    unittest.main()
