"""
question_generator.py
---------------------
Generates personalised interview question sets using IBM Granite
and the RAG-retrieved context. Covers both technical and behavioral
questions, tailored by role and experience level.
"""

import logging
from typing import Optional

from src.granite_llm import GraniteLLM, get_llm
from src.rag_engine import RAGEngine, get_rag_engine
from src.knowledge_base import EXPERIENCE_LEVELS, normalise_role

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """
    Generates tailored interview question sets using RAG + Granite.
    """

    def __init__(
        self,
        llm: Optional[GraniteLLM] = None,
        rag: Optional[RAGEngine] = None,
    ):
        self.llm = llm or get_llm()
        self.rag = rag or get_rag_engine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_question_set(
        self,
        name: str,
        role: str,
        experience_level: str,
        skills: Optional[list[str]] = None,
        num_technical: int = 5,
        num_behavioral: int = 3,
    ) -> dict:
        """
        Generate a complete personalised interview question set.

        Returns
        -------
        {
            "profile": {...},
            "technical_questions": [...],
            "behavioral_questions": [...],
            "preparation_strategy": str,
            "improvement_tips": str,
        }
        """
        norm_role = normalise_role(role)
        level_info = EXPERIENCE_LEVELS.get(experience_level, EXPERIENCE_LEVELS["junior"])
        skills_str = ", ".join(skills[:10]) if skills else "general programming"

        logger.info(
            "Generating question set for %s | role=%s | level=%s",
            name, norm_role, experience_level,
        )

        # 1. RAG retrieval
        tech_docs = self.rag.query_technical(
            query=f"{role} {skills_str} {level_info['focus']}",
            role=norm_role,
            top_k=num_technical + 3,
        )
        behav_docs = self.rag.query_behavioral(
            query=f"{level_info['focus']} behavioral interview",
            top_k=num_behavioral + 2,
        )

        # 2. LLM-enhanced question generation
        technical_questions = self._generate_technical_questions(
            name=name,
            role=role,
            level_info=level_info,
            skills=skills_str,
            retrieved_docs=tech_docs,
            count=num_technical,
        )

        behavioral_questions = self._generate_behavioral_questions(
            name=name,
            role=role,
            level_info=level_info,
            retrieved_docs=behav_docs,
            count=num_behavioral,
        )

        # 3. Preparation strategy
        prep_strategy = self._generate_preparation_strategy(
            name=name,
            role=role,
            level_info=level_info,
            skills=skills_str,
        )

        # 4. Improvement tips
        improvement_tips = self._generate_improvement_tips(
            role=role,
            level_info=level_info,
            skills=skills_str,
        )

        return {
            "profile": {
                "name": name,
                "role": role,
                "normalised_role": norm_role,
                "experience_level": level_info["label"],
                "skills": skills or [],
            },
            "technical_questions": technical_questions,
            "behavioral_questions": behavioral_questions,
            "preparation_strategy": prep_strategy,
            "improvement_tips": improvement_tips,
        }

    def generate_model_answer(
        self,
        question: str,
        role: str,
        experience_level: str,
        skills: Optional[list[str]] = None,
    ) -> str:
        """
        Generate a model (sample) answer for a specific interview question.
        """
        level_info = EXPERIENCE_LEVELS.get(experience_level, EXPERIENCE_LEVELS["junior"])
        skills_str = ", ".join(skills[:6]) if skills else "relevant technologies"

        # Retrieve supporting context from RAG
        tech_context = self.rag.query_technical(f"{question} {role}", top_k=2)
        hr_context = self.rag.query_hr_guidelines(question, top_k=1)

        context_parts = [doc["text"] for doc in tech_context + hr_context]
        context_str = "\n".join(context_parts[:3]) if context_parts else ""

        prompt = f"""You are an expert career coach preparing a {level_info['label']} {role} candidate for a job interview.

Context from knowledge base:
{context_str}

Candidate skills: {skills_str}
Experience depth expected: {level_info['expected_depth']}

Provide a strong, concise model answer for the following interview question. Use the STAR method where applicable. Include specific technical details where relevant. Keep the answer between 150-250 words.

Interview Question: {question}

Model Answer:"""

        try:
            return self.llm.generate(prompt, max_tokens=400)
        except Exception as exc:
            logger.error("Failed to generate model answer: %s", exc)
            return self._fallback_model_answer(question, role, level_info)

    # ------------------------------------------------------------------
    # Internal generation helpers
    # ------------------------------------------------------------------

    def _generate_technical_questions(
        self,
        name: str,
        role: str,
        level_info: dict,
        skills: str,
        retrieved_docs: list[dict],
        count: int,
    ) -> list[dict]:
        """Use Granite to generate or enhance technical questions from RAG context."""
        retrieved_qs = "\n".join(
            f"- {doc['text']} (Topic: {doc['metadata'].get('topic', 'General')})"
            for doc in retrieved_docs[:count + 2]
        )

        prompt = f"""You are an expert technical interviewer at a top tech company.

Candidate: {name}
Role: {role}
Experience Level: {level_info['label']}
Skills: {skills}
Focus Areas: {level_info['focus']}

Sample questions from knowledge base:
{retrieved_qs}

Generate exactly {count} targeted technical interview questions for this candidate. Each question should:
- Be specific to their experience level ({level_info['question_depth']}-level)
- Be directly relevant to the role and skills listed
- Include a mix of conceptual, practical, and scenario-based questions

Format your response as a numbered list (1. Question text):"""

        try:
            raw = self.llm.generate(prompt, max_tokens=600)
            questions = self._parse_numbered_list(raw, count)
            if len(questions) >= count:
                return [{"question": q, "type": "technical", "source": "ai_generated"}
                        for q in questions[:count]]
        except Exception as exc:
            logger.warning("LLM generation failed, using RAG questions: %s", exc)

        # Fallback to RAG-only questions
        return [
            {
                "question": doc["text"],
                "type": "technical",
                "topic": doc["metadata"].get("topic", "General"),
                "source": "knowledge_base",
            }
            for doc in retrieved_docs[:count]
        ]

    def _generate_behavioral_questions(
        self,
        name: str,
        role: str,
        level_info: dict,
        retrieved_docs: list[dict],
        count: int,
    ) -> list[dict]:
        """Generate behavioral questions using RAG context and Granite."""
        retrieved_qs = "\n".join(
            f"- {doc['text']} (Category: {doc['metadata'].get('category', 'General')}, "
            f"Framework: {doc['metadata'].get('framework', 'STAR')})"
            for doc in retrieved_docs[:count + 2]
        )

        prompt = f"""You are an HR expert conducting behavioral interviews.

Candidate: {name}
Role: {role}
Experience Level: {level_info['label']}
Focus: {level_info['focus']}

Sample behavioral questions:
{retrieved_qs}

Generate exactly {count} behavioral interview questions tailored for a {level_info['label']} {role}. Include a mix of questions about teamwork, leadership, conflict resolution, and problem-solving. Use the STAR framework.

Format as a numbered list (1. Question text):"""

        try:
            raw = self.llm.generate(prompt, max_tokens=400)
            questions = self._parse_numbered_list(raw, count)
            if len(questions) >= count:
                return [{"question": q, "type": "behavioral", "framework": "STAR", "source": "ai_generated"}
                        for q in questions[:count]]
        except Exception as exc:
            logger.warning("LLM behavioral generation failed, using RAG questions: %s", exc)

        return [
            {
                "question": doc["text"],
                "type": "behavioral",
                "category": doc["metadata"].get("category", "General"),
                "framework": doc["metadata"].get("framework", "STAR"),
                "tip": doc["metadata"].get("tip", ""),
                "source": "knowledge_base",
            }
            for doc in retrieved_docs[:count]
        ]

    def _generate_preparation_strategy(
        self, name: str, role: str, level_info: dict, skills: str
    ) -> str:
        """Generate a personalised 2-week interview preparation strategy."""
        hr_docs = self.rag.query_hr_guidelines("preparation strategy interview tips", top_k=2)
        hr_context = "\n".join(doc["text"] for doc in hr_docs)

        prompt = f"""You are an expert career coach.

Candidate: {name}
Role: {role}
Experience Level: {level_info['label']}
Skills: {skills}

HR Guidelines:
{hr_context}

Create a concise, personalised 2-week interview preparation strategy for {name}. Include:
1. Week 1: Core technical preparation areas
2. Week 2: Behavioral prep and company research
3. Day-of interview tips
4. Resources to study

Keep it practical and actionable. Max 300 words."""

        try:
            return self.llm.generate(prompt, max_tokens=500)
        except Exception as exc:
            logger.error("Failed to generate prep strategy: %s", exc)
            return self._fallback_preparation_strategy(role, level_info)

    def _generate_improvement_tips(
        self, role: str, level_info: dict, skills: str
    ) -> str:
        """Generate targeted improvement tips for the candidate."""
        prompt = f"""You are an expert technical recruiter.

Role: {role}
Experience Level: {level_info['label']}
Current Skills: {skills}
Expected Depth: {level_info['expected_depth']}

Provide 5 specific, actionable improvement tips for a {level_info['label']} {role} candidate to maximise their interview success. Focus on skill gaps, communication, and preparation quality.

Format as a numbered list:"""

        try:
            return self.llm.generate(prompt, max_tokens=400)
        except Exception as exc:
            logger.error("Failed to generate improvement tips: %s", exc)
            return self._fallback_improvement_tips(level_info)

    # ------------------------------------------------------------------
    # Fallback methods (used when LLM is unavailable)
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_model_answer(question: str, role: str, level_info: dict) -> str:
        return (
            f"[Model Answer – IBM Granite unavailable]\n\n"
            f"For a {level_info['label']} {role}, a strong answer to '{question}' would:\n"
            f"• Use the STAR framework (Situation, Task, Action, Result)\n"
            f"• Demonstrate {level_info['expected_depth']}\n"
            f"• Include specific, quantified examples from your experience\n"
            f"• Be 90–120 seconds when spoken aloud"
        )

    @staticmethod
    def _fallback_preparation_strategy(role: str, level_info: dict) -> str:
        return (
            f"2-Week Preparation Plan for {level_info['label']} {role}:\n\n"
            f"Week 1 – Technical Foundation:\n"
            f"• Days 1-2: Review core {role} concepts and fundamentals\n"
            f"• Days 3-4: Practice coding / hands-on exercises\n"
            f"• Days 5-7: Mock technical interviews\n\n"
            f"Week 2 – Behavioral & Final Prep:\n"
            f"• Days 8-9: Prepare STAR stories for 5 key behavioral questions\n"
            f"• Days 10-11: Research the company, products, and culture\n"
            f"• Days 12-13: Mock full interviews with a friend\n"
            f"• Day 14: Rest, review notes, prepare questions to ask\n\n"
            f"Day-of Tips:\n"
            f"• Arrive/log in 10 minutes early\n"
            f"• Bring copies of your resume\n"
            f"• Prepare 3 thoughtful questions for the interviewer"
        )

    @staticmethod
    def _fallback_improvement_tips(level_info: dict) -> str:
        return (
            f"Top 5 Improvement Tips for {level_info['label']} Candidates:\n\n"
            f"1. Practice explaining concepts aloud – communication matters as much as knowledge\n"
            f"2. Build and document 2-3 strong portfolio projects\n"
            f"3. Use the STAR framework for every behavioral question\n"
            f"4. Research the company's tech stack and recent news\n"
            f"5. Track your mock interview performance and iterate"
        )

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_numbered_list(text: str, expected: int) -> list[str]:
        """Parse a numbered list from LLM output."""
        import re
        lines = text.strip().split("\n")
        questions = []
        pattern = re.compile(r"^\s*\d+[\.\)]\s*(.+)")
        for line in lines:
            m = pattern.match(line)
            if m:
                q = m.group(1).strip()
                if len(q) > 10:
                    questions.append(q)
        return questions
