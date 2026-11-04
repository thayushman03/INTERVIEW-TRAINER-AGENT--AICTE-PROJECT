"""
test_agent.py
-------------
Unit and integration tests for the Interview Trainer Agent.
Tests that do NOT require IBM Cloud credentials are run with the
fallback/RAG-only path.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Make sure src/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestConfig(unittest.TestCase):
    """Test configuration loading."""

    def test_validate_config_flags_missing_keys(self):
        from src.config import validate_config
        missing = validate_config()
        # In CI without real keys, both should be missing
        self.assertIsInstance(missing, list)

    def test_config_has_required_attributes(self):
        import src.config as cfg
        self.assertTrue(hasattr(cfg, "GRANITE_MODEL_ID"))
        self.assertTrue(hasattr(cfg, "WATSONX_URL"))
        self.assertTrue(hasattr(cfg, "RAG_TOP_K"))
        self.assertIsInstance(cfg.RAG_TOP_K, int)
        self.assertIsInstance(cfg.LLM_TEMPERATURE, float)


class TestKnowledgeBase(unittest.TestCase):
    """Test the curated knowledge base."""

    def test_technical_questions_not_empty(self):
        from src.knowledge_base import TECHNICAL_QUESTIONS
        self.assertGreater(len(TECHNICAL_QUESTIONS), 0)
        for role, questions in TECHNICAL_QUESTIONS.items():
            self.assertIsInstance(questions, list)
            self.assertGreater(len(questions), 0)
            for q in questions:
                self.assertIn("q", q)
                self.assertIn("topic", q)

    def test_behavioral_questions_not_empty(self):
        from src.knowledge_base import BEHAVIORAL_QUESTIONS
        self.assertGreater(len(BEHAVIORAL_QUESTIONS), 5)
        for q in BEHAVIORAL_QUESTIONS:
            self.assertIn("q", q)
            self.assertIn("framework", q)

    def test_hr_guidelines_not_empty(self):
        from src.knowledge_base import HR_GUIDELINES
        self.assertGreater(len(HR_GUIDELINES), 0)

    def test_normalise_role(self):
        from src.knowledge_base import normalise_role
        self.assertEqual(normalise_role("Software Engineer"), "software_engineer")
        self.assertEqual(normalise_role("data scientist"), "data_scientist")
        self.assertEqual(normalise_role("frontend"), "frontend_developer")
        self.assertEqual(normalise_role("PM"), "product_manager")

    def test_experience_levels_complete(self):
        from src.knowledge_base import EXPERIENCE_LEVELS
        expected_levels = {"fresher", "junior", "mid", "senior", "lead"}
        self.assertEqual(set(EXPERIENCE_LEVELS.keys()), expected_levels)


class TestResumeParser(unittest.TestCase):
    """Test resume parsing logic."""

    def setUp(self):
        from src.resume_parser import ResumeParser
        self.parser = ResumeParser()

    def test_parse_email(self):
        text = "Alice Johnson\nalice.johnson@example.com\n+1-555-0100"
        profile = self.parser.parse_text(text)
        self.assertEqual(profile["email"], "alice.johnson@example.com")

    def test_parse_phone(self):
        text = "Bob Smith\nbob@test.com\n+44 7700 900123"
        profile = self.parser.parse_text(text)
        self.assertIn("7700", profile["phone"])

    def test_extract_skills(self):
        text = (
            "Alice Johnson\nalice@example.com\n\n"
            "Skills\nPython, Django, PostgreSQL, Docker, Redis\n\n"
            "Experience\n3 years of experience at Acme Corp"
        )
        profile = self.parser.parse_text(text)
        self.assertIn("Python", profile["skills"])
        self.assertIn("Docker", profile["skills"])

    def test_extract_experience_years(self):
        text = "John Doe\njohn@test.com\n5 years of experience in software development"
        profile = self.parser.parse_text(text)
        self.assertEqual(profile["experience_years"], 5)

    def test_name_extraction(self):
        text = "Alice Johnson\nalice@example.com"
        profile = self.parser.parse_text(text)
        self.assertEqual(profile["name"], "Alice Johnson")

    def test_parse_text_returns_required_keys(self):
        required_keys = ["raw_text", "name", "email", "phone", "skills",
                         "experience_years", "summary", "experience", "education"]
        profile = self.parser.parse_text("John Doe\njohn@example.com")
        for key in required_keys:
            self.assertIn(key, profile, f"Missing key: {key}")


class TestAgentFallback(unittest.TestCase):
    """Test agent in fallback mode (no LLM credentials)."""

    def setUp(self):
        # Patch validate_config to simulate missing credentials
        with patch("src.agent.validate_config", return_value=["IBM_CLOUD_API_KEY"]):
            from src.agent import InterviewTrainerAgent
            self.agent = InterviewTrainerAgent.__new__(InterviewTrainerAgent)
            self.agent._llm_available = False
            self.agent._question_gen = None

        from src.rag_engine import RAGEngine
        from src.resume_parser import ResumeParser
        self.agent.resume_parser = ResumeParser()
        # Use a temp directory for ChromaDB
        import tempfile
        tmp = tempfile.mkdtemp()
        self.agent.rag = RAGEngine(persist_dir=tmp)

    def test_years_to_level(self):
        from src.agent import InterviewTrainerAgent
        self.assertEqual(InterviewTrainerAgent._years_to_level(0), "fresher")
        self.assertEqual(InterviewTrainerAgent._years_to_level(2), "junior")
        self.assertEqual(InterviewTrainerAgent._years_to_level(5), "mid")
        self.assertEqual(InterviewTrainerAgent._years_to_level(8), "senior")
        self.assertEqual(InterviewTrainerAgent._years_to_level(15), "lead")

    def test_infer_experience_level(self):
        from src.agent import InterviewTrainerAgent
        self.assertEqual(InterviewTrainerAgent._infer_experience_level("fresher"), "fresher")
        self.assertEqual(InterviewTrainerAgent._infer_experience_level("senior engineer"), "senior")

    def test_rag_only_session_returns_valid_structure(self):
        session = self.agent._rag_only_session(
            name="Test User",
            role="Software Engineer",
            experience_level="junior",
            skills=["Python", "SQL"],
            num_technical=3,
            num_behavioral=2,
        )
        self.assertIn("profile", session)
        self.assertIn("technical_questions", session)
        self.assertIn("behavioral_questions", session)
        self.assertIn("preparation_strategy", session)
        self.assertIn("improvement_tips", session)
        self.assertGreaterEqual(len(session["technical_questions"]), 1)
        self.assertGreaterEqual(len(session["behavioral_questions"]), 1)

    def test_get_available_roles(self):
        roles = self.agent.get_available_roles()
        self.assertIn("software_engineer", roles)
        self.assertIn("data_scientist", roles)

    def test_get_available_levels(self):
        levels = self.agent.get_available_levels()
        level_keys = [l["key"] for l in levels]
        self.assertIn("junior", level_keys)
        self.assertIn("senior", level_keys)


class TestRAGEngine(unittest.TestCase):
    """Test RAG engine query functionality."""

    def setUp(self):
        import tempfile
        from src.rag_engine import RAGEngine
        tmp = tempfile.mkdtemp()
        self.rag = RAGEngine(persist_dir=tmp)

    def test_query_technical_returns_results(self):
        results = self.rag.query_technical("Python algorithms sorting", role="software_engineer", top_k=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("text", r)
            self.assertIn("metadata", r)
            self.assertIn("relevance_score", r)

    def test_query_behavioral_returns_results(self):
        results = self.rag.query_behavioral("teamwork conflict resolution", top_k=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_query_hr_guidelines_returns_results(self):
        results = self.rag.query_hr_guidelines("salary negotiation", top_k=2)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_relevance_scores_in_range(self):
        results = self.rag.query_technical("database indexing", top_k=3)
        for r in results:
            self.assertGreaterEqual(r["relevance_score"], 0.0)
            self.assertLessEqual(r["relevance_score"], 1.1)  # cosine can slightly exceed 1


class TestQuestionGeneratorFallbacks(unittest.TestCase):
    """Test question generator fallback methods (no LLM needed)."""

    def test_fallback_model_answer(self):
        from src.question_generator import QuestionGenerator
        from src.knowledge_base import EXPERIENCE_LEVELS
        level_info = EXPERIENCE_LEVELS["junior"]
        answer = QuestionGenerator._fallback_model_answer(
            "Tell me about yourself", "Software Engineer", level_info
        )
        self.assertIn("STAR", answer)
        self.assertGreater(len(answer), 50)

    def test_fallback_prep_strategy(self):
        from src.question_generator import QuestionGenerator
        from src.knowledge_base import EXPERIENCE_LEVELS
        strategy = QuestionGenerator._fallback_preparation_strategy(
            "Data Scientist", EXPERIENCE_LEVELS["mid"]
        )
        self.assertIn("Week", strategy)
        self.assertGreater(len(strategy), 100)

    def test_parse_numbered_list(self):
        from src.question_generator import QuestionGenerator
        text = "1. What is Python?\n2. Explain OOP.\n3. What is a REST API?"
        result = QuestionGenerator._parse_numbered_list(text, 3)
        self.assertEqual(len(result), 3)
        self.assertIn("Python", result[0])


class TestUtils(unittest.TestCase):
    """Test utility functions."""

    def test_format_session_report_contains_key_sections(self):
        from src.utils import format_session_report
        session = {
            "session_id": "abc123",
            "created_at": "2024-01-01T00:00:00Z",
            "profile": {
                "name": "Alice",
                "role": "Data Scientist",
                "experience_level": "Mid-Level (3–6 years)",
                "skills": ["Python", "TensorFlow"],
            },
            "technical_questions": [
                {"question": "What is overfitting?", "topic": "ML Theory"},
            ],
            "behavioral_questions": [
                {"question": "Tell me about yourself.", "framework": "Present-Past-Future", "tip": ""},
            ],
            "preparation_strategy": "Study hard.",
            "improvement_tips": "Practice daily.",
        }
        report = format_session_report(session)
        self.assertIn("Alice", report)
        self.assertIn("TECHNICAL QUESTIONS", report)
        self.assertIn("BEHAVIORAL QUESTIONS", report)
        self.assertIn("PREPARATION STRATEGY", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
