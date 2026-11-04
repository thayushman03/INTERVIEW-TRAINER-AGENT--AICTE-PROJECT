# 🎯 IBM Interview Trainer Agent
### AICTE IBM Project – Problem Statement #22

> **An AI-powered Interview Trainer** built with IBM Granite LLM and Retrieval-Augmented Generation (RAG) that prepares candidates for job interviews through tailored question sets, model answers, and personalised preparation strategies.

---

## 📋 Table of Contents
- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration (.env)](#configuration-env)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [How It Works](#how-it-works)
- [Features](#features)
- [Supported Roles](#supported-roles)

---

## Overview

The Interview Trainer Agent helps candidates prepare for technical and behavioral job interviews by:

1. **Accepting a user profile** — name, role, experience level, and skills (or a resume file)
2. **Retrieving relevant context** via RAG from a curated knowledge base (interview questions, HR guidelines, industry expectations)
3. **Generating personalised content** using IBM Granite LLM:
   - Tailored technical question sets
   - Behavioural scenarios with STAR framework guidance
   - Model answers with improvement tips
   - 2-week preparation strategies

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **LLM** | IBM Granite 13B Chat v2 / Granite 3.8B Instruct |
| **LLM API** | IBM WatsonX.ai (`ibm-watsonx-ai` SDK) |
| **Vector Store** | ChromaDB (persistent, local) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| **RAG Framework** | Custom pipeline (LangChain-compatible) |
| **Web Framework** | Flask + Flask-CORS |
| **Resume Parsing** | PyPDF2, python-docx |
| **CLI** | Rich (interactive terminal UI) |
| **Frontend** | Vanilla HTML/CSS/JS (served by Flask) |

---

## Project Structure

```
interview-trainer-agent/
│
├── app.py                   # Flask REST API server
├── cli.py                   # Interactive CLI interface
├── requirements.txt         # Python dependencies
├── env.example              # Environment variable template
│
├── src/
│   ├── __init__.py
│   ├── config.py            # Centralised configuration loader
│   ├── granite_llm.py       # IBM Granite LLM wrapper
│   ├── rag_engine.py        # RAG pipeline (ChromaDB + embeddings)
│   ├── knowledge_base.py    # Curated interview questions & guidelines
│   ├── resume_parser.py     # PDF/DOCX/TXT resume parser
│   ├── question_generator.py# Question + answer generation
│   ├── agent.py             # Main orchestrator
│   └── utils.py             # Logging & formatting utilities
│
├── templates/
│   └── index.html           # Web UI
│
├── static/
│   ├── css/style.css        # Stylesheet
│   └── js/app.js            # Frontend JavaScript
│
├── data/
│   ├── chroma_db/           # ChromaDB vector store (auto-created)
│   └── uploads/             # Temporary resume uploads (auto-created)
│
└── logs/
    └── interview_trainer.log # Application logs (auto-created)
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- IBM Cloud account (free Lite tier works)
- IBM WatsonX.ai project

### Step 1 – Clone and create a virtual environment
```bash
git clone <repo-url>
cd interview-trainer-agent
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 2 – Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 – Configure environment variables
```bash
# Copy the template
cp env.example .env   # Linux/macOS
copy env.example .env  # Windows

# Edit .env and fill in your credentials
```

---

## Configuration (.env)

```env
# ── REQUIRED ──────────────────────────────────────────────────────
IBM_CLOUD_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# ── IBM Granite Models ─────────────────────────────────────────────
GRANITE_MODEL_ID=ibm/granite-13b-chat-v2
GRANITE_INSTRUCT_MODEL_ID=ibm/granite-3-8b-instruct

# ── RAG Configuration ──────────────────────────────────────────────
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_TOP_K=5

# ── Application ────────────────────────────────────────────────────
FLASK_PORT=5000
LLM_TEMPERATURE=0.7
LLM_MAX_NEW_TOKENS=800
```

### How to get your IBM credentials

1. **IBM Cloud API Key**  
   → [https://cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys)  
   → Click **Create an IBM Cloud API key**

2. **WatsonX Project ID**  
   → Go to [https://dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)  
   → Create or open a project → **Manage** tab → Copy the Project ID

3. **WatsonX URL**  
   → Use the region closest to you:  
   - `https://us-south.ml.cloud.ibm.com` (Dallas)  
   - `https://eu-de.ml.cloud.ibm.com` (Frankfurt)  
   - `https://jp-tok.ml.cloud.ibm.com` (Tokyo)

---

## Running the Application

### Option A – Web Interface (Flask)
```bash
python app.py
```
Then open **http://localhost:5000** in your browser.

### Option B – Interactive CLI
```bash
python cli.py
```

### Option C – CLI with arguments (non-interactive)
```bash
# By profile
python cli.py --name "Alice" --role "Data Scientist" --level mid --skills "Python,scikit-learn,SQL"

# From resume file
python cli.py --resume ./my_resume.pdf --role "Software Engineer" --level junior
```

---

## API Reference

### `GET /api/health`
Health check.

### `GET /api/roles`
Returns available job roles.

### `GET /api/levels`
Returns available experience levels.

### `POST /api/session/start`
Start a session from a profile.

**Request Body:**
```json
{
  "name": "Alice",
  "role": "software_engineer",
  "experience_level": "mid",
  "skills": ["Python", "Django", "PostgreSQL"],
  "num_technical": 5,
  "num_behavioral": 3
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "a1b2c3d4",
    "profile": { ... },
    "technical_questions": [ { "question": "...", "type": "technical", ... } ],
    "behavioral_questions": [ { "question": "...", "framework": "STAR", ... } ],
    "preparation_strategy": "...",
    "improvement_tips": "..."
  }
}
```

### `POST /api/session/resume`
Start a session from an uploaded resume.

**Form Data:**
- `file`: Resume file (PDF/DOCX/TXT)
- `role`: Target job role
- `experience_level`: Experience level

### `POST /api/model-answer`
Get a model answer for a specific question.

**Request Body:**
```json
{
  "question": "What is the bias-variance tradeoff?",
  "role": "data_scientist",
  "experience_level": "mid",
  "skills": ["Python", "scikit-learn"]
}
```

---

## How It Works

```
User Input (Profile / Resume)
        │
        ▼
┌─────────────────────┐
│   Resume Parser      │  ← Extracts name, skills, experience from PDF/DOCX/TXT
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│    RAG Engine        │  ← ChromaDB + sentence-transformers embeddings
│                      │     Retrieves:
│  • Technical Qs      │     - Role-specific technical questions
│  • Behavioral Qs     │     - Behavioral scenarios
│  • HR Guidelines     │     - Interview tips & guidelines
└─────────┬───────────┘
          │ Retrieved Context
          ▼
┌─────────────────────┐
│  IBM Granite LLM     │  ← ibm-watsonx-ai SDK → WatsonX.ai
│  (granite-13b-chat)  │     Generates:
│                      │     - Personalised questions
│                      │     - Model answers
│                      │     - Preparation strategy
│                      │     - Improvement tips
└─────────┬───────────┘
          │
          ▼
     Session Output
  (Web UI / CLI / JSON)
```

---

## Features

| Feature | Description |
|---------|-------------|
| 🎯 **Personalised Questions** | Questions tailored to role, level, and skills |
| 📄 **Resume Upload** | Parse PDF/DOCX/TXT to auto-fill profile |
| 🤖 **IBM Granite LLM** | AI-generated questions and model answers |
| 🔍 **RAG Pipeline** | Semantic retrieval from curated knowledge base |
| 💬 **STAR Framework** | Behavioral questions with STAR-guided tips |
| 📅 **Prep Strategy** | 2-week personalised preparation plan |
| 🌐 **Web Interface** | Clean responsive UI served by Flask |
| 💻 **Rich CLI** | Coloured interactive terminal interface |
| 🔄 **Fallback Mode** | Works without LLM (RAG-only) if credentials missing |
| 📊 **Multi-level Support** | Fresher through Lead/Principal levels |

---

## Supported Roles

| Role Key | Display Name |
|----------|-------------|
| `software_engineer` | Software Engineer |
| `data_scientist` | Data Scientist / ML Engineer |
| `frontend_developer` | Frontend Developer |
| `backend_developer` | Backend Developer |
| `devops_engineer` | DevOps / SRE Engineer |
| `product_manager` | Product Manager |

---

## Experience Levels

| Level | Range | Focus |
|-------|-------|-------|
| `fresher` | 0–1 years | Fundamentals, projects, conceptual |
| `junior` | 1–3 years | Practical, code quality, tools |
| `mid` | 3–6 years | System design, ownership |
| `senior` | 6–10 years | Architecture, leadership |
| `lead` | 10+ years | Strategy, org-wide impact |

---

## License

This project is developed for the **AICTE IBM Skills Build** programme.  
Uses IBM Cloud Lite / WatsonX.ai free tier services.

---

*Built with ❤️ using IBM Granite LLM, RAG, and ChromaDB*
