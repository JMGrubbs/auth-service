import unittest

from services.login_rate_limit import LoginRateLimitError, LoginRateLimiter


class MemoryRateLimitRedis:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    async def eval(self, _script: str, _key_count: int, key: str, ttl: int) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        self.ttls[key] = ttl
        return self.values[key]


class LoginRateLimiterTests(unittest.IsolatedAsyncioTestCase):
    async def test_limits_repeated_attempts_for_an_email_without_storing_pii(self) -> None:
        redis = MemoryRateLimitRedis()
        limiter = LoginRateLimiter(redis, window_seconds=300, email_limit=2, ip_limit=20)

        await limiter.check(ip_address="203.0.113.8", email="User@Example.com")
        await limiter.check(ip_address="203.0.113.8", email="user@example.com")
        with self.assertRaises(LoginRateLimitError):
            await limiter.check(ip_address="203.0.113.8", email="user@example.com")

        self.assertTrue(all("user@example.com" not in key for key in redis.values))
        self.assertTrue(all(ttl == 300 for ttl in redis.ttls.values()))

    async def test_limits_attempts_across_accounts_from_one_ip(self) -> None:
        redis = MemoryRateLimitRedis()
        limiter = LoginRateLimiter(redis, window_seconds=60, email_limit=20, ip_limit=2)

        await limiter.check(ip_address="203.0.113.9", email="one@example.com")
        await limiter.check(ip_address="203.0.113.9", email="two@example.com")
        with self.assertRaises(LoginRateLimitError):
            await limiter.check(ip_address="203.0.113.9", email="three@example.com")


if __name__ == "__main__":
    unittest.main()
