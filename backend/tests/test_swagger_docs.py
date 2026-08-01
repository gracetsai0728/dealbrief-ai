import unittest

from app import create_app


class SwaggerTestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://localhost:5173"]
    OPENAI_API_KEY = None
    OPENAI_BRIEF_MODEL = "test-model"
    OPENAI_INTELLIGENCE_MODEL = "test-model"


class SwaggerDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(SwaggerTestConfig)
        cls.client = cls.app.test_client()

    def test_swagger_ui_is_available(self):
        with self.client.get("/api/docs") as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"DealBrief AI API Docs", response.data)
            self.assertIn(b"/api/openapi.yaml", response.data)
            self.assertIn(b"SwaggerUIBundle", response.data)

    def test_openapi_spec_is_available(self):
        with self.client.get("/api/openapi.yaml") as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("application/yaml", response.content_type)
            self.assertIn(b"openapi: 3.0.3", response.data)
            self.assertIn(b"/generate-brief:", response.data)
            self.assertIn(b"/engagement-log/{engagementId}:", response.data)


if __name__ == "__main__":
    unittest.main()
