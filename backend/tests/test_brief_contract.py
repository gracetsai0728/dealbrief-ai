import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from flask import Flask
from pydantic import ValidationError

from app.errors import ApiError
from app.schemas import (
    CallBriefOutput,
    EmailDraftOutput,
    IntelligenceOutput,
    MeetingAgendaOutput,
)
from app.services.brief_service import normalize_generation_request
from app.services.openai_service import generate_structured_brief


class BriefRequestTests(unittest.TestCase):
    def test_accepts_current_frontend_labels(self):
        meeting_type, deliverable_type, notes = normalize_generation_request(
            {
                "meetingType": "QBR",
                "deliverable": "Call Brief",
                "notes": "Focus on renewal.",
            }
        )

        self.assertEqual(meeting_type, "qbr")
        self.assertEqual(deliverable_type, "call_brief")
        self.assertEqual(notes, "Focus on renewal.")

    def test_rejects_unknown_deliverable(self):
        with self.assertRaises(ApiError):
            normalize_generation_request(
                {"meetingType": "QBR", "deliverable": "Spreadsheet"}
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
                "title": "QBR Agenda",
                "summary": "Quarterly review agenda.",
                "agenda": {
                    "objective": "Align on renewal value.",
                    "desiredOutcome": "Agree on next steps.",
                    "items": [
                        {
                            "time": "10 minutes",
                            "topic": "Adoption",
                            "detail": "Review usage trends.",
                        }
                    ],
                    "preparation": ["Bring usage data."],
                },
            }
        )
        self.assertEqual(result.agenda.items[0].topic, "Adoption")

    def test_intelligence_contract(self):
        result = IntelligenceOutput.model_validate(
            {
                "aiKeySignal": "Usage is growing while reporting adoption is uneven.",
                "nextBestActions": [
                    {
                        "action": "Prepare a renewal value story.",
                        "priority": "high",
                        "reason": "The account is approaching renewal.",
                        "dueDate": None,
                    }
                ],
                "metrics": {
                    "accountHealthScore": 74,
                    "adoptionScore": 70,
                    "engagementScore": 72,
                    "usageGrowth": 35,
                    "licenseUtilization": 82,
                    "riskReasons": ["Uneven reporting adoption"],
                },
            }
        )
        self.assertEqual(result.nextBestActions[0].priority, "high")


class OpenAIServiceTests(unittest.TestCase):
    @patch("app.services.openai_service.OpenAI")
    def test_uses_responses_structured_output(self, openai_class):
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
        parse = Mock(return_value=SimpleNamespace(output_parsed=parsed, id="resp_test"))
        openai_class.return_value.responses.parse = parse
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
        self.assertEqual(parse.call_args.kwargs["model"], "test-model")
        self.assertIs(parse.call_args.kwargs["text_format"], CallBriefOutput)


if __name__ == "__main__":
    unittest.main()
