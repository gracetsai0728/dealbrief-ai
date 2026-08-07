import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from agents import ModelBehaviorError, WebSearchTool
from flask import Flask
from pydantic import ValidationError

from app.agents.context import IntelligenceRunContext, MeetingBriefRunContext
from app.agents.intelligence_agent import run_intelligence_agent
from app.agents.meeting_brief_agent import run_meeting_brief_agent
from app.errors import ApiError
from app.schemas import (
    CallBriefOutput,
    EmailDraftOutput,
    IntelligenceOutput,
    MeetingAgendaOutput,
)
from app.services.brief_service import normalize_generation_request
from app.services.openai_service import (
    generate_structured_brief,
    generate_structured_intelligence,
)


class BriefRequestTests(unittest.TestCase):
    def test_accepts_current_frontend_labels(self):
        meeting_type, deliverable_type, notes = normalize_generation_request(
            {
                "meetingType": "Winback",
                "deliverable": "Call Brief",
                "notes": "Focus on renewal.",
            }
        )

        self.assertEqual(meeting_type, "winback")
        self.assertEqual(deliverable_type, "call_brief")
        self.assertEqual(notes, "Focus on renewal.")

    def test_rejects_unknown_deliverable(self):
        with self.assertRaises(ApiError):
            normalize_generation_request(
                {"meetingType": "Winback", "deliverable": "Spreadsheet"}
            )


class StructuredOutputTests(unittest.TestCase):
    def test_call_brief_contract(self):
        result = CallBriefOutput.model_validate(
            {
                "title": "ABC Bank Call Brief",
                "summary": "Renewal-focused preparation.",
                "customerSnapshot": "ABC Bank is in renewal review.",
                "keyInsights": ["Usage is growing."],
                "talkingPoints": ["Review reporting value."],
                "suggestedQuestions": ["Which teams need support?"],
                "risksAndOpportunities": ["Reporting adoption is uneven."],
                "nextSteps": ["Prepare a renewal value story."],
            }
        )
        self.assertEqual(result.title, "ABC Bank Call Brief")

    def test_email_contract_rejects_missing_call_to_action(self):
        with self.assertRaises(ValidationError):
            EmailDraftOutput.model_validate(
                {
                    "title": "Follow-up",
                    "summary": "Summary",
                    "email": {
                        "to": "Customer team",
                        "subject": "Next steps",
                        "greeting": "Hello",
                        "paragraphs": ["Thank you."],
                        "signature": "Grace",
                    },
                }
            )

    def test_agenda_contract(self):
        result = MeetingAgendaOutput.model_validate(
            {
                "title": "Winback Agenda",
                "summary": "Quarterly review agenda.",
                "agenda": {
                    "objective": "Align on renewal value.",
                    "desiredOutcome": "Agree on next steps.",
                    "items": [
                        {
                            "time": "10 minutes",
                            "topic": "Adoption",
                            "detail": "Review subscription value.",
                        }
                    ],
                    "preparation": ["Bring subscription details."],
                },
            }
        )
        self.assertEqual(result.agenda.items[0].topic, "Adoption")

    def test_intelligence_contract(self):
        result = IntelligenceOutput.model_validate(
            {
                "aiKeySignal": "Usage is growing while reporting adoption is uneven.",
                "industryDynamics": [
                    {
                        "headline": "Banks prioritize workflow automation",
                        "summary": "Automation remains a major investment area.",
                        "impact": "Connect product value to operating efficiency.",
                    },
                    {
                        "headline": "Banks strengthen data governance",
                        "summary": "Institutions are tightening controls around customer data.",
                        "impact": "Connect platform governance to risk reduction.",
                    },
                ],
                "companyNews": [],
                "recommendedNextSteps": {
                    "crossSell": [{
                        "action": "Introduce analytics workflows.",
                        "priority": "medium",
                        "reason": "Reporting adoption is uneven.",
                        "dueDate": None,
                    }],
                    "upsell": [{
                        "action": "Review advanced reporting capacity.",
                        "priority": "medium",
                        "reason": "Usage is growing.",
                        "dueDate": None,
                    }],
                    "renewal": [{
                        "action": "Prepare a renewal value story.",
                        "priority": "high",
                        "reason": "The account is approaching renewal.",
                        "dueDate": None,
                    }],
                    "winback": [{
                        "action": "Monitor inactive teams.",
                        "priority": "low",
                        "reason": "No subscription is currently canceled.",
                        "dueDate": None,
                    }],
                },
                "metrics": {
                    "accountHealthScore": 74,
                    "totalLicensedSeats": 1200,
                    "activeSubscriptions": 3,
                    "riskReasons": ["One subscription is approaching renewal"],
                },
            }
        )
        self.assertEqual(result.recommendedNextSteps.renewal[0].priority, "high")


