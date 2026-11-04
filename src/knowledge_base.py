"""
knowledge_base.py
-----------------
Curated interview knowledge base.
Provides role-specific questions, HR guidelines, and behavioral scenarios
that are loaded into the RAG vector store at startup.
"""

# ---------------------------------------------------------------------------
# Technical Interview Questions by Role
# ---------------------------------------------------------------------------

TECHNICAL_QUESTIONS: dict[str, list[dict]] = {
    "software_engineer": [
        {"q": "Explain the difference between a process and a thread.", "topic": "OS"},
        {"q": "What is Big-O notation? Give examples of O(1), O(n), O(n log n).", "topic": "Algorithms"},
        {"q": "Describe the SOLID principles with an example.", "topic": "OOP"},
        {"q": "What is a RESTful API? How does it differ from GraphQL?", "topic": "Web"},
        {"q": "Explain database indexing and when you would use it.", "topic": "Database"},
        {"q": "What is the difference between SQL and NoSQL databases?", "topic": "Database"},
        {"q": "Describe the MVC architecture pattern.", "topic": "Architecture"},
        {"q": "What is a design pattern? Describe Singleton and Factory patterns.", "topic": "Design Patterns"},
        {"q": "How does garbage collection work in Java/Python?", "topic": "Memory"},
        {"q": "Explain the concept of microservices and their advantages.", "topic": "Architecture"},
        {"q": "What is Docker and how does containerisation help in development?", "topic": "DevOps"},
        {"q": "Describe CI/CD pipelines and their importance.", "topic": "DevOps"},
        {"q": "What is a deadlock? How can it be prevented?", "topic": "Concurrency"},
        {"q": "Explain the differences between GET, POST, PUT, DELETE HTTP methods.", "topic": "Web"},
        {"q": "What is caching? Describe LRU cache.", "topic": "Performance"},
    ],
    "data_scientist": [
        {"q": "What is the bias-variance tradeoff?", "topic": "ML Theory"},
        {"q": "Explain overfitting and how to prevent it.", "topic": "ML Theory"},
        {"q": "What is the difference between supervised and unsupervised learning?", "topic": "ML Theory"},
        {"q": "Describe how gradient descent works.", "topic": "Optimization"},
        {"q": "What are precision, recall, and F1-score?", "topic": "Evaluation"},
        {"q": "Explain cross-validation and why it is used.", "topic": "Evaluation"},
        {"q": "What is regularisation (L1 vs L2)?", "topic": "ML Theory"},
        {"q": "How does a Random Forest algorithm work?", "topic": "Algorithms"},
        {"q": "Explain the difference between bagging and boosting.", "topic": "Algorithms"},
        {"q": "What is PCA and when would you use it?", "topic": "Dimensionality Reduction"},
        {"q": "How do you handle missing values in a dataset?", "topic": "Data Preprocessing"},
        {"q": "What is a confusion matrix?", "topic": "Evaluation"},
        {"q": "Describe the architecture of a neural network.", "topic": "Deep Learning"},
        {"q": "What is transfer learning?", "topic": "Deep Learning"},
        {"q": "How would you detect and handle outliers?", "topic": "Data Preprocessing"},
    ],
    "frontend_developer": [
        {"q": "What is the difference between == and === in JavaScript?", "topic": "JavaScript"},
        {"q": "Explain the concept of closures in JavaScript.", "topic": "JavaScript"},
        {"q": "What is the Virtual DOM? How does React use it?", "topic": "React"},
        {"q": "Explain CSS specificity.", "topic": "CSS"},
        {"q": "What is the Box Model in CSS?", "topic": "CSS"},
        {"q": "How does event bubbling and capturing work?", "topic": "DOM"},
        {"q": "What are React Hooks? Explain useState and useEffect.", "topic": "React"},
        {"q": "What is responsive design? How do media queries work?", "topic": "CSS"},
        {"q": "Explain the difference between localStorage, sessionStorage, and cookies.", "topic": "Web Storage"},
        {"q": "What is CORS and how do you handle it?", "topic": "Web Security"},
        {"q": "What is webpack and why is it used?", "topic": "Build Tools"},
        {"q": "Explain async/await and Promises in JavaScript.", "topic": "Async"},
        {"q": "What is TypeScript and how does it differ from JavaScript?", "topic": "TypeScript"},
        {"q": "Describe the Flux/Redux pattern for state management.", "topic": "State Management"},
        {"q": "What are Web Accessibility (a11y) best practices?", "topic": "Accessibility"},
    ],
    "backend_developer": [
        {"q": "What is the difference between authentication and authorisation?", "topic": "Security"},
        {"q": "Explain JWT tokens and how they work.", "topic": "Security"},
        {"q": "What is database normalisation? Explain 1NF, 2NF, 3NF.", "topic": "Database"},
        {"q": "How do you prevent SQL injection?", "topic": "Security"},
        {"q": "What is an ORM? What are its advantages and disadvantages?", "topic": "Database"},
        {"q": "Explain connection pooling.", "topic": "Database"},
        {"q": "What is message queuing? When would you use RabbitMQ/Kafka?", "topic": "Messaging"},
        {"q": "How do you design a rate limiter?", "topic": "System Design"},
        {"q": "What is the difference between synchronous and asynchronous programming?", "topic": "Async"},
        {"q": "Explain horizontal vs vertical scaling.", "topic": "Scalability"},
        {"q": "What is a reverse proxy? How does Nginx work?", "topic": "Infrastructure"},
        {"q": "Describe the CAP theorem.", "topic": "Distributed Systems"},
        {"q": "What is event-driven architecture?", "topic": "Architecture"},
        {"q": "How would you implement caching in a web application?", "topic": "Performance"},
        {"q": "Explain ACID properties of databases.", "topic": "Database"},
    ],
    "devops_engineer": [
        {"q": "What is Infrastructure as Code (IaC)? Name some tools.", "topic": "IaC"},
        {"q": "Explain the difference between Docker and Kubernetes.", "topic": "Containers"},
        {"q": "How does a Kubernetes Pod differ from a Deployment?", "topic": "Kubernetes"},
        {"q": "What is a rolling deployment vs blue-green deployment?", "topic": "Deployment"},
        {"q": "Describe your experience with CI/CD pipelines.", "topic": "CI/CD"},
        {"q": "How would you monitor a production system?", "topic": "Monitoring"},
        {"q": "What is the ELK stack?", "topic": "Monitoring"},
        {"q": "Explain the concept of immutable infrastructure.", "topic": "Infrastructure"},
        {"q": "How do you handle secrets management in a cloud environment?", "topic": "Security"},
        {"q": "What is a Service Mesh (e.g., Istio)?", "topic": "Networking"},
    ],
    "product_manager": [
        {"q": "How do you prioritise a product backlog?", "topic": "Product Strategy"},
        {"q": "What is a Product Requirements Document (PRD)?", "topic": "Documentation"},
        {"q": "How do you define success metrics for a feature?", "topic": "Metrics"},
        {"q": "Describe the product lifecycle.", "topic": "Product Strategy"},
        {"q": "How do you conduct user research?", "topic": "UX Research"},
        {"q": "What is A/B testing and when would you use it?", "topic": "Experimentation"},
        {"q": "How do you handle disagreements between stakeholders?", "topic": "Stakeholder Management"},
        {"q": "Explain the MoSCoW prioritisation method.", "topic": "Prioritisation"},
        {"q": "What KPIs would you track for an e-commerce app?", "topic": "Metrics"},
        {"q": "How do you write a good user story?", "topic": "Agile"},
    ],
}

