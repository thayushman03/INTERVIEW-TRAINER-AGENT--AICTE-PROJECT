"""
config.py
---------
Centralised configuration loader.
Reads all settings from .env and exposes them as typed constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ── IBM WatsonX / Granite ──────────────────────────────────────────────────
IBM_CLOUD_API_KEY: str = os.getenv("IBM_CLOUD_API_KEY", "")
WATSONX_PROJECT_ID: str = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL: str = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_MODEL_ID: str = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-chat-v2")
GRANITE_INSTRUCT_MODEL_ID: str = os.getenv(
    "GRANITE_INSTRUCT_MODEL_ID", "ibm/granite-3-8b-instruct"
)

# ── RAG / Vector Store ─────────────────────────────────────────────────────
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))

# ── Application ────────────────────────────────────────────────────────────
FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "5242880"))
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "60"))

# ── LLM Generation ─────────────────────────────────────────────────────────
LLM_MAX_NEW_TOKENS: int = int(os.getenv("LLM_MAX_NEW_TOKENS", "800"))
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "0.9"))
LLM_TOP_K: int = int(os.getenv("LLM_TOP_K", "50"))
LLM_REPETITION_PENALTY: float = float(os.getenv("LLM_REPETITION_PENALTY", "1.1"))

# ── Logging ────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", "./logs/interview_trainer.log")

# ── Validation ─────────────────────────────────────────────────────────────
REQUIRED_VARS = ["IBM_CLOUD_API_KEY", "WATSONX_PROJECT_ID"]


def validate_config() -> list[str]:
    """Return a list of missing required environment variables."""
    missing = []
    for var in REQUIRED_VARS:
        val = os.getenv(var, "")
        if not val or val.endswith("_here"):
            missing.append(var)
    return missing