class OpenAIServiceTests(unittest.TestCase):
    @patch("app.services.openai_service.run_meeting_brief_agent")
    def test_meeting_brief_service_runs_meeting_brief_agent(self, run_agent):
        parsed = CallBriefOutput.model_validate(
            {
                "title": "ABC Bank Call Brief",
                "summary": "Renewal-focused preparation.",
                "customerSnapshot": "ABC Bank is in renewal review.",
                "keyInsights": ["Usage is growing."],
                "talkingPoints": ["Review reporting value."],
                "suggestedQuestions": ["Which teams need support?"],
                "risksAndOpportunities": ["Reporting adoption is uneven."],
                "nextSteps": ["Prepare a renewal value story."],
            }
        )
        run_agent.return_value = (parsed, "resp_test")
        flask_app = Flask(__name__)
        flask_app.config.update(
            OPENAI_API_KEY="test-key",
            OPENAI_BRIEF_MODEL="test-model",
        )

        with flask_app.app_context():
            result = generate_structured_brief(
                {"customer": {"name": "ABC Bank"}},
                "call_brief",
            )

        self.assertEqual(result["response_id"], "resp_test")
        self.assertEqual(result["content"]["title"], "ABC Bank Call Brief")
        self.assertEqual(run_agent.call_args.kwargs["model"], "test-model")
        self.assertIs(run_agent.call_args.kwargs["output_schema"], CallBriefOutput)

    @patch("app.services.openai_service.run_intelligence_agent")
    def test_intelligence_service_runs_intelligence_agent(self, run_agent):
        action = {
            "action": "Review account plan.",
            "priority": "medium",
            "reason": "Usage supports a focused conversation.",
            "dueDate": None,
        }
        parsed = IntelligenceOutput.model_validate(
            {
                "aiKeySignal": "Usage is stable.",
                "industryDynamics": [
                    {
                        "headline": "Industry change",
                        "summary": "A current market shift.",
                        "impact": "Review customer priorities.",
                    },
                    {
                        "headline": "A second industry change",
                        "summary": "Another relevant market shift.",
                        "impact": "Validate the customer's response plan.",
                    },
                ],
                "companyNews": [],
                "recommendedNextSteps": {
                    "crossSell": [action],
                    "upsell": [action],
                    "renewal": [action],
                    "winback": [action],
                },
                "metrics": {
                    "accountHealthScore": 70,
                    "totalLicensedSeats": 1200,
                    "activeSubscriptions": 3,
                    "riskReasons": [],
                },
            }
        )
        run_agent.return_value = (parsed, "resp_intel")
        flask_app = Flask(__name__)
        flask_app.config.update(
            OPENAI_API_KEY="test-key",
            OPENAI_INTELLIGENCE_MODEL="test-model",
        )

        with flask_app.app_context():
            result = generate_structured_intelligence(
                {"customer": {"name": "ABC Bank"}}
            )

        self.assertEqual(result["response_id"], "resp_intel")
        self.assertEqual(run_agent.call_args.kwargs["model"], "test-model")


