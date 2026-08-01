import os
import unittest
from unittest.mock import patch

from app import create_app
from app.extensions import db
from app.models import (
    Customer,
    Engagement,
    ImportJob,
    IntelligenceSnapshot,
    Product,
    UsageSnapshot,
)


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION") == "1",
    "Set RUN_DB_INTEGRATION=1 to run PostgreSQL integration tests.",
)
class DatabaseApiIntegrationTests(unittest.TestCase):
    customer_salesforce_id = "TEST-CAPSTONE-API-001"
    customer_filename = "test-capstone-customers.json"
    usage_filename = "test-capstone-usage.json"

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True)
        cls.client = cls.app.test_client()
        cls._cleanup()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup()

    @classmethod
    def _cleanup(cls):
        with cls.app.app_context():
            customer = Customer.query.filter_by(
                salesforce_account_id=cls.customer_salesforce_id
            ).first()
            if customer:
                IntelligenceSnapshot.query.filter_by(customer_id=customer.id).delete()
                Engagement.query.filter_by(customer_id=customer.id).delete()
                UsageSnapshot.query.filter_by(customer_id=customer.id).delete()
                db.session.delete(customer)
                db.session.flush()
            ImportJob.query.filter(
                ImportJob.filename.in_([cls.customer_filename, cls.usage_filename])
            ).delete(synchronize_session=False)
            db.session.commit()

    def test_full_database_backed_api_flow(self):
        product_response = self.client.get("/api/products")
        self.assertEqual(product_response.status_code, 200)
        products = product_response.get_json()["data"]
        product = next(item for item in products if item["name"] == "CRM Platform")

        customer_import = self.client.post(
            "/api/imports/customers",
            json={
                "filename": self.customer_filename,
                "rows": [
                    {
                        "name": "API Integration Test Customer",
                        "industry": "Software",
                        "salesforceAccountId": self.customer_salesforce_id,
                        "opportunityStage": "Discovery",
                        "renewalDate": "2027-01-15",
                        "status": "active",
                    }
                ],
            },
        )
        self.assertEqual(customer_import.status_code, 201)
        self.assertEqual(customer_import.get_json()["data"]["insertedRows"], 1)

        customers = self.client.get("/api/customers?search=API%20Integration").get_json()[
            "data"
        ]
        self.assertEqual(len(customers), 1)
        customer_id = customers[0]["id"]

        usage_import = self.client.post(
            "/api/imports/usage",
            json={
                "filename": self.usage_filename,
                "rows": [
                    {
                        "customerId": customer_id,
                        "productId": product["id"],
                        "snapshotDate": "2026-07-20",
                        "activeUsers": 80,
                        "licensedSeats": 100,
                        "licenseUtilization": 80,
                        "usageGrowth": 12.5,
                        "featureAdoption": {"Reporting": 55},
                    }
                ],
            },
        )
        self.assertEqual(usage_import.status_code, 201)
        self.assertEqual(usage_import.get_json()["data"]["insertedRows"], 1)
        usage_rows = self.client.get(f"/api/usage?customerId={customer_id}").get_json()[
            "data"
        ]
        self.assertEqual(len(usage_rows), 1)
        usage_id = usage_rows[0]["id"]

        intelligence_result = {
            "content": {
                "aiKeySignal": "Usage is growing with room for reporting adoption.",
                "nextBestActions": [
                    {
                        "action": "Validate reporting goals",
                        "priority": "high",
                        "reason": "Reporting adoption trails overall utilization.",
                        "dueDate": None,
                    }
                ],
                "metrics": {
                    "accountHealthScore": 76,
                    "adoptionScore": 72,
                    "engagementScore": 60,
                    "usageGrowth": 12.5,
                    "licenseUtilization": 80,
                    "riskReasons": ["No saved meetings in the analysis period"],
                },
            },
            "model": "test-model",
            "response_id": "resp_intelligence_test",
        }
        with patch(
            "app.services.intelligence_service.generate_structured_intelligence",
            return_value=intelligence_result,
        ):
            intelligence_response = self.client.post(
                f"/api/customers/{customer_id}/intelligence/refresh",
                json={"periodStart": "2026-07-01", "periodEnd": "2026-07-31"},
            )
        self.assertEqual(intelligence_response.status_code, 201)
        self.assertEqual(
            intelligence_response.get_json()["data"]["metrics"]["accountHealthScore"], 76
        )

        brief_result = {
            "content": {
                "title": "Integration Test Call Brief",
                "summary": "Prepare to validate reporting goals.",
                "customerSnapshot": "The customer has 80 percent utilization.",
                "keyInsights": ["Usage is growing."],
                "talkingPoints": ["Discuss reporting goals."],
                "suggestedQuestions": ["Which reports matter most?"],
                "risksAndOpportunities": ["Reporting adoption can improve."],
                "nextSteps": ["Agree on a reporting success metric."],
            },
            "model": "test-model",
            "response_id": "resp_brief_test",
        }
        with patch(
            "app.services.brief_service.generate_structured_brief",
            return_value=brief_result,
        ):
            brief_response = self.client.post(
                "/api/generate-brief",
                json={
                    "customerId": customer_id,
                    "productId": product["id"],
                    "meetingType": "qbr",
                    "deliverableType": "call_brief",
                    "notes": "Focus on reporting.",
                },
            )
        self.assertEqual(brief_response.status_code, 201)
        engagement_id = brief_response.get_json()["data"]["engagementId"]

        save_response = self.client.post(
            "/api/engagement-log", json={"engagementId": engagement_id}
        )
        self.assertEqual(save_response.status_code, 200)
        dashboard = self.client.get(
            f"/api/customers/{customer_id}/dashboard"
        ).get_json()["data"]
        self.assertEqual(len(dashboard["engagementTimeline"]), 1)

        archive_response = self.client.delete(
            f"/api/engagement-log/{engagement_id}"
        )
        self.assertEqual(archive_response.status_code, 200)
        self.assertEqual(archive_response.get_json()["data"]["status"], "archived")

        usage_delete = self.client.delete(f"/api/usage/{usage_id}")
        self.assertEqual(usage_delete.status_code, 200)
        self.assertEqual(
            self.client.get(f"/api/usage?customerId={customer_id}").get_json()["data"],
            [],
        )

        customer_delete = self.client.delete(f"/api/customers/{customer_id}")
        self.assertEqual(customer_delete.status_code, 200)
        self.assertEqual(customer_delete.get_json()["data"]["deleteMode"], "soft")
        self.assertEqual(
            self.client.get("/api/customers?search=API%20Integration").get_json()[
                "data"
            ],
            [],
        )

    def test_generate_brief_requires_customer_id(self):
        response = self.client.post(
            "/api/generate-brief",
            json={
                "productId": "20000000-0000-0000-0000-000000000001",
                "meetingType": "qbr",
                "deliverableType": "call_brief",
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error"]["code"], "VALIDATION_ERROR")
