import os
import unittest

from app import create_app
from app.extensions import db
from app.models import Customer, IntelligenceSnapshot, Product


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
        cls.created_intelligence_ids = []
        login_response = cls.client.post(
            "/api/auth/login",
            json={"email": "user@dealbrief.ai", "password": "User123!"},
        )
        if login_response.status_code != 200:
            raise RuntimeError("Seeded user login failed.")

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            if cls.created_intelligence_ids:
                IntelligenceSnapshot.query.filter(
                    IntelligenceSnapshot.id.in_(cls.created_intelligence_ids)
                ).delete(synchronize_session=False)
            db.session.commit()

    def test_live_brief_and_intelligence_structured_outputs(self):
        with self.app.app_context():
            customer = Customer.query.filter_by(name="ABC Bank").first()
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
        self.assertEqual(len(intelligence_data["industryDynamics"]), 2)
        self.assertTrue(intelligence_data["recommendedNextSteps"]["renewal"])
        self.assertTrue(intelligence_data["aiKeySignal"])

        brief = self.client.post(
            "/api/generate-brief",
            json={
                "customerId": customer_id,
                "productId": product_id,
                "meetingType": "winback",
                "deliverableType": "call_brief",
                "notes": "Focus on renewal value and reporting adoption.",
            },
        )
        self.assertEqual(brief.status_code, 201, brief.get_json())
        brief_data = brief.get_json()["data"]
        self.assertNotIn("engagementId", brief_data)
        self.assertTrue(brief_data["talkingPoints"])
