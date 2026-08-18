import asyncio
import os
import unittest
from datetime import date
from unittest.mock import patch

from agents.tool_context import ToolContext
from sqlalchemy import inspect

from app import create_app
from app.agents.context import (
    IntelligenceRunContext,
    MeetingBriefRunContext,
)
from app.agents.database_tools import (
    get_customer_profile,
    get_latest_intelligence,
    get_latest_subscription,
    get_product_context,
    get_product_subscriptions,
)
from app.extensions import db
from app.models import (
    Customer,
    IntelligenceSnapshot,
    Product,
    Subscription,
    User,
)


@unittest.skipUnless(
    os.getenv("RUN_DB_INTEGRATION") == "1",
    "Set RUN_DB_INTEGRATION=1 to run PostgreSQL integration tests.",
)
class DatabaseApiIntegrationTests(unittest.TestCase):
    integration_customer_name = "API Integration Test Customer"
    registered_email = "registered-api-test@dealbrief.ai"
    manual_customer_name = "Manual API Test Customer"
    manual_product_name = "Manual API Test Product"
    seeded_customer_names = {
        "ABC Bank",
        "Northstar Retail",
        "GreenHealth Group",
        "Summit Manufacturing",
        "BrightPath Education",
    }

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True, INTELLIGENCE_NEWS_MODE="hybrid")
        cls.client = cls.app.test_client()
        cls._cleanup()
        login_response = cls.client.post(
            "/api/auth/login",
            json={"email": "admin@dealbrief.ai", "password": "Admin123!"},
        )
        if login_response.status_code != 200:
            raise RuntimeError("Seeded admin login failed; apply database/schema.sql and database/seed.sql.")

    @classmethod
    def tearDownClass(cls):
        cls._cleanup()

    @classmethod
    def _cleanup(cls):
        with cls.app.app_context():
            customer = Customer.query.filter_by(name=cls.integration_customer_name).first()
            if customer:
                IntelligenceSnapshot.query.filter_by(customer_id=customer.id).delete()
                Subscription.query.filter_by(customer_id=customer.id).delete()
                db.session.delete(customer)
                db.session.flush()
            manual_customer = Customer.query.filter_by(name=cls.manual_customer_name).first()
            if manual_customer:
                IntelligenceSnapshot.query.filter_by(customer_id=manual_customer.id).delete()
                Subscription.query.filter_by(customer_id=manual_customer.id).delete()
                db.session.delete(manual_customer)
                db.session.flush()
            Product.query.filter_by(name=cls.manual_product_name).delete()
            User.query.filter_by(email=cls.registered_email).delete()
            db.session.commit()

    def test_authentication_and_registration_roles(self):
        anonymous = self.app.test_client()
        protected = anonymous.get("/api/customers")
        self.assertEqual(protected.status_code, 401)

        registration = anonymous.post(
            "/api/auth/register",
            json={
                "name": "Registered API Test",
                "email": self.registered_email,
                "password": "Registered123!",
            },
        )
        self.assertEqual(registration.status_code, 201)
        self.assertEqual(registration.get_json()["data"]["user"]["role"], "user")
        forbidden = anonymous.post("/api/products", json={"name": "Forbidden Product"})
        self.assertEqual(forbidden.status_code, 403)

        me = anonymous.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.get_json()["data"]["user"]["email"], self.registered_email)
        self.assertEqual(anonymous.post("/api/auth/logout").status_code, 200)
        self.assertEqual(anonymous.get("/api/auth/me").status_code, 401)

    def test_every_seeded_customer_has_initial_intelligence(self):
        with self.app.app_context():
            customers = Customer.query.filter(
                Customer.name.in_(self.seeded_customer_names)
            ).all()

            self.assertEqual(len(customers), len(self.seeded_customer_names))
            for customer in customers:
                snapshot = (
                    IntelligenceSnapshot.query.filter_by(customer_id=customer.id)
                    .order_by(IntelligenceSnapshot.generated_at.desc())
                    .first()
                )
                self.assertIsNotNone(
                    snapshot,
                    f"{customer.name} should have an initial intelligence snapshot.",
                )

    def test_agent_function_tools_read_authorized_database_context(self):
        with self.app.app_context():
            customer = Customer.query.filter_by(name="ABC Bank").one()
            product = Product.query.filter_by(name="CRM Platform").one()
            counts_before = (
                Customer.query.count(),
                Product.query.count(),
                Subscription.query.count(),
                IntelligenceSnapshot.query.count(),
            )

            intelligence_context = IntelligenceRunContext(
                customer_id=customer.id,
                period_start=date(2022, 1, 1),
                period_end=date(2026, 12, 31),
            )
            meeting_context = MeetingBriefRunContext(
                customer_id=customer.id,
                product_id=product.id,
            )

            profile = self._invoke_agent_tool(
                get_customer_profile,
                intelligence_context,
            )
            subscriptions = self._invoke_agent_tool(
                get_product_subscriptions,
                intelligence_context,
            )
            product_context = self._invoke_agent_tool(
                get_product_context,
                meeting_context,
            )
            latest_subscription = self._invoke_agent_tool(
                get_latest_subscription,
                meeting_context,
            )
            latest_intelligence = self._invoke_agent_tool(
                get_latest_intelligence,
                meeting_context,
            )

            self.assertEqual(profile.name, "ABC Bank")
            self.assertGreater(len(subscriptions), 0)
            self.assertEqual(product_context.name, "CRM Platform")
            self.assertTrue(latest_subscription.found)
            self.assertTrue(latest_intelligence.found)
            self.assertEqual(
                counts_before,
                (
                    Customer.query.count(),
                    Product.query.count(),
                    Subscription.query.count(),
                    IntelligenceSnapshot.query.count(),
                ),
            )

    @staticmethod
    def _invoke_agent_tool(tool, context):
        tool_context = ToolContext(
            context=context,
            tool_name=tool.name,
            tool_call_id=f"test_{tool.name}",
            tool_arguments="{}",
        )
        return asyncio.run(tool.on_invoke_tool(tool_context, "{}"))

    def test_usage_storage_was_removed(self):
        with self.app.app_context():
            inspector = inspect(db.engine)
            self.assertNotIn("subscription_usage_points", inspector.get_table_names())
            subscription_columns = {
                column["name"] for column in inspector.get_columns("subscriptions")
            }
            customer_columns = {
                column["name"] for column in inspector.get_columns("customers")
            }
            intelligence_columns = {
                column["name"]
                for column in inspector.get_columns("intelligence_snapshots")
            }
            self.assertNotIn("account_owner_id", customer_columns)
            self.assertNotIn("salesforce_account_id", customer_columns)
            self.assertNotIn("snapshot_date", subscription_columns)
            self.assertNotIn("license_utilization", subscription_columns)
            self.assertNotIn("usage_growth", subscription_columns)
            self.assertNotIn("feature_adoption", subscription_columns)
            for removed_column in {
                "snapshot_date",
                "model",
                "prompt_version",
                "period_start",
                "period_end",
                "source_data_through",
                "generation_status",
            }:
                self.assertNotIn(removed_column, intelligence_columns)

    def test_seeded_timelines_have_varied_product_portfolios(self):
        expected_portfolios = {
            "ABC Bank": (8, 2),
            "Northstar Retail": (12, 3),
            "GreenHealth Group": (5, 1),
            "Summit Manufacturing": (8, 2),
            "BrightPath Education": (7, 2),
        }

        with self.app.app_context():
            for (
                customer_name,
                (contract_count, product_count),
            ) in expected_portfolios.items():
                customer = Customer.query.filter_by(name=customer_name).first()
                self.assertIsNotNone(customer)
                subscriptions = Subscription.query.filter_by(
                    customer_id=customer.id
                ).all()
                self.assertEqual(len(subscriptions), contract_count)
                self.assertEqual(
                    len({subscription.product_id for subscription in subscriptions}),
                    product_count,
                )

            abc = Customer.query.filter_by(name="ABC Bank").first()
            customer_id = str(abc.id)

        timeline = self.client.get(
            f"/api/customers/{customer_id}/timeline"
        ).get_json()["data"]
        self.assertEqual(timeline["periodStart"], "2022-01-01")
        self.assertEqual(len(timeline["series"]), 2)
        crm_series = next(
            item for item in timeline["series"] if item["productName"] == "CRM Platform"
        )
        self.assertEqual(crm_series["licensedSeats"], 500)
        self.assertEqual(crm_series["seatPoints"][0]["date"], "2022-01-01")
        self.assertEqual(len(crm_series["seatPoints"]), 6)
        renewal_dates = [
            point["date"] for point in crm_series["seatPoints"][:-1]
        ]
        self.assertEqual(
            renewal_dates,
            [
                "2022-01-01",
                "2023-01-01",
                "2024-01-01",
                "2025-01-01",
                "2026-01-01",
            ],
        )

    def test_admin_can_manually_create_customer_product_and_subscription(self):
        customer_response = self.client.post(
            "/api/customers",
            json={
                "name": self.manual_customer_name,
                "industry": "Software",
            },
        )
        self.assertEqual(customer_response.status_code, 201)
        customer_data = customer_response.get_json()["data"]
        customer_id = customer_data["id"]
        self.assertNotIn("opportunityStage", customer_data)
        self.assertNotIn("renewalDate", customer_data)

        product_response = self.client.post(
            "/api/products",
            json={"name": self.manual_product_name, "description": "Created manually."},
        )
        self.assertEqual(product_response.status_code, 201)
        product_id = product_response.get_json()["data"]["id"]

        subscription_response = self.client.post(
            "/api/subscriptions",
            json={
                "customerId": customer_id,
                "productId": product_id,
                "subscriptionStartDate": "2026-08-01",
                "subscriptionEndDate": "2027-07-31",
                "subscriptionStatus": "active",
                "licensedSeats": 50,
            },
        )
        self.assertEqual(subscription_response.status_code, 201)
        subscription = subscription_response.get_json()["data"]
        self.assertEqual(subscription["licensedSeats"], 50)
        self.assertEqual(subscription["subscriptionStatus"], "active")
        self.assertNotIn("snapshotDate", subscription)
        self.assertNotIn("activeUsers", subscription)
        self.assertNotIn("licenseUtilization", subscription)
        self.assertNotIn("usageGrowth", subscription)
        self.assertNotIn("featureAdoption", subscription)

    def test_full_database_backed_api_flow(self):
        product_response = self.client.get("/api/products")
        self.assertEqual(product_response.status_code, 200)
        products = product_response.get_json()["data"]
        product = next(item for item in products if item["name"] == "CRM Platform")

        customer_response = self.client.post(
            "/api/customers",
            json={
                "name": self.integration_customer_name,
                "industry": "Software",
            },
        )
        self.assertEqual(customer_response.status_code, 201)
        customer_id = customer_response.get_json()["data"]["id"]

        customers = self.client.get("/api/customers?search=API%20Integration").get_json()[
            "data"
        ]
        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0]["id"], customer_id)

        subscription_response = self.client.post(
            "/api/subscriptions",
            json={
                "customerId": customer_id,
                "productId": product["id"],
                "subscriptionStartDate": "2026-01-01",
                "subscriptionEndDate": "2026-12-31",
                "subscriptionStatus": "active",
                "licensedSeats": 100,
            },
        )
        self.assertEqual(subscription_response.status_code, 201)
        self.assertEqual(subscription_response.get_json()["data"]["licensedSeats"], 100)
        subscriptions = self.client.get(
            f"/api/subscriptions?customerId={customer_id}"
        ).get_json()["data"]
        self.assertEqual(len(subscriptions), 1)
        subscription_id = subscriptions[0]["id"]
        timeline = self.client.get(
            f"/api/customers/{customer_id}/timeline"
        ).get_json()["data"]
        self.assertEqual(len(timeline["series"]), 1)
        self.assertEqual(timeline["series"][0]["licensedSeats"], 100)
        self.assertEqual(timeline["series"][0]["seatPoints"][0]["seats"], 100)

        intelligence_result = {
            "content": {
                "aiKeySignal": "Usage is growing with room for reporting adoption.",
                "industryDynamics": [
                    {
                        "headline": "Software buyers prioritize measurable adoption",
                        "summary": "Value realization remains a purchasing focus.",
                        "impact": "Use the subscription footprint in the account plan.",
                    },
                    {
                        "headline": "Software teams consolidate core platforms",
                        "summary": "Buyers are reducing fragmented point solutions.",
                        "impact": "Position connected workflows across subscribed products.",
                    },
                ],
                "companyNews": [],
                "recommendedNextSteps": {
                    "crossSell": [{
                        "action": "Introduce analytics.",
                        "priority": "medium",
                        "reason": "The portfolio has room for expansion.",
                        "dueDate": None,
                    }],
                    "upsell": [{
                        "action": "Review advanced capacity.",
                        "priority": "medium",
                        "reason": "Usage is growing.",
                        "dueDate": None,
                    }],
                    "renewal": [{
                        "action": "Validate reporting goals",
                        "priority": "high",
                        "reason": "The subscription is approaching renewal.",
                        "dueDate": None,
                    }],
                    "winback": [{
                        "action": "Monitor inactive teams.",
                        "priority": "low",
                        "reason": "No canceled subscription exists.",
                        "dueDate": None,
                    }],
                },
                "metrics": {
                    "accountHealthScore": 76,
                    "totalLicensedSeats": 100,
                    "activeSubscriptions": 1,
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
        self.assertEqual(
            len(intelligence_response.get_json()["data"]["industryDynamics"]),
            2,
        )
        company_news = intelligence_response.get_json()["data"]["companyNews"]
        self.assertEqual(len(company_news), 2)
        self.assertTrue(all(item["isMock"] for item in company_news))
        self.assertTrue(all(item["sourceType"] == "synthetic" for item in company_news))
        self.assertTrue(all(item["sourceUrl"] is None for item in company_news))
        self.assertEqual(
            intelligence_response.get_json()["data"]["recommendedNextSteps"]["renewal"][0][
                "priority"
            ],
            # The deterministic rules engine overrides the AI placeholder. This
            # 100-seat contract is 153 days from renewal, so it scores medium.
            "medium",
        )
        intelligence_data = intelligence_response.get_json()["data"]
        for removed_field in {
            "snapshotDate",
            "model",
            "promptVersion",
            "periodStart",
            "periodEnd",
            "sourceDataThrough",
            "generationStatus",
        }:
            self.assertNotIn(removed_field, intelligence_data)

        brief_result = {
            "content": {
                "title": "Integration Test Call Brief",
                "summary": "Prepare to validate reporting goals.",
                "customerSnapshot": "The customer has 100 licensed seats.",
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
                    "meetingType": "winback",
                    "deliverableType": "call_brief",
                    "notes": "Focus on reporting.",
                },
            )
        self.assertEqual(brief_response.status_code, 201)
        brief_data = brief_response.get_json()["data"]
        self.assertNotIn("engagementId", brief_data)
        self.assertNotIn("status", brief_data)
        dashboard = self.client.get(
            f"/api/customers/{customer_id}/dashboard"
        ).get_json()["data"]
        self.assertNotIn("engagementTimeline", dashboard)
        self.assertIn("latestSubscriptions", dashboard)
        self.assertNotIn("latestUsage", dashboard)
        self.assertEqual(self.client.get("/api/engagement-log").status_code, 404)
        self.assertEqual(self.client.get("/api/imports").status_code, 404)
        self.assertEqual(self.client.get("/api/usage").status_code, 404)

        subscription_delete = self.client.delete(
            f"/api/subscriptions/{subscription_id}"
        )
        self.assertEqual(subscription_delete.status_code, 200)
        self.assertEqual(
            self.client.get(
                f"/api/subscriptions?customerId={customer_id}"
            ).get_json()["data"],
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
                "meetingType": "winback",
                "deliverableType": "call_brief",
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["error"]["code"], "VALIDATION_ERROR")
