"""
resume_parser.py
----------------
Parses uploaded resumes (PDF / DOCX / plain text) and extracts
structured profile information for personalised interview prep.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ResumeParser:
    """
    Extracts profile information from a resume file or raw text.

    Supported formats: PDF (.pdf), Word (.docx), plain text (.txt)
    """

    # Patterns for extracting basic profile info
    _EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    _PHONE_RE = re.compile(r"[\+\(]?[0-9][0-9 \-\(\)]{7,}[0-9]")
    _LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)
    _GITHUB_RE = re.compile(r"github\.com/[\w\-]+", re.IGNORECASE)
    _YEARS_RE = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)", re.IGNORECASE)

    SECTION_KEYWORDS = {
        "skills": ["skills", "technical skills", "core competencies", "technologies"],
        "experience": ["experience", "work experience", "employment", "professional experience"],
        "education": ["education", "academic background", "qualifications"],
        "projects": ["projects", "personal projects", "key projects"],
        "certifications": ["certifications", "certificates", "credentials"],
        "summary": ["summary", "profile", "objective", "about me"],
    }

    def parse_file(self, file_path: str) -> dict:
        """
        Parse a resume file and return a structured profile dict.

        Parameters
        ----------
        file_path : Absolute or relative path to the resume file.

        Returns
        -------
        dict with keys: raw_text, name, email, phone, skills,
                         experience_years, education, summary, sections
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            text = self._extract_pdf(file_path)
        elif suffix == ".docx":
            text = self._extract_docx(file_path)
        elif suffix in (".txt", ".md"):
            text = path.read_text(encoding="utf-8", errors="ignore")
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        return self.parse_text(text)

    def parse_text(self, text: str) -> dict:
        """Parse raw resume text into a structured profile dict."""
        profile = {
            "raw_text": text,
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "linkedin": self._extract_linkedin(text),
            "github": self._extract_github(text),
            "experience_years": self._extract_experience_years(text),
            "skills": self._extract_skills(text),
            "summary": self._extract_section(text, "summary"),
            "experience": self._extract_section(text, "experience"),
            "education": self._extract_section(text, "education"),
            "projects": self._extract_section(text, "projects"),
            "certifications": self._extract_section(text, "certifications"),
        }
        logger.info(
            "Parsed resume – name: %s, exp: %s yrs, skills: %d",
            profile["name"],
            profile["experience_years"],
            len(profile["skills"]),
        )
        return profile

    # ------------------------------------------------------------------
    # File extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_pdf(file_path: str) -> str:
        """Extract text from a PDF using PyPDF2."""
        try:
            import PyPDF2
            text_parts = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            logger.warning("PyPDF2 not installed. Install it: pip install PyPDF2")
            return ""
        except Exception as exc:
            logger.error("PDF extraction failed: %s", exc)
            return ""

    @staticmethod
    def _extract_docx(file_path: str) -> str:
        """Extract text from a DOCX file using python-docx."""
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs)
        except ImportError:
            logger.warning("python-docx not installed. Install it: pip install python-docx")
            return ""
        except Exception as exc:
            logger.error("DOCX extraction failed: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Information extractors
    # ------------------------------------------------------------------

    def _extract_name(self, text: str) -> str:
        """Attempt to extract the candidate's name from the first two lines."""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:4]:
            # Name is usually a short line without special characters
            if len(line.split()) in (2, 3) and not any(c in line for c in ["@", ":", "/"]):
                if not any(kw in line.lower() for kw in ["resume", "cv", "curriculum"]):
                    return line.title()
        return "Unknown"

    def _extract_email(self, text: str) -> str:
        match = self._EMAIL_RE.search(text)
        return match.group() if match else ""

    def _extract_phone(self, text: str) -> str:
        match = self._PHONE_RE.search(text)
        return match.group() if match else ""

    def _extract_linkedin(self, text: str) -> str:
        match = self._LINKEDIN_RE.search(text)
        return match.group() if match else ""

    def _extract_github(self, text: str) -> str:
        match = self._GITHUB_RE.search(text)
        return match.group() if match else ""

    def _extract_experience_years(self, text: str) -> Optional[int]:
        """Extract years of experience if explicitly mentioned."""
        match = self._YEARS_RE.search(text)
        return int(match.group(1)) if match else None

    def _extract_skills(self, text: str) -> list[str]:
        """Extract a deduplicated list of technical skills."""
        skills_section = self._extract_section(text, "skills")
        if not skills_section:
            return []

        # Split on common delimiters
        raw = re.split(r"[,\|\n•\-\*·]", skills_section)
        skills = []
        for item in raw:
            item = item.strip()
            if 2 < len(item) < 50 and item:
                skills.append(item)
        return list(dict.fromkeys(skills))  # deduplicate preserving order

    def _extract_section(self, text: str, section_key: str) -> str:
        """Extract text content for a named section from the resume."""
        keywords = self.SECTION_KEYWORDS.get(section_key, [])
        lines = text.split("\n")
        capturing = False
        collected = []

        for i, line in enumerate(lines):
            stripped = line.strip().lower()
            # Check if this line is the section header
            if any(stripped == kw or stripped.startswith(kw + ":") for kw in keywords):
                capturing = True
                continue
            # Stop when we hit another known section
            if capturing:
                is_new_section = False
                for other_key, other_kws in self.SECTION_KEYWORDS.items():
                    if other_key == section_key:
                        continue
                    if any(stripped == kw or stripped.startswith(kw + ":") for kw in other_kws):
                        is_new_section = True
                        break
                if is_new_section:
                    break
                collected.append(line)

        return "\n".join(collected).strip()
