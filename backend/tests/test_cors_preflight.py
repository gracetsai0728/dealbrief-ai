import unittest

from app import create_app


class CorsTestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://localhost:5173"]
    OPENAI_API_KEY = None
    OPENAI_BRIEF_MODEL = "test-model"
    OPENAI_INTELLIGENCE_MODEL = "test-model"


class CorsPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(CorsTestConfig)
        cls.client = cls.app.test_client()

    def assert_post_preflight_allowed(self, path):
        response = self.client.options(
            path,
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:5173",
        )
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Credentials"),
            "true",
        )
        self.assertIn("POST", response.headers.get("Access-Control-Allow-Methods", ""))

    def test_intelligence_refresh_preflight_does_not_require_login(self):
        self.assert_post_preflight_allowed(
            "/api/customers/00000000-0000-0000-0000-000000000000/intelligence/refresh"
        )

    def test_meeting_brief_preflight_does_not_require_login(self):
        self.assert_post_preflight_allowed("/api/generate-brief")

    def test_actual_post_still_requires_login(self):
        response = self.client.post("/api/generate-brief", json={})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json()["error"]["code"],
            "AUTHENTICATION_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
