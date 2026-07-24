import unittest

from fastapi.testclient import TestClient

from cache.dependencies import get_redis
from main import app


class BrowserCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides[get_redis] = lambda: object()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_legacy_delete_preflights_are_allowed(self) -> None:
        response = self.client.options(
            "/api/v1/users/delete",
            headers={
                "Origin": "https://legacy-app.example",
                "Access-Control-Request-Method": "DELETE",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("DELETE", response.headers["access-control-allow-methods"])

    def test_invalid_oauth_requests_are_not_cacheable(self) -> None:
        response = self.client.post("/api/v1/oauth/token", json={})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["pragma"], "no-cache")


if __name__ == "__main__":
    unittest.main()
