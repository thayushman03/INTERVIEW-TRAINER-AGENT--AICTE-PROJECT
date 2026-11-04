"""
app.py
------
Flask REST API for the Interview Trainer Agent.
Provides endpoints for session management, question generation,
model answers, and resume upload.
"""

import logging
import os
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG,
    SECRET_KEY, MAX_FILE_SIZE, UPLOAD_DIR,
)
from src.agent import InterviewTrainerAgent
from src.utils import setup_logging

# ── Logging ────────────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)

# ── Flask App ──────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
CORS(app)

# ── Agent (lazy init to avoid blocking startup) ────────────────────────────
_agent: InterviewTrainerAgent | None = None


def get_agent() -> InterviewTrainerAgent:
    global _agent
    if _agent is None:
        _agent = InterviewTrainerAgent()
    return _agent


ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the web UI."""
    return send_from_directory("templates", "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "Interview Trainer Agent", "version": "1.0.0"})


@app.route("/api/roles", methods=["GET"])
def get_roles():
    """Return available job roles."""
    return jsonify({"roles": get_agent().get_available_roles()})


@app.route("/api/levels", methods=["GET"])
def get_levels():
    """Return available experience levels."""
    return jsonify({"levels": get_agent().get_available_levels()})


@app.route("/api/session/start", methods=["POST"])
def start_session():
    """
    Start a new interview prep session from a profile.

    Request JSON:
    {
        "name": "Alice",
        "role": "Software Engineer",
        "experience_level": "mid",
        "skills": ["Python", "Django", "SQL"],   // optional
        "num_technical": 5,                       // optional
        "num_behavioral": 3                       // optional
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    required = ["name", "role", "experience_level"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        session = get_agent().start_session(
            name=data["name"],
            role=data["role"],
            experience_level=data["experience_level"],
            skills=data.get("skills"),
            num_technical=int(data.get("num_technical", 5)),
            num_behavioral=int(data.get("num_behavioral", 3)),
        )
        return jsonify({"success": True, "data": session})
    except Exception as exc:
        logger.error("Session start failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@app.route("/api/session/resume", methods=["POST"])
def start_session_from_resume():
    """
    Start a session by uploading a resume file.

    Form fields:
        file            : Resume file (PDF/DOCX/TXT)
        role            : Target job role
        experience_level: Experience level
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use PDF, DOCX, or TXT"}), 400

    role = request.form.get("role", "Software Engineer")
    experience_level = request.form.get("experience_level", "junior")

    # Save file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    try:
        session = get_agent().start_session_from_resume(
            file_path=filepath,
            role=role,
            experience_level=experience_level,
        )
        return jsonify({"success": True, "data": session})
    except Exception as exc:
        logger.error("Resume session failed: %s", exc)
        return jsonify({"error": str(exc)}), 500
    finally:
        # Clean up uploaded file after processing
        try:
            os.remove(filepath)
        except OSError:
            pass


@app.route("/api/model-answer", methods=["POST"])
def get_model_answer():
    """
    Get a model answer for a specific question.

    Request JSON:
    {
        "question": "What is the bias-variance tradeoff?",
        "role": "Data Scientist",
        "experience_level": "mid",
        "skills": ["Python", "scikit-learn"]   // optional
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    required = ["question", "role", "experience_level"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        result = get_agent().get_model_answer(
            question=data["question"],
            role=data["role"],
            experience_level=data["experience_level"],
            skills=data.get("skills"),
        )
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        logger.error("Model answer failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ── Error handlers ──────────────────────────────────────────────────────────

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": "File too large. Maximum size is 5 MB."}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting Interview Trainer Agent on %s:%s", FLASK_HOST, FLASK_PORT)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
