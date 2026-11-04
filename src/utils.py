"""
utils.py
--------
Shared utility functions for the Interview Trainer Agent.
"""

import logging
import os
from src.config import LOG_LEVEL, LOG_FILE


def setup_logging() -> None:
    """Configure root logger with file and console handlers."""
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))
    except OSError:
        pass  # If log file can't be created, just use console

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def format_session_report(session: dict) -> str:
    """Format a session dict into a human-readable text report."""
    lines = []
    profile = session.get("profile", {})

    lines.append("=" * 60)
    lines.append("    INTERVIEW TRAINER AGENT – SESSION REPORT")
    lines.append("=" * 60)
    lines.append(f"  Session ID  : {session.get('session_id', 'N/A')}")
    lines.append(f"  Generated   : {session.get('created_at', 'N/A')}")
    lines.append("-" * 60)
    lines.append(f"  Candidate   : {profile.get('name', 'Unknown')}")
    lines.append(f"  Role        : {profile.get('role', 'Unknown')}")
    lines.append(f"  Level       : {profile.get('experience_level', 'Unknown')}")
    skills = profile.get("skills", [])
    if skills:
        lines.append(f"  Skills      : {', '.join(skills[:8])}")
    lines.append("=" * 60)

    # Technical Questions
    tech_qs = session.get("technical_questions", [])
    if tech_qs:
        lines.append(f"\n📌 TECHNICAL QUESTIONS ({len(tech_qs)})")
        lines.append("-" * 40)
        for i, q in enumerate(tech_qs, 1):
            topic = q.get("topic", "")
            tag = f" [{topic}]" if topic else ""
            lines.append(f"{i}. {q['question']}{tag}")

    # Behavioral Questions
    behav_qs = session.get("behavioral_questions", [])
    if behav_qs:
        lines.append(f"\n🧠 BEHAVIORAL QUESTIONS ({len(behav_qs)})")
        lines.append("-" * 40)
        for i, q in enumerate(behav_qs, 1):
            framework = q.get("framework", "STAR")
            lines.append(f"{i}. {q['question']} [{framework}]")
            tip = q.get("tip", "")
            if tip:
                lines.append(f"   💡 Tip: {tip}")

    # Preparation Strategy
    prep = session.get("preparation_strategy", "")
    if prep:
        lines.append(f"\n📅 PREPARATION STRATEGY")
        lines.append("-" * 40)
        lines.append(prep)

    # Improvement Tips
    tips = session.get("improvement_tips", "")
    if tips:
        lines.append(f"\n🎯 IMPROVEMENT TIPS")
        lines.append("-" * 40)
        lines.append(tips)

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
