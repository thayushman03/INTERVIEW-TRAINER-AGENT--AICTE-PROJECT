"""
agent.py
--------
Interview Trainer Agent – main orchestrator.

Coordinates the resume parser, RAG engine, and question generator
to provide a complete, personalised interview preparation experience.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from src.config import UPLOAD_DIR, validate_config
from src.resume_parser import ResumeParser
from src.rag_engine import get_rag_engine
from src.question_generator import QuestionGenerator
from src.knowledge_base import EXPERIENCE_LEVELS, normalise_role

logger = logging.getLogger(__name__)


class InterviewTrainerAgent:
    """
    The core Interview Trainer Agent.

    It accepts a user profile (name, role, experience level) or a resume
    file, then orchestrates the RAG pipeline and Granite LLM to produce:
    - A personalised question set (technical + behavioral)
    - Model answers
    - A preparation strategy
    - Improvement tips

    Example
    -------
    >>> agent = InterviewTrainerAgent()
    >>> session = agent.start_session(
    ...     name="Alice",
    ...     role="Data Scientist",
    ...     experience_level="mid",
    ... )
    >>> print(session["technical_questions"])
    """

    SUPPORTED_LEVELS = list(EXPERIENCE_LEVELS.keys())

    def __init__(self):
        missing = validate_config()
        if missing:
            logger.warning(
                "Missing IBM Cloud credentials: %s — "
                "LLM features will run in fallback mode.",
                missing,
            )

        self.rag = get_rag_engine()
        self.resume_parser = ResumeParser()
        self._question_gen: Optional[QuestionGenerator] = None
        self._llm_available = not bool(missing)

        os.makedirs(UPLOAD_DIR, exist_ok=True)

    @property
    def question_generator(self) -> QuestionGenerator:
        """Lazy-initialise the question generator (requires LLM connection)."""
        if self._question_gen is None:
            from src.granite_llm import get_llm
            llm = get_llm()
            self._question_gen = QuestionGenerator(llm=llm, rag=self.rag)
        return self._question_gen

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_session(
        self,
        name: str,
        role: str,
        experience_level: str,
        skills: Optional[list[str]] = None,
        resume_text: Optional[str] = None,
        num_technical: int = 5,
        num_behavioral: int = 3,
    ) -> dict:
        """
        Start a new interview preparation session.

        Parameters
        ----------
        name             : Candidate's full name
        role             : Target job role (e.g. "Software Engineer")
        experience_level : One of fresher | junior | mid | senior | lead
        skills           : List of skills (auto-extracted from resume if not provided)
        resume_text      : Raw resume text (optional)
        num_technical    : Number of technical questions to generate
        num_behavioral   : Number of behavioral questions to generate

        Returns
        -------
        Full session dict with questions, strategy, and tips.
        """
        session_id = str(uuid.uuid4())[:8]
        created_at = datetime.utcnow().isoformat() + "Z"

        # Normalise experience level
        experience_level = experience_level.lower().strip()
        if experience_level not in self.SUPPORTED_LEVELS:
            experience_level = self._infer_experience_level(experience_level)

        # Parse resume text if provided but skills not given
        if resume_text and not skills:
            profile = self.resume_parser.parse_text(resume_text)
            skills = profile.get("skills", [])
            # If experience years found in resume, let it override
            exp_years = profile.get("experience_years")
            if exp_years is not None:
                experience_level = self._years_to_level(exp_years)

        logger.info(
            "[%s] Starting session – %s | %s | %s",
            session_id, name, role, experience_level,
        )

        # Generate the question set
        try:
            result = self.question_generator.generate_question_set(
                name=name,
                role=role,
                experience_level=experience_level,
                skills=skills,
                num_technical=num_technical,
                num_behavioral=num_behavioral,
            )
        except Exception as exc:
            logger.error("LLM generation failed, using RAG-only fallback: %s", exc)
            result = self._rag_only_session(name, role, experience_level, skills, num_technical, num_behavioral)

        result["session_id"] = session_id
        result["created_at"] = created_at
        return result

    def start_session_from_resume(
        self,
        file_path: str,
        role: str,
        experience_level: str,
        num_technical: int = 5,
        num_behavioral: int = 3,
    ) -> dict:
        """
        Start a session by parsing a resume file first.

        Parameters
        ----------
        file_path        : Path to the uploaded resume (PDF/DOCX/TXT)
        role             : Target job role
        experience_level : Experience level override
        """
        profile = self.resume_parser.parse_file(file_path)
        name = profile.get("name", "Candidate")
        skills = profile.get("skills", [])

        # Override experience level from resume if detected
        exp_years = profile.get("experience_years")
        if exp_years is not None:
            experience_level = self._years_to_level(exp_years)

        # Index resume in RAG for personalised context
        self.rag.add_custom_document(
            text=profile["raw_text"],
            metadata={"type": "resume", "name": name, "role": role},
            doc_id=f"resume_{name.replace(' ', '_').lower()}",
        )

        session = self.start_session(
            name=name,
            role=role,
            experience_level=experience_level,
            skills=skills,
            resume_text=profile["raw_text"],
            num_technical=num_technical,
            num_behavioral=num_behavioral,
        )
        session["parsed_profile"] = {
            k: v for k, v in profile.items() if k != "raw_text"
        }
        return session

    def get_model_answer(
        self,
        question: str,
        role: str,
        experience_level: str,
        skills: Optional[list[str]] = None,
    ) -> dict:
        """
        Get a model answer for a specific interview question.

        Returns
        -------
        {"question": str, "model_answer": str, "tips": list[str]}
        """
        try:
            answer = self.question_generator.generate_model_answer(
                question=question,
                role=role,
                experience_level=experience_level,
                skills=skills,
            )
        except Exception as exc:
            logger.error("Model answer generation failed: %s", exc)
            level_info = EXPERIENCE_LEVELS.get(experience_level, EXPERIENCE_LEVELS["junior"])
            answer = QuestionGenerator._fallback_model_answer(question, role, level_info)

        # Pull relevant HR tips from RAG
        hr_docs = self.rag.query_hr_guidelines(question, top_k=2)
        tips = [doc["text"][:200] for doc in hr_docs]

        return {
            "question": question,
            "model_answer": answer,
            "tips": tips,
        }

    def get_available_roles(self) -> list[str]:
        """Return all roles available in the knowledge base."""
        from src.knowledge_base import TECHNICAL_QUESTIONS
        return list(TECHNICAL_QUESTIONS.keys())

    def get_available_levels(self) -> list[dict]:
        """Return all experience levels."""
        return [
            {"key": k, "label": v["label"]}
            for k, v in EXPERIENCE_LEVELS.items()
        ]

    # ------------------------------------------------------------------
    # Fallback helpers
    # ------------------------------------------------------------------

    def _rag_only_session(
        self, name: str, role: str, experience_level: str,
        skills: Optional[list[str]], num_technical: int, num_behavioral: int,
    ) -> dict:
        """Pure RAG fallback when LLM is unavailable."""
        norm_role = normalise_role(role)
        skills_str = ", ".join(skills[:8]) if skills else "general"
        level_info = EXPERIENCE_LEVELS.get(experience_level, EXPERIENCE_LEVELS["junior"])

        tech_docs = self.rag.query_technical(
            f"{role} {skills_str}", role=norm_role, top_k=num_technical
        )
        behav_docs = self.rag.query_behavioral(
            f"{level_info['focus']} behavioral", top_k=num_behavioral
        )

        from src.question_generator import QuestionGenerator as QG
        return {
            "profile": {
                "name": name, "role": role,
                "normalised_role": norm_role,
                "experience_level": level_info["label"],
                "skills": skills or [],
            },
            "technical_questions": [
                {"question": d["text"], "type": "technical",
                 "topic": d["metadata"].get("topic", ""), "source": "knowledge_base"}
                for d in tech_docs
            ],
            "behavioral_questions": [
                {"question": d["text"], "type": "behavioral",
                 "category": d["metadata"].get("category", ""),
                 "framework": d["metadata"].get("framework", "STAR"),
                 "tip": d["metadata"].get("tip", ""), "source": "knowledge_base"}
                for d in behav_docs
            ],
            "preparation_strategy": QG._fallback_preparation_strategy(role, level_info),
            "improvement_tips": QG._fallback_improvement_tips(level_info),
        }

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _years_to_level(years: int) -> str:
        if years == 0:
            return "fresher"
        if years <= 3:
            return "junior"
        if years <= 6:
            return "mid"
        if years <= 10:
            return "senior"
        return "lead"

    @staticmethod
    def _infer_experience_level(raw: str) -> str:
        """Map free-text experience descriptions to standard levels."""
        raw = raw.lower()
        if any(w in raw for w in ["fresh", "entry", "graduate", "0", "intern"]):
            return "fresher"
        if any(w in raw for w in ["junior", "1", "2", "3"]):
            return "junior"
        if any(w in raw for w in ["mid", "3", "4", "5", "6"]):
            return "mid"
        if any(w in raw for w in ["senior", "7", "8", "9", "10"]):
            return "senior"
        if any(w in raw for w in ["lead", "principal", "staff", "director"]):
            return "lead"
        return "junior"
