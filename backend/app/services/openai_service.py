from agents import AgentsException
from flask import current_app
from openai import OpenAIError

from ..agents import run_intelligence_agent, run_meeting_brief_agent
from ..errors import ApiError
from ..schemas import BRIEF_OUTPUT_SCHEMAS, IntelligenceOutput


def generate_structured_brief(context, deliverable_type):
    api_key = current_app.config.get("OPENAI_API_KEY")
    if not api_key:
        raise ApiError(
            "OPENAI_NOT_CONFIGURED",
            "OPENAI_API_KEY is not configured on the Flask server.",
            503,
        )

    output_schema = BRIEF_OUTPUT_SCHEMAS[deliverable_type]
    model = current_app.config["OPENAI_BRIEF_MODEL"]

    try:
        output, response_id = run_meeting_brief_agent(
            context=context,
            api_key=api_key,
            model=model,
            output_schema=output_schema,
        )
    except (AgentsException, OpenAIError) as error:
        current_app.logger.exception("Meeting Brief Agent failed")
        raise ApiError(
            "OPENAI_REQUEST_FAILED",
            "The Meeting Brief Agent could not generate the meeting brief.",
            502,
        ) from error

    if not isinstance(output, output_schema):
        raise ApiError(
            "OPENAI_INVALID_OUTPUT",
            "The Meeting Brief Agent did not return a usable structured meeting brief.",
            502,
        )

    return {
        "content": output.model_dump(),
        "model": model,
        "response_id": response_id,
    }


def generate_structured_intelligence(context):
    api_key = current_app.config.get("OPENAI_API_KEY")
    if not api_key:
        raise ApiError(
            "OPENAI_NOT_CONFIGURED",
            "OPENAI_API_KEY is not configured on the Flask server.",
            503,
        )

    model = current_app.config["OPENAI_INTELLIGENCE_MODEL"]

    try:
        output, response_id = run_intelligence_agent(
            context=context,
            api_key=api_key,
            model=model,
        )
    except (AgentsException, OpenAIError) as error:
        current_app.logger.exception("Intelligence Agent failed")
        raise ApiError(
            "OPENAI_REQUEST_FAILED",
            "The Intelligence Agent could not generate the intelligence snapshot.",
            502,
        ) from error

    if not isinstance(output, IntelligenceOutput):
        raise ApiError(
            "OPENAI_INVALID_OUTPUT",
            "The Intelligence Agent did not return a usable structured intelligence snapshot.",
            502,
        )

    return {
        "content": output.model_dump(),
        "model": model,
        "response_id": response_id,
    }
