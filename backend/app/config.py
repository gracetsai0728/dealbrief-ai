import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/dealbriefai",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BRIEF_MODEL = os.getenv("OPENAI_BRIEF_MODEL", "gpt-5.6-terra")
    OPENAI_INTELLIGENCE_MODEL = os.getenv(
        "OPENAI_INTELLIGENCE_MODEL",
        os.getenv("OPENAI_BRIEF_MODEL", "gpt-5.6-terra"),
    )
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