# ---------------------------------------------------------------------------
# Behavioral / HR Interview Scenarios
# ---------------------------------------------------------------------------

BEHAVIORAL_QUESTIONS: list[dict] = [
    {
        "q": "Tell me about yourself.",
        "category": "Introduction",
        "framework": "Present-Past-Future",
        "tip": "Keep it professional – 2 minutes max. Cover current role, key achievements, and why this opportunity excites you.",
    },
    {
        "q": "Tell me about a time you faced a challenging deadline. How did you handle it?",
        "category": "Time Management",
        "framework": "STAR",
        "tip": "Quantify the deadline, explain your prioritisation approach, and highlight the outcome.",
    },
    {
        "q": "Describe a situation where you had a conflict with a team member. How was it resolved?",
        "category": "Conflict Resolution",
        "framework": "STAR",
        "tip": "Focus on collaboration and solution, not blame. Demonstrate empathy.",
    },
    {
        "q": "Give an example of when you showed leadership.",
        "category": "Leadership",
        "framework": "STAR",
        "tip": "Leadership doesn't require a title. Think about owning a problem or guiding a team.",
    },
    {
        "q": "Describe a time you failed. What did you learn?",
        "category": "Self-Awareness",
        "framework": "STAR",
        "tip": "Be genuine. Show reflection and growth. Avoid catastrophic failures.",
    },
    {
        "q": "Why do you want to work here?",
        "category": "Motivation",
        "framework": "Company Research",
        "tip": "Align your answer with the company's mission, products, and culture.",
    },
    {
        "q": "Where do you see yourself in 5 years?",
        "category": "Career Goals",
        "framework": "Growth Alignment",
        "tip": "Show ambition while aligning with a realistic path at this company.",
    },
    {
        "q": "What is your greatest strength?",
        "category": "Self-Assessment",
        "framework": "Strength + Evidence",
        "tip": "Pick a strength relevant to the role and back it with a specific example.",
    },
    {
        "q": "What is your greatest weakness?",
        "category": "Self-Assessment",
        "framework": "Weakness + Improvement",
        "tip": "Choose a real weakness. Show the steps you are taking to improve it.",
    },
    {
        "q": "How do you handle working under pressure?",
        "category": "Stress Management",
        "framework": "STAR",
        "tip": "Give a concrete example. Mention tools like prioritisation, breathing techniques, or delegation.",
    },
    {
        "q": "Describe a time you had to learn something quickly.",
        "category": "Adaptability",
        "framework": "STAR",
        "tip": "Show your learning process and speed. Quantify what you learned and how it was applied.",
    },
    {
        "q": "How do you handle feedback and criticism?",
        "category": "Growth Mindset",
        "framework": "STAR",
        "tip": "Show openness to feedback. Describe how you applied it to improve.",
    },
    {
        "q": "Tell me about a time you went above and beyond.",
        "category": "Initiative",
        "framework": "STAR",
        "tip": "Show proactivity and the positive impact it had on your team or company.",
    },
    {
        "q": "How do you manage multiple projects at once?",
        "category": "Organisation",
        "framework": "Methods + Tools",
        "tip": "Mention specific tools (Jira, Trello, Notion) and prioritisation strategies.",
    },
    {
        "q": "Tell me about a time you influenced someone without formal authority.",
        "category": "Influence",
        "framework": "STAR",
        "tip": "Focus on persuasion skills, data-driven arguments, and relationship building.",
    },
]

