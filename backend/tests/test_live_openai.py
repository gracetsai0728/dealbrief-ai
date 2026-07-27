import os
import unittest

from app import create_app
from app.extensions import db
from app.models import Customer, Engagement, IntelligenceSnapshot, Product


@unittest.skipUnless(
    os.getenv("RUN_LIVE_OPENAI") == "1",
    "Set RUN_LIVE_OPENAI=1 to run paid live OpenAI smoke tests.",
)
class LiveOpenAiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True)
        cls.client = cls.app.test_client()
        cls.created_engagement_ids = []
        cls.created_intelligence_ids = []

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            if cls.created_engagement_ids:
                Engagement.query.filter(
                    Engagement.id.in_(cls.created_engagement_ids)
                ).delete(synchronize_session=False)
            if cls.created_intelligence_ids:
                IntelligenceSnapshot.query.filter(
                    IntelligenceSnapshot.id.in_(cls.created_intelligence_ids)
                ).delete(synchronize_session=False)
            db.session.commit()

    def test_live_brief_and_intelligence_structured_outputs(self):
        with self.app.app_context():
            customer = Customer.query.filter_by(
                salesforce_account_id="SF-ACCT-1042"
            ).first()
            product = Product.query.filter_by(name="CRM Platform").first()
            self.assertIsNotNone(customer)
            self.assertIsNotNone(product)
            customer_id = str(customer.id)
            product_id = str(product.id)

        intelligence = self.client.post(
            f"/api/customers/{customer_id}/intelligence/refresh",
            json={"periodStart": "2026-04-01", "periodEnd": "2026-07-31"},
        )
        self.assertEqual(intelligence.status_code, 201, intelligence.get_json())
        intelligence_data = intelligence.get_json()["data"]
        self.created_intelligence_ids.append(intelligence_data["id"])
        self.assertTrue(intelligence_data["nextBestActions"])
        self.assertIn(intelligence_data["renewalRisk"], {"low", "medium", "high"})

        brief = self.client.post(
            "/api/generate-brief",
            json={
                "customerId": customer_id,
                "productId": product_id,
                "meetingType": "qbr",
                "deliverableType": "call_brief",
                "notes": "Focus on renewal value and reporting adoption.",
            },
        )
        self.assertEqual(brief.status_code, 201, brief.get_json())
        brief_data = brief.get_json()["data"]
        self.created_engagement_ids.append(brief_data["engagementId"])
        self.assertEqual(brief_data["status"], "draft")
        self.assertTrue(brief_data["talkingPoints"])