class AgentRuntimeTests(unittest.TestCase):
    @patch("app.agents.meeting_brief_agent.set_default_openai_key")
    @patch("app.agents.meeting_brief_agent.Runner.run_sync")
    def test_meeting_brief_agent_uses_required_database_tools(
        self,
        run_sync,
        set_api_key,
    ):
        parsed = CallBriefOutput.model_validate(
            {
                "title": "ABC Bank Call Brief",
                "summary": "Renewal-focused preparation.",
                "customerSnapshot": "ABC Bank is in renewal review.",
                "keyInsights": ["Usage is growing."],
                "talkingPoints": ["Review reporting value."],
                "suggestedQuestions": ["Which teams need support?"],
                "risksAndOpportunities": ["Reporting adoption is uneven."],
                "nextSteps": ["Prepare a renewal value story."],
            }
        )
        result = Mock(
            last_response_id="resp_brief_agent",
            new_items=[
                SimpleNamespace(tool_name="get_customer_profile"),
                SimpleNamespace(tool_name="get_product_context"),
                SimpleNamespace(tool_name="get_latest_subscription"),
                SimpleNamespace(tool_name="get_latest_intelligence"),
            ],
        )
        result.final_output_as.return_value = parsed
        run_sync.return_value = result

        output, response_id = run_meeting_brief_agent(
            context={
                "customerId": "10000000-0000-0000-0000-000000000001",
                "productId": "20000000-0000-0000-0000-000000000001",
                "request": {
                    "meetingType": "winback",
                    "deliverableType": "call_brief",
                    "notes": None,
                },
            },
            api_key="test-key",
            model="test-model",
            output_schema=CallBriefOutput,
        )

        agent = run_sync.call_args.args[0]
        run_config = run_sync.call_args.kwargs["run_config"]
        self.assertEqual(agent.name, "DealBrief Meeting Brief Agent")
        self.assertIs(agent.output_type, CallBriefOutput)
        self.assertEqual(
            [tool.name for tool in agent.tools],
            [
                "get_customer_profile",
                "get_product_context",
                "get_latest_subscription",
                "get_latest_intelligence",
            ],
        )
        self.assertIsInstance(
            run_sync.call_args.kwargs["context"],
            MeetingBriefRunContext,
        )
        self.assertEqual(
            run_config.tool_execution.max_function_tool_concurrency,
            1,
        )
        self.assertEqual(run_config.workflow_name, "dealbrief-meeting-brief")
        self.assertFalse(run_config.trace_include_sensitive_data)
        self.assertEqual(output.title, "ABC Bank Call Brief")
        self.assertEqual(response_id, "resp_brief_agent")
        set_api_key.assert_called_once_with("test-key")

    @patch("app.agents.intelligence_agent.set_default_openai_key")
    @patch("app.agents.intelligence_agent.Runner.run_sync")
    def test_intelligence_agent_uses_database_tools_and_web_search(
        self,
        run_sync,
        set_api_key,
    ):
        action = {
            "action": "Review account plan.",
            "priority": "medium",
            "reason": "Subscription data supports a focused conversation.",
            "dueDate": None,
        }
        parsed = IntelligenceOutput.model_validate(
            {
                "aiKeySignal": "The account has active subscriptions.",
                "industryDynamics": [
                    {
                        "headline": "Industry change",
                        "summary": "A current market shift.",
                        "impact": "Review customer priorities.",
                    },
                    {
                        "headline": "A second industry change",
                        "summary": "Another relevant market shift.",
                        "impact": "Validate the customer's response plan.",
                    },
                ],
                "companyNews": [],
                "recommendedNextSteps": {
                    "crossSell": [action],
                    "upsell": [action],
                    "renewal": [action],
                    "winback": [action],
                },
                "metrics": {
                    "accountHealthScore": 70,
                    "totalLicensedSeats": 1200,
                    "activeSubscriptions": 3,
                    "riskReasons": [],
                },
            }
        )
        result = Mock(
            last_response_id="resp_intelligence_agent",
            new_items=[
                SimpleNamespace(tool_name="get_customer_profile"),
                SimpleNamespace(tool_name="get_product_subscriptions"),
                SimpleNamespace(tool_name="web_search"),
            ],
        )
        result.final_output_as.return_value = parsed
        run_sync.return_value = result

        output, response_id = run_intelligence_agent(
            context={
                "customerId": "10000000-0000-0000-0000-000000000001",
                "analysisPeriod": {
                    "start": "2026-05-01T00:00:00+00:00",
                    "end": "2026-07-31T23:59:59+00:00",
                },
            },
            api_key="test-key",
            model="test-model",
        )

        agent = run_sync.call_args.args[0]
        run_config = run_sync.call_args.kwargs["run_config"]
        self.assertEqual(agent.name, "DealBrief Intelligence Agent")
        self.assertIs(agent.output_type, IntelligenceOutput)
        self.assertEqual(
            [getattr(tool, "name", None) for tool in agent.tools],
            [
                "get_customer_profile",
                "get_product_subscriptions",
                "web_search",
            ],
        )
        self.assertIsInstance(agent.tools[2], WebSearchTool)
        self.assertIsInstance(
            run_sync.call_args.kwargs["context"],
            IntelligenceRunContext,
        )
        self.assertEqual(
            run_config.tool_execution.max_function_tool_concurrency,
            1,
        )
        self.assertEqual(run_config.workflow_name, "dealbrief-intelligence")
        self.assertFalse(run_config.trace_include_sensitive_data)
        self.assertEqual(output.aiKeySignal, "The account has active subscriptions.")
        self.assertEqual(response_id, "resp_intelligence_agent")
        set_api_key.assert_called_once_with("test-key")

    @patch("app.agents.intelligence_agent.set_default_openai_key")
    @patch("app.agents.intelligence_agent.Runner.run_sync")
    def test_intelligence_agent_rejects_missing_required_database_tool(
        self,
        run_sync,
        _set_api_key,
    ):
        run_sync.return_value = Mock(
            new_items=[SimpleNamespace(tool_name="get_customer_profile")]
        )

        with self.assertRaises(ModelBehaviorError):
            run_intelligence_agent(
                context={
                    "customerId": "10000000-0000-0000-0000-000000000001",
                    "analysisPeriod": {
                        "start": "2026-05-01T00:00:00+00:00",
                        "end": "2026-07-31T23:59:59+00:00",
                    },
                },
                api_key="test-key",
                model="test-model",
            )


if __name__ == "__main__":
    unittest.main()
