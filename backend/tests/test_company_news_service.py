import unittest
from datetime import date
from types import SimpleNamespace

from app.services.company_news_service import (
    SYNTHETIC_SOURCE_NAME,
    normalize_news_mode,
    resolve_company_news,
)


class CompanyNewsServiceTests(unittest.TestCase):
    def setUp(self):
        self.customer = SimpleNamespace(
            name="Example Demo Bank",
            industry="Financial Services",
        )
        self.subscriptions = [
            SimpleNamespace(
                subscription_start_date=date(2026, 1, 1),
                subscription_end_date=date(2026, 12, 31),
                subscription_status="active",
                licensed_seats=250,
                product=SimpleNamespace(name="CRM Platform"),
            )
        ]
        self.as_of = date(2026, 8, 17)

    def test_unknown_mode_defaults_to_hybrid(self):
        self.assertEqual(normalize_news_mode("unsupported"), "hybrid")

    def test_hybrid_uses_verified_web_news_when_available(self):
        generated = [{
            "headline": "Verified company update",
            "summary": "A sourced public update.",
            "sourceName": "Example Publisher",
            "sourceUrl": "https://publisher.example/update",
            "publishedDate": "2026-08-10",
            "sourceType": "web",
            "isMock": False,
        }]

        resolved = resolve_company_news(
            "hybrid", generated, self.customer, self.subscriptions, self.as_of
        )

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]["sourceType"], "web")
        self.assertFalse(resolved[0]["isMock"])
        self.assertEqual(resolved[0]["sourceUrl"], generated[0]["sourceUrl"])

    def test_hybrid_builds_two_labeled_scenarios_without_fake_urls(self):
        resolved = resolve_company_news(
            "hybrid", [], self.customer, self.subscriptions, self.as_of
        )

        self.assertEqual(len(resolved), 2)
        for item in resolved:
            self.assertEqual(item["sourceType"], "synthetic")
            self.assertTrue(item["isMock"])
            self.assertEqual(item["sourceName"], SYNTHETIC_SOURCE_NAME)
            self.assertIsNone(item["sourceUrl"])
            self.assertTrue(item["summary"].startswith("Synthetic demo scenario"))

    def test_real_mode_never_returns_synthetic_news(self):
        generated = [{
            "headline": "Fictional update",
            "summary": "Synthetic demo scenario — not real company news.",
            "sourceName": SYNTHETIC_SOURCE_NAME,
            "sourceUrl": None,
            "publishedDate": "2026-08-10",
            "sourceType": "synthetic",
            "isMock": True,
        }]

        resolved = resolve_company_news(
            "real", generated, self.customer, self.subscriptions, self.as_of
        )

        self.assertEqual(resolved, [])


if __name__ == "__main__":
    unittest.main()