# ---------------------------------------------------------------------------
# Industry-specific HR Guidelines
# ---------------------------------------------------------------------------

HR_GUIDELINES: list[dict] = [
    {
        "title": "STAR Method",
        "content": (
            "The STAR framework is the gold standard for behavioral interview answers:\n"
            "S – Situation: Set the context. Where were you? What was the challenge?\n"
            "T – Task: What was your specific responsibility?\n"
            "A – Action: What steps did YOU take? Use 'I', not 'we'.\n"
            "R – Result: What was the measurable outcome? Quantify if possible.\n"
            "A complete STAR answer takes 90–120 seconds."
        ),
    },
    {
        "title": "Salary Negotiation",
        "content": (
            "Research market rates on Glassdoor, LinkedIn Salary, and Levels.fyi.\n"
            "Never give a number first. Respond with 'What is the budgeted range for this role?'.\n"
            "Once an offer is made, it is always negotiable. Counter with data, not emotion.\n"
            "Consider total compensation: base, bonus, equity, benefits, WFH flexibility."
        ),
    },
    {
        "title": "Questions to Ask the Interviewer",
        "content": (
            "1. What does success look like in this role in the first 90 days?\n"
            "2. What are the biggest challenges the team is currently facing?\n"
            "3. How do you support professional development and learning?\n"
            "4. What is the engineering/team culture like?\n"
            "5. What is the typical career progression from this role?"
        ),
    },
    {
        "title": "Virtual Interview Tips",
        "content": (
            "Test your camera, microphone, and internet connection beforehand.\n"
            "Use a clean, well-lit background. Avoid backlighting.\n"
            "Look at the camera, not your own video feed.\n"
            "Dress professionally from head to toe.\n"
            "Have a glass of water nearby.\n"
            "Minimise notifications and close unneeded tabs."
        ),
    },
    {
        "title": "Body Language and Communication",
        "content": (
            "Maintain appropriate eye contact – shows confidence and engagement.\n"
            "Sit up straight with an open posture.\n"
            "Avoid filler words: 'um', 'like', 'you know'.\n"
            "Pause before answering – it shows thoughtfulness.\n"
            "Mirror the interviewer's energy level slightly.\n"
            "Smile genuinely – it builds rapport."
        ),
    },
    {
        "title": "Resume Tailoring Strategy",
        "content": (
            "Always tailor your resume for each job posting.\n"
            "Use keywords from the job description (for ATS systems).\n"
            "Quantify achievements: 'Reduced load time by 40%' not 'Improved performance'.\n"
            "Keep it to 1–2 pages. Use bullet points, not paragraphs.\n"
            "List impact first, then method: 'Increased revenue by $500K by building...'."
        ),
    },
]

# ---------------------------------------------------------------------------
# Experience Level Definitions
# ---------------------------------------------------------------------------

EXPERIENCE_LEVELS: dict[str, dict] = {
    "fresher": {
        "label": "Fresher (0–1 years)",
        "focus": "fundamentals, academic projects, internships, problem-solving approach",
        "question_depth": "conceptual",
        "expected_depth": "Basic understanding with clear explanation. Projects and coursework are valid experience.",
    },
    "junior": {
        "label": "Junior (1–3 years)",
        "focus": "practical experience, code quality, debugging, team collaboration",
        "question_depth": "applied",
        "expected_depth": "Hands-on examples from real projects. Should know common tools and workflows.",
    },
    "mid": {
        "label": "Mid-Level (3–6 years)",
        "focus": "system design, performance, mentoring, ownership",
        "question_depth": "design",
        "expected_depth": "Independent decision-making, trade-off analysis, basic system design.",
    },
    "senior": {
        "label": "Senior (6–10 years)",
        "focus": "architecture, cross-team impact, technical leadership, scalability",
        "question_depth": "architectural",
        "expected_depth": "Deep expertise, strategic thinking, team leadership, scalable system design.",
    },
    "lead": {
        "label": "Lead / Principal (10+ years)",
        "focus": "strategy, org-wide impact, building platforms, hiring",
        "question_depth": "strategic",
        "expected_depth": "Organisational thinking, vision, cross-functional leadership, technology roadmaps.",
    },
}

# ---------------------------------------------------------------------------
# Role normalisation map
# ---------------------------------------------------------------------------

ROLE_ALIASES: dict[str, str] = {
    "swe": "software_engineer",
    "software engineer": "software_engineer",
    "software developer": "software_engineer",
    "developer": "software_engineer",
    "programmer": "software_engineer",
    "data scientist": "data_scientist",
    "ml engineer": "data_scientist",
    "machine learning engineer": "data_scientist",
    "ai engineer": "data_scientist",
    "frontend": "frontend_developer",
    "front end": "frontend_developer",
    "frontend developer": "frontend_developer",
    "ui developer": "frontend_developer",
    "react developer": "frontend_developer",
    "backend": "backend_developer",
    "back end": "backend_developer",
    "backend developer": "backend_developer",
    "api developer": "backend_developer",
    "devops": "devops_engineer",
    "devops engineer": "devops_engineer",
    "sre": "devops_engineer",
    "site reliability engineer": "devops_engineer",
    "pm": "product_manager",
    "product manager": "product_manager",
    "product owner": "product_manager",
}


def normalise_role(role: str) -> str:
    """Normalise a free-text role string to an internal key."""
    return ROLE_ALIASES.get(role.lower().strip(), "software_engineer")
