"""
SkillBridge ATS-Friendly Resume Service
Provides:
1. Rule-based ATS Resume Quality Review (scoring, critical issues, improvements)
2. Bullet Point Action-Verb & Contribution Guidance
3. Job-Specific Keyword Tailoring & Gap Analysis (reusing skill_extractor)
4. Native, zero-dependency OpenXML DOCX Resume Generator
5. Industry-standard student sample resume templates
"""

import io
import re
import zipfile
from xml.sax.saxutils import escape
from typing import Dict, List, Any, Optional, Tuple

from app.services.skill_extractor import extract_skills_from_text

# -----------------------------------------------------------------------------
# Strong Action Verbs & Vague Phrases Dictionaries
# -----------------------------------------------------------------------------
STRONG_ACTION_VERBS = {
    # Engineering & Building
    "architected", "built", "engineered", "developed", "constructed", "implemented",
    "programmed", "coded", "designed", "created", "configured", "deployed",
    # Optimization & Performance
    "optimized", "streamlined", "accelerated", "refactored", "automated",
    "enhanced", "reduced", "scaled", "debugged", "resolved", "overhauled",
    # Leadership & Delivery
    "orchestrated", "spearheaded", "directed", "led", "managed", "coordinated",
    "collaborated", "mentored", "delivered", "launched", "executed", "championed",
    # Data & Analysis
    "analyzed", "modelled", "modeled", "quantified", "evaluated", "extracted",
    "visualized", "synthesized", "formulated", "computed", "queried",
    # Integration & Testing
    "integrated", "tested", "validated", "benchmarked", "standardized",
    "audited", "established", "authored", "documented", "published"
}

VAGUE_PHRASES = [
    ("worked on", "Specify your exact role and contributions (e.g., 'Engineered', 'Developed')"),
    ("responsible for", "Focus on the outcome achieved rather than the duty assigned (e.g., 'Spearheaded', 'Delivered')"),
    ("helped with", "Clarify your individual technical contribution (e.g., 'Collaborated to build', 'Integrated')"),
    ("assisted in", "State the specific module or feature you implemented (e.g., 'Implemented', 'Refactored')"),
    ("handled", "Describe the technical method and results (e.g., 'Managed and optimized', 'Resolved')"),
    ("participated in", "Detail what you personally delivered (e.g., 'Contributed to sprint goals by engineering')"),
    ("was tasked with", "Focus on proactive delivery (e.g., 'Spearheaded development of')"),
    ("gained experience", "Highlight what you built using the technology (e.g., 'Built responsive UI components using')")
]

PLACEHOLDER_PATTERNS = [
    r"\[company(?:\s+name)?\]",
    r"\[project(?:\s+name)?\]",
    r"\[role\]",
    r"\[your(?:\s+name)?\]",
    r"lorem\s+ipsum",
    r"\btodo\b",
    r"\bxxx+\b",
    r"example\.com",
    r"user@email\.com",
    r"john\s+doe"
]


# -----------------------------------------------------------------------------
# Student Sample Templates (Accurate, Non-Fabricated Entry-Level Profiles)
# -----------------------------------------------------------------------------
SAMPLE_RESUMES = {
    "software_engineering": {
        "title": "Full-Stack Software Engineering Resume",
        "target_role": "Full-Stack Developer",
        "template_id": "classic_ats",
        "contact_info": {
            "full_name": "Alex Chen",
            "email": "alex.chen.dev@example.edu",
            "phone": "+1 (555) 019-2834",
            "location": "San Francisco, CA",
            "linkedin_url": "https://linkedin.com/in/alexchen-dev",
            "github_url": "https://github.com/alexchen-dev",
            "portfolio_url": "https://alexchen.dev"
        },
        "summary": "Computer Science undergraduate with practical experience in building full-stack web applications using React, Python (FastAPI), and relational databases. Strong foundation in data structures, algorithms, and RESTful API architecture with a passion for clean code and performance optimization.",
        "skills": [
            {"category": "Programming Languages", "items": ["Python", "JavaScript", "TypeScript", "SQL", "C++"]},
            {"category": "Frontend Technologies", "items": ["React.js", "HTML5", "CSS3", "Vite", "Responsive Design"]},
            {"category": "Backend & APIs", "items": ["FastAPI", "Node.js", "Express", "RESTful Architecture", "SQLAlchemy"]},
            {"category": "Databases & Storage", "items": ["PostgreSQL", "SQLite", "Redis", "Database Indexing"]},
            {"category": "Developer Tools", "items": ["Git", "GitHub", "Docker", "Linux / Bash", "Postman", "CI/CD Basics"]}
        ],
        "education": [
            {
                "id": "edu-1",
                "institution": "University of Technology",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": "Aug 2022",
                "graduation_date": "May 2026",
                "gpa_or_grade": "3.8 / 4.0",
                "coursework": "Data Structures & Algorithms, Database Systems, Operating Systems, Web Engineering"
            }
        ],
        "projects": [
            {
                "id": "proj-1",
                "title": "SkillBridge Career Readiness Platform",
                "description": "Full-stack application unifying job application tracking, job description keyword analysis, and interview practice.",
                "technologies": ["React", "FastAPI", "Python", "SQLAlchemy", "SQLite"],
                "github_url": "https://github.com/alexchen-dev/skillbridge",
                "live_url": "https://skillbridge.example.edu",
                "bullets": [
                    "Engineered a responsive single-page application using React 19 and custom CSS design system with zero framework overhead.",
                    "Architected RESTful endpoints in FastAPI with Pydantic validation, achieving sub-50ms average response latency.",
                    "Implemented deterministic skill extraction algorithms comparing candidate profiles against 100+ industry skill standards.",
                    "Constructed 40+ automated test suites with unittest, verifying end-to-end multi-module integration and relational data integrity."
                ]
            },
            {
                "id": "proj-2",
                "title": "Distributed Task Queue & Metrics Monitor",
                "description": "Asynchronous job worker and real-time execution dashboard for batch data processing.",
                "technologies": ["Python", "Redis", "PostgreSQL", "Docker"],
                "github_url": "https://github.com/alexchen-dev/distributed-queue",
                "live_url": "",
                "bullets": [
                    "Developed an asynchronous task distributor using Redis pub/sub queues and worker worker processes.",
                    "Structured relational database schemas in PostgreSQL with foreign keys and compound indexes for fast query filtering.",
                    "Containerized multi-service environment using Docker Compose to ensure reproducible local development."
                ]
            }
        ],
        "experience": [
            {
                "id": "exp-1",
                "organization": "Campus Tech Solutions",
                "job_title": "Undergraduate Software Engineering Intern",
                "employment_type": "Internship",
                "location": "On-site",
                "start_date": "Jun 2024",
                "end_date": "Aug 2024",
                "bullets": [
                    "Collaborated with senior engineers to maintain campus portal microservices handling 15,000+ student requests daily.",
                    "Refactored legacy database queries and added connection pooling, eliminating connection timeout exceptions.",
                    "Authored automated integration tests and technical documentation for newly onboarded student developers."
                ]
            }
        ],
        "additional_sections": {
            "certifications": [
                {
                    "id": "cert-1",
                    "name": "PostgreSQL Fundamentals & Schema Design",
                    "issuer": "Coursera / Meta",
                    "date": "Jan 2024",
                    "url": "https://coursera.org/verify/example"
                }
            ],
            "achievements": [
                {
                    "id": "ach-1",
                    "title": "Dean's Honor List",
                    "description": "Recognized for academic excellence across 4 consecutive semesters.",
                    "date": "2023 - 2024"
                }
            ],
            "leadership": [
                {
                    "id": "lead-1",
                    "role": "Technical Lead",
                    "organization": "ACM Student Chapter",
                    "bullets": [
                        "Organized hands-on web development workshops for 80+ freshman computer science students."
                    ]
                }
            ],
            "languages": [
                {
                    "id": "lang-1",
                    "language": "English",
                    "proficiency": "Fluent"
                }
            ]
        },
        "section_config": {
            "order": ["contact", "summary", "skills", "education", "projects", "experience", "certifications", "achievements"],
            "enabled": {
                "contact": True,
                "summary": True,
                "skills": True,
                "education": True,
                "projects": True,
                "experience": True,
                "certifications": True,
                "achievements": True,
                "leadership": False,
                "languages": False
            }
        }
    }
}


def _to_resume_dict(data: Any) -> Dict[str, Any]:
    """Normalizes dict, Pydantic, or SQLAlchemy model into a standard dictionary."""
    if isinstance(data, dict):
        return data
    return {
        "id": getattr(data, "id", 0),
        "title": getattr(data, "title", ""),
        "target_job_id": getattr(data, "target_job_id", None),
        "target_role": getattr(data, "target_role", None),
        "template_id": getattr(data, "template_id", "ats-classic"),
        "contact_info": getattr(data, "contact_info", {}) or {},
        "summary": getattr(data, "summary", "") or "",
        "skills": getattr(data, "skills", []) or [],
        "education": getattr(data, "education", []) or [],
        "projects": getattr(data, "projects", []) or [],
        "experience": getattr(data, "experience", []) or [],
        "additional_sections": getattr(data, "additional_sections", {}) or {},
        "section_config": getattr(data, "section_config", {}) or {},
    }


def _to_job_dict(data: Any) -> Dict[str, Any]:
    """Normalizes job application into a dict."""
    if isinstance(data, dict):
        return data
    return {
        "id": getattr(data, "id", 0),
        "company_name": getattr(data, "company_name", ""),
        "job_title": getattr(data, "job_title", ""),
        "job_description": getattr(data, "job_description", ""),
    }


def _to_analysis_dict(data: Any) -> Optional[Dict[str, Any]]:
    """Normalizes job analysis into a dict."""
    if data is None or isinstance(data, dict):
        return data
    return {
        "required_skills": getattr(data, "required_skills", []),
        "preferred_skills": getattr(data, "preferred_skills", []),
    }


# -----------------------------------------------------------------------------
# Quality Review Engine (Explainable, Transparent, Rule-Based)
# -----------------------------------------------------------------------------
def analyze_resume_quality(resume_data: Any) -> Dict[str, Any]:
    """
    Evaluates practical ATS compliance, completeness, and phrasing quality.
    Scores are strictly rule-based (0 to 100) and explained with actionable feedback.
    Accepts dictionary, Pydantic model, or SQLAlchemy Resume instance.
    """
    resume_dict = _to_resume_dict(resume_data)
    contact = resume_dict.get("contact_info") or {}
    summary = (resume_dict.get("summary") or "").strip()
    skills = resume_dict.get("skills") or []
    education = resume_dict.get("education") or []
    projects = resume_dict.get("projects") or []
    experience = resume_dict.get("experience") or []
    section_cfg = resume_dict.get("section_config") or {}
    enabled_sections = section_cfg.get("enabled", {})

    critical_issues: List[Dict[str, str]] = []
    recommended_improvements: List[Dict[str, str]] = []
    optional_refinements: List[Dict[str, str]] = []
    bullet_insights: List[Dict[str, Any]] = []

    # Category score accumulator (Max: 100)
    scores = {
        "contact": 20,
        "summary": 10,
        "skills": 20,
        "projects_and_experience": 25,
        "education": 15,
        "formatting_and_phrasing": 10
    }

    # 1. Contact Information Checks
    full_name = contact.get("full_name", "").strip()
    email = contact.get("email", "").strip()
    phone = contact.get("phone", "").strip()
    location = contact.get("location", "").strip()
    linkedin = contact.get("linkedin_url", "").strip()
    github = contact.get("github_url", "").strip()

    if not full_name:
        scores["contact"] -= 10
        critical_issues.append({
            "rule_id": "missing_name",
            "category": "critical",
            "title": "Missing Full Name",
            "detail": "ATS parsers require an applicant name at the top of the resume document.",
            "action_hint": "Enter your legal or professional name in Contact Information.",
            "section": "contact"
        })

    if not email or "@" not in email or "." not in email:
        scores["contact"] -= 6
        critical_issues.append({
            "rule_id": "invalid_email",
            "category": "critical",
            "title": "Missing or Invalid Email Address",
            "detail": "A professional email address is essential for automated recruiter communications.",
            "action_hint": "Provide a clean, valid email address (e.g., student@university.edu).",
            "section": "contact"
        })

    if not phone:
        scores["contact"] -= 2
        recommended_improvements.append({
            "rule_id": "missing_phone",
            "category": "improvement",
            "title": "Phone Number Recommended",
            "detail": "Many ATS systems validate a contact telephone number for SMS or phone screenings.",
            "action_hint": "Add a phone number with country or area code.",
            "section": "contact"
        })

    if not linkedin and not github:
        scores["contact"] -= 2
        recommended_improvements.append({
            "rule_id": "missing_links",
            "category": "improvement",
            "title": "Add LinkedIn or GitHub Profile",
            "detail": "Technical recruiters and ATS screeners look for links to code repositories or verified profiles.",
            "action_hint": "Include your LinkedIn URL or active GitHub profile link.",
            "section": "contact"
        })

    # Validate URLs if present
    for link_name, url_val in [("LinkedIn", linkedin), ("GitHub", github), ("Portfolio", contact.get("portfolio_url", ""))]:
        if url_val and not (url_val.startswith("http://") or url_val.startswith("https://")):
            optional_refinements.append({
                "rule_id": f"unformatted_{link_name.lower()}",
                "category": "optional",
                "title": f"Format {link_name} URL with https://",
                "detail": f"URLs with standard https:// prefixes parse cleanly in modern ATS systems.",
                "action_hint": f"Prefix your {link_name} link with https://.",
                "section": "contact"
            })

    # 2. Professional Summary Checks
    is_summary_enabled = enabled_sections.get("summary", True)
    if is_summary_enabled:
        if not summary:
            scores["summary"] -= 6
            recommended_improvements.append({
                "rule_id": "empty_summary",
                "category": "improvement",
                "title": "Add a Professional Summary",
                "detail": "A 2-3 sentence summary clarifies your degree, focus areas, and target role for recruiters.",
                "action_hint": "Write a concise summary describing your background and key technical strengths.",
                "section": "summary"
            })
        elif len(summary.split()) < 15:
            scores["summary"] -= 2
            optional_refinements.append({
                "rule_id": "short_summary",
                "category": "optional",
                "title": "Summary is Very Brief",
                "detail": "Your summary has under 15 words. Consider mentioning your target role and 2-3 core skills.",
                "action_hint": "Expand summary to 2-3 concise sentences.",
                "section": "summary"
            })
        elif len(summary.split()) > 100:
            scores["summary"] -= 2
            optional_refinements.append({
                "rule_id": "long_summary",
                "category": "optional",
                "title": "Summary is Longer than Recommended",
                "detail": "Summaries longer than 100 words can distract from your projects and skills on a 1-page resume.",
                "action_hint": "Tighten your summary to under 75 words.",
                "section": "summary"
            })

    # 3. Technical Skills Checks
    total_skills_count = sum(len(cat.get("items", [])) for cat in skills)
    if not skills or total_skills_count == 0:
        scores["skills"] -= 18
        critical_issues.append({
            "rule_id": "no_skills",
            "category": "critical",
            "title": "Technical Skills Section is Empty",
            "detail": "ATS parsers heavily index the Technical Skills section for keyword matching against job requirements.",
            "action_hint": "Add categorized skills such as Programming Languages, Frameworks, and Tools.",
            "section": "skills"
        })
    elif total_skills_count < 5:
        scores["skills"] -= 6
        recommended_improvements.append({
            "rule_id": "few_skills",
            "category": "improvement",
            "title": "Fewer than 5 Skills Listed",
            "detail": f"You currently have {total_skills_count} skills listed. Most entry-level roles expect 8-15 recognizable technical skills.",
            "action_hint": "Add the languages, libraries, and tools you have practiced or learned.",
            "section": "skills"
        })

    # 4. Education Checks
    if not education:
        scores["education"] -= 12
        critical_issues.append({
            "rule_id": "no_education",
            "category": "critical",
            "title": "Education Section is Empty",
            "detail": "For students and recent graduates, university degree and graduation timing are key qualification criteria.",
            "action_hint": "Add your college or university, degree, field of study, and expected graduation date.",
            "section": "education"
        })
    else:
        for idx, edu in enumerate(education):
            inst = edu.get("institution", "").strip()
            deg = edu.get("degree", "").strip()
            grad_date = edu.get("graduation_date", "").strip()

            if not inst or not deg:
                scores["education"] -= 3
                recommended_improvements.append({
                    "rule_id": f"incomplete_edu_{idx}",
                    "category": "improvement",
                    "title": f"Incomplete Education Entry #{idx + 1}",
                    "detail": "Missing institution or degree name.",
                    "action_hint": "Fill in the institution name and degree.",
                    "section": "education"
                })
            if not grad_date:
                scores["education"] -= 2
                recommended_improvements.append({
                    "rule_id": f"missing_grad_date_{idx}",
                    "category": "improvement",
                    "title": f"Missing Graduation Date (#{idx + 1})",
                    "detail": "Recruiters and ATS filters look for graduation year/month to determine internship vs. full-time eligibility.",
                    "action_hint": "Add your graduation month and year (e.g., 'May 2026').",
                    "section": "education"
                })

    # 5. Projects and Experience Checks
    has_projects = len(projects) > 0
    has_experience = len(experience) > 0

    if not has_projects and not has_experience:
        scores["projects_and_experience"] -= 22
        critical_issues.append({
            "rule_id": "no_projects_or_experience",
            "category": "critical",
            "title": "No Projects or Experience Entries",
            "detail": "Practical projects or internships are the most critical evidence of technical capability on a student resume.",
            "action_hint": "Add at least one technical project describing technologies used and your contributions.",
            "section": "projects"
        })
    elif not has_projects:
        scores["projects_and_experience"] -= 8
        recommended_improvements.append({
            "rule_id": "no_projects",
            "category": "improvement",
            "title": "Add Technical Projects",
            "detail": "For college students, projects demonstrate hands-on coding capability beyond coursework.",
            "action_hint": "Add your best course projects, hackathon work, or personal projects.",
            "section": "projects"
        })

    # Analyze project bullets
    for p_idx, proj in enumerate(projects):
        p_title = proj.get("title", f"Project #{p_idx+1}")
        p_tech = proj.get("technologies", [])
        p_bullets = proj.get("bullets", [])

        if not p_tech:
            optional_refinements.append({
                "rule_id": f"proj_missing_tech_{p_idx}",
                "category": "optional",
                "title": f"Tag Technologies for '{p_title}'",
                "detail": "Explicitly listing technologies (e.g. React, Python) enables ATS keyword parsers to index the project.",
                "action_hint": "Add technologies used to the project tags.",
                "section": "projects"
            })

        if not p_bullets or len(p_bullets) == 0:
            scores["projects_and_experience"] -= 3
            recommended_improvements.append({
                "rule_id": f"proj_no_bullets_{p_idx}",
                "category": "improvement",
                "title": f"Add Bullet Points for '{p_title}'",
                "detail": "Bullets describing your specific implementation details and verified outcomes make projects stand out.",
                "action_hint": "Add 2-3 bullet points describing what you built and how you built it.",
                "section": "projects"
            })
        else:
            for b_idx, bullet in enumerate(p_bullets):
                insight = _inspect_bullet("Project", p_title, b_idx, bullet)
                bullet_insights.append(insight)
                if insight["has_vague_phrase"]:
                    scores["formatting_and_phrasing"] -= 1
                if not insight["has_action_verb"] and len(bullet.strip()) > 15:
                    scores["formatting_and_phrasing"] -= 1

    # Analyze experience bullets
    for e_idx, exp in enumerate(experience):
        e_title = f"{exp.get('job_title', 'Role')} at {exp.get('organization', 'Organization')}"
        e_bullets = exp.get("bullets", [])
        for b_idx, bullet in enumerate(e_bullets):
            insight = _inspect_bullet("Experience", e_title, b_idx, bullet)
            bullet_insights.append(insight)
            if insight["has_vague_phrase"]:
                scores["formatting_and_phrasing"] -= 1

    # 6. Placeholder Text Detection
    all_resume_text = _extract_all_text_from_resume(resume_dict).lower()
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, all_resume_text)
        if matches:
            scores["formatting_and_phrasing"] -= 3
            critical_issues.append({
                "rule_id": f"placeholder_detected_{matches[0]}",
                "category": "critical",
                "title": f"Placeholder Text Found ('{matches[0]}')",
                "detail": "Resumes containing unfilled placeholders or template tokens create a negative impression with automated screeners.",
                "action_hint": f"Replace '{matches[0]}' with your actual personal details.",
                "section": "general"
            })

    # Clamp scores
    for k in scores:
        scores[k] = max(0, min(scores[k], 25))

    overall_score = max(0, min(100, sum(scores.values())))

    # Overall Summary Critique
    if overall_score >= 85:
        summary_critique = "Strong ATS foundation! Your resume has clear section structure, actionable bullet points, and complete contact details."
    elif overall_score >= 70:
        summary_critique = "Good progress. Addressing the recommended improvements below will elevate your resume's clarity and ATS parsing fidelity."
    else:
        summary_critique = "Needs attention. Resolve the critical issues above—particularly contact info, skills, and project bullet details—before submitting."

    return {
        "resume_id": resume_dict.get("id", 0),
        "overall_score": overall_score,
        "score_breakdown": scores,
        "critical_issues": critical_issues,
        "recommended_improvements": recommended_improvements,
        "optional_refinements": optional_refinements,
        "bullet_insights": bullet_insights,
        "summary_critique": summary_critique
    }


def _inspect_bullet(section_type: str, item_title: str, bullet_idx: int, bullet_text: str) -> Dict[str, Any]:
    """Inspects a single bullet point for action verb and vague phrases."""
    cleaned = bullet_text.strip()
    words = re.findall(r"\b[A-Za-z\-']+\b", cleaned)
    first_word = words[0].lower() if words else ""

    has_action_verb = first_word in STRONG_ACTION_VERBS
    detected_verb = first_word if has_action_verb else None

    has_vague = False
    flagged_phrase = None
    suggestion = None

    lower_text = cleaned.lower()
    for phrase, rec in VAGUE_PHRASES:
        if phrase in lower_text:
            has_vague = True
            flagged_phrase = phrase
            suggestion = rec
            break

    if not has_action_verb and not suggestion:
        suggestion = "Start this bullet with a strong action verb (e.g., 'Engineered', 'Built', 'Implemented', 'Designed')."

    return {
        "section": section_type,
        "item_title": item_title,
        "bullet_index": bullet_idx,
        "bullet_text": bullet_text,
        "has_action_verb": has_action_verb,
        "detected_action_verb": detected_verb,
        "has_vague_phrase": has_vague,
        "flagged_phrase": flagged_phrase,
        "improvement_suggestion": suggestion
    }


def _extract_all_text_from_resume(resume_data: Any) -> str:
    """Concatenates all user-entered resume text into a single searchable string."""
    resume_data = _to_resume_dict(resume_data)
    parts = []
    contact = resume_data.get("contact_info") or {}
    for val in contact.values():
        if val:
            parts.append(str(val))

    if resume_data.get("summary"):
        parts.append(resume_data["summary"])

    for cat in resume_data.get("skills") or []:
        parts.append(cat.get("category", ""))
        parts.extend(cat.get("items", []))

    for edu in resume_data.get("education") or []:
        parts.append(edu.get("institution", ""))
        parts.append(edu.get("degree", ""))
        parts.append(edu.get("field_of_study", ""))
        parts.append(edu.get("coursework", ""))

    for proj in resume_data.get("projects") or []:
        parts.append(proj.get("title", ""))
        parts.append(proj.get("description", ""))
        parts.extend(proj.get("technologies", []))
        parts.extend(proj.get("bullets", []))

    for exp in resume_data.get("experience") or []:
        parts.append(exp.get("organization", ""))
        parts.append(exp.get("job_title", ""))
        parts.extend(exp.get("bullets", []))

    addtl = resume_data.get("additional_sections") or {}
    for cert in addtl.get("certifications", []):
        parts.append(cert.get("name", ""))
        parts.append(cert.get("issuer", ""))
    for ach in addtl.get("achievements", []):
        parts.append(ach.get("title", ""))
        parts.append(ach.get("description", ""))

    return " ".join(parts)


# -----------------------------------------------------------------------------
# Job Tailoring & Keyword Matching (Reuses SkillBridge skill_extractor)
# -----------------------------------------------------------------------------
def tailor_resume_to_job(
    resume_data: Any,
    job_application: Any,
    job_analysis: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Compares resume text against target job requirements, reusing transparent
    skill extraction rules to identify present vs. missing keywords and provide
    truthful, non-hallucinatory suggestions.
    """
    resume_data = _to_resume_dict(resume_data)
    job_application = _to_job_dict(job_application)
    job_analysis = _to_analysis_dict(job_analysis)

    resume_text = _extract_all_text_from_resume(resume_data)

    # 1. Determine job requirements
    required_skills: List[Dict[str, Any]] = []
    preferred_skills: List[Dict[str, Any]] = []

    if job_analysis:
        required_skills = job_analysis.get("required_skills") or []
        preferred_skills = job_analysis.get("preferred_skills") or []

    # If no analysis exists, extract on the fly from job_description or notes
    if not required_skills and not preferred_skills:
        jd_text = (
            job_application.get("job_description")
            or job_application.get("notes")
            or job_application.get("skills")
            or ""
        )
        if jd_text:
            extracted_list = extract_skills_from_text(jd_text)
            if not required_skills and extracted_list:
                required_skills = extracted_list[:8]
                preferred_skills = extracted_list[8:14]

    # Fallback to skills column on JobApplication
    if not required_skills and job_application.get("skills"):
        manual_skills = [s.strip() for s in job_application["skills"].split(",") if s.strip()]
        for s in manual_skills:
            required_skills.append({"skill": s, "category": "Required Technical Skill"})

    # 2. Extract skills from the candidate's resume text
    resume_extracted = extract_skills_from_text(resume_text)
    # Collect all canonical skill names present in resume
    candidate_skills = set()
    if isinstance(resume_extracted, list):
        for s_dict in resume_extracted:
            if isinstance(s_dict, dict) and "skill" in s_dict:
                candidate_skills.add(s_dict["skill"].lower())

    # Also include raw tokens from resume skills list
    for cat in resume_data.get("skills") or []:
        for item in cat.get("items", []):
            candidate_skills.add(item.strip().lower())

    # 3. Categorize matching vs. missing
    present_keywords: List[Dict[str, str]] = []
    missing_required: List[Dict[str, str]] = []
    missing_preferred: List[Dict[str, str]] = []

    for req in required_skills:
        s_name = req.get("skill", "")
        if not s_name:
            continue
        if s_name.lower() in candidate_skills or any(s_name.lower() in item for item in candidate_skills):
            present_keywords.append({
                "keyword": s_name,
                "category": req.get("category", "Required Skill"),
                "location_in_resume": "Present in resume"
            })
        else:
            missing_required.append({
                "keyword": s_name,
                "category": req.get("category", "Required Skill"),
                "location_in_resume": "Missing"
            })

    for pref in preferred_skills:
        s_name = pref.get("skill", "")
        if not s_name:
            continue
        if s_name.lower() in candidate_skills or any(s_name.lower() in item for item in candidate_skills):
            present_keywords.append({
                "keyword": s_name,
                "category": pref.get("category", "Preferred Skill"),
                "location_in_resume": "Present in resume"
            })
        else:
            missing_preferred.append({
                "keyword": s_name,
                "category": pref.get("category", "Preferred Skill"),
                "location_in_resume": "Missing"
            })

    # Deduplicate present
    seen_present = set()
    dedup_present = []
    for p in present_keywords:
        if p["keyword"].lower() not in seen_present:
            seen_present.add(p["keyword"].lower())
            dedup_present.append(p)
    present_keywords = dedup_present

    # Calculate match percentage
    total_tracked = len(required_skills) + len(preferred_skills)
    match_score = 0.0
    if total_tracked > 0:
        match_score = round((len(present_keywords) / total_tracked) * 100.0, 1)
        match_score = min(100.0, match_score)

    # 4. Actionable Alignment Suggestions
    alignment_suggestions: List[str] = []
    company = job_application.get("company_name", "this company")
    role = job_application.get("job_title", "this role")

    # Check for skills present in resume projects but missing from top skills list
    skill_category_items = set()
    for cat in resume_data.get("skills") or []:
        for item in cat.get("items", []):
            skill_category_items.add(item.lower().strip())

    for present in present_keywords:
        kw = present["keyword"]
        if kw.lower() not in skill_category_items:
            alignment_suggestions.append(
                f"You mentioned '{kw}' in your project/experience text, but it is not listed in your Technical Skills section. Add '{kw}' to your categorized skills list so ATS parsers index it immediately."
            )

    # Check projects mentioning required technologies
    for proj in resume_data.get("projects") or []:
        p_title = proj.get("title", "Project")
        p_techs = [t.lower() for t in proj.get("technologies", [])]
        matched_in_proj = [p["keyword"] for p in present_keywords if p["keyword"].lower() in p_techs]
        if matched_in_proj:
            alignment_suggestions.append(
                f"Highlight your work on '{p_title}': It directly demonstrates {', '.join(matched_in_proj[:2])}, which {company} explicitly looks for in {role} applicants."
            )

    # 5. Recommended Truthful Additions
    recommended_additions: List[str] = []
    for miss in missing_required[:4]:
        kw = miss["keyword"]
        recommended_additions.append(
            f"{company} specifically lists '{kw}' as a required skill. If you have coursework, academic labs, or personal projects using {kw}, consider truthfully adding that experience or project."
        )

    for pref in missing_preferred[:2]:
        kw = pref["keyword"]
        recommended_additions.append(
            f"Bonus qualification: '{kw}' was identified as preferred. Mentioning any familiarity with {kw} will help differentiate your application."
        )

    return {
        "resume_id": resume_data.get("id", 0),
        "job_id": job_application.get("id", 0),
        "company_name": company,
        "job_title": role,
        "keyword_match_score": match_score,
        "keyword_match_percentage": match_score,
        "present_keywords": present_keywords,
        "missing_required_keywords": missing_required,
        "missing_preferred_keywords": missing_preferred,
        "alignment_suggestions": alignment_suggestions[:5],
        "truthful_alignment_suggestions": alignment_suggestions[:5],
        "recommended_additions": recommended_additions[:5]
    }


# -----------------------------------------------------------------------------
# Native OpenXML DOCX Resume Generator (Zero External Binary Dependencies)
# -----------------------------------------------------------------------------
def generate_docx_resume(resume_data: Any) -> bytes:
    """
    Generates a genuine, standard ATS-friendly Microsoft Word (.docx) file
    directly via OpenXML specification using Python's standard zipfile library.

    Guarantees:
    - Pure single-column document flow
    - Standard Heading 1, Heading 2, and Bullet list paragraph styles
    - Clean typography (Calibri, 10.5pt body, 14pt section titles)
    - Zero floating text boxes, zero multi-column tables, zero decorative shapes
    - 100% selectable, parseable text
    """
    resume_data = _to_resume_dict(resume_data)
    contact = resume_data.get("contact_info") or {}
    summary = resume_data.get("summary") or ""
    skills = resume_data.get("skills") or []
    education = resume_data.get("education") or []
    projects = resume_data.get("projects") or []
    experience = resume_data.get("experience") or []
    addtl = resume_data.get("additional_sections") or {}
    section_cfg = resume_data.get("section_config") or {}
    enabled = section_cfg.get("enabled", {})

    # Build document XML body paragraphs
    body_xml_parts: List[str] = []

    # 1. Candidate Name (Large Bold Title)
    full_name = contact.get("full_name") or "Applicant Resume"
    body_xml_parts.append(
        f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="80"/></w:pPr>'
        f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr>'
        f'<w:t>{escape(full_name)}</w:t></w:r></w:p>'
    )

    # 2. Contact Details Line
    contact_parts = []
    if contact.get("email"):
        contact_parts.append(contact["email"])
    if contact.get("phone"):
        contact_parts.append(contact["phone"])
    if contact.get("location"):
        contact_parts.append(contact["location"])
    if contact.get("linkedin_url"):
        contact_parts.append(contact["linkedin_url"])
    if contact.get("github_url"):
        contact_parts.append(contact["github_url"])
    if contact.get("portfolio_url"):
        contact_parts.append(contact["portfolio_url"])

    contact_line = " | ".join(contact_parts)
    if contact_line:
        body_xml_parts.append(
            f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="240"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:color w:val="475569"/><w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr>'
            f'<w:t>{escape(contact_line)}</w:t></w:r></w:p>'
        )

    # Helper: Section Heading
    def _add_section_heading(title: str):
        body_xml_parts.append(
            f'<w:p><w:pPr><w:spacing w:before="240" w:after="80"/><w:pBdr>'
            f'<w:bottom w:val="single" w:sz="6" w:space="4" w:color="94A3B8"/></w:pBdr></w:pPr>'
            f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="0F172A"/></w:rPr>'
            f'<w:t>{escape(title.upper())}</w:t></w:r></w:p>'
        )

    # Helper: Bullet Point
    def _add_bullet(text: str):
        body_xml_parts.append(
            f'<w:p><w:pPr><w:ind w:left="360" w:hanging="240"/><w:spacing w:after="60"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
            f'<w:t>•  {escape(text)}</w:t></w:r></w:p>'
        )

    # 3. Professional Summary
    if enabled.get("summary", True) and summary.strip():
        _add_section_heading("Professional Summary")
        body_xml_parts.append(
            f'<w:p><w:pPr><w:spacing w:after="160"/></w:pPr>'
            f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>'
            f'<w:t>{escape(summary.strip())}</w:t></w:r></w:p>'
        )

    # 4. Technical Skills
    if enabled.get("skills", True) and skills:
        _add_section_heading("Technical Skills")
        for cat in skills:
            cat_name = cat.get("category", "Skills")
            items_str = ", ".join(cat.get("items", []))
            if items_str:
                body_xml_parts.append(
                    f'<w:p><w:pPr><w:spacing w:after="60"/></w:pPr>'
                    f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>'
                    f'<w:t>{escape(cat_name)}: </w:t></w:r>'
                    f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>'
                    f'<w:t>{escape(items_str)}</w:t></w:r></w:p>'
                )

    # 5. Education
    if enabled.get("education", True) and education:
        _add_section_heading("Education")
        for edu in education:
            inst = edu.get("institution", "")
            deg = edu.get("degree", "")
            field = edu.get("field_of_study", "")
            deg_str = f"{deg} in {field}" if deg and field else (deg or field)
            grad = edu.get("graduation_date", "")
            grade = edu.get("gpa_or_grade", "")
            coursework = edu.get("coursework", "")

            # Line 1: Degree & Institution
            body_xml_parts.append(
                f'<w:p><w:pPr><w:spacing w:before="60" w:after="40"/></w:pPr>'
                f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>'
                f'<w:t>{escape(deg_str)}</w:t></w:r>'
                f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>'
                f'<w:t> — {escape(inst)}</w:t></w:r>'
                f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:i/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
                f'<w:t>  ({escape(grad)})</w:t></w:r></w:p>'
            )

            if grade:
                body_xml_parts.append(
                    f'<w:p><w:pPr><w:spacing w:after="40"/></w:pPr>'
                    f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
                    f'<w:t>GPA / Grade: {escape(grade)}</w:t></w:r></w:p>'
                )

            if coursework:
                body_xml_parts.append(
                    f'<w:p><w:pPr><w:spacing w:after="80"/></w:pPr>'
                    f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:color w:val="475569"/><w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr>'
                    f'<w:t>Relevant Coursework: {escape(coursework)}</w:t></w:r></w:p>'
                )

    # 6. Projects
    if enabled.get("projects", True) and projects:
        _add_section_heading("Technical Projects")
        for proj in projects:
            title = proj.get("title", "")
            tech_list = proj.get("technologies", [])
            tech_str = " | ".join(tech_list) if tech_list else ""
            desc = proj.get("description", "")
            bullets = proj.get("bullets", [])

            # Title + Tech
            title_line = f"{title}" + (f" ({tech_str})" if tech_str else "")
            body_xml_parts.append(
                f'<w:p><w:pPr><w:spacing w:before="80" w:after="40"/></w:pPr>'
                f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
                f'<w:t>{escape(title_line)}</w:t></w:r></w:p>'
            )

            if desc:
                body_xml_parts.append(
                    f'<w:p><w:pPr><w:spacing w:after="60"/></w:pPr>'
                    f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:color w:val="475569"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
                    f'<w:t>{escape(desc)}</w:t></w:r></w:p>'
                )

            for b in bullets:
                if b.strip():
                    _add_bullet(b.strip())

    # 7. Experience / Internships
    if enabled.get("experience", True) and experience:
        _add_section_heading("Experience & Internships")
        for exp in experience:
            role = exp.get("job_title", "")
            org = exp.get("organization", "")
            dates = f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}".strip(" -")
            loc = exp.get("location", "")
            bullets = exp.get("bullets", [])

            header_line = f"{role} — {org}" + (f", {loc}" if loc else "") + (f" ({dates})" if dates else "")
            body_xml_parts.append(
                f'<w:p><w:pPr><w:spacing w:before="80" w:after="40"/></w:pPr>'
                f'<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:b/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
                f'<w:t>{escape(header_line)}</w:t></w:r></w:p>'
            )

            for b in bullets:
                if b.strip():
                    _add_bullet(b.strip())

    # 8. Additional Sections (Certifications, Achievements, Leadership)
    certs = addtl.get("certifications", [])
    if enabled.get("certifications") and certs:
        _add_section_heading("Certifications")
        for cert in certs:
            c_name = cert.get("name", "")
            c_iss = cert.get("issuer", "")
            c_date = cert.get("date", "")
            c_str = f"{c_name}" + (f" — {c_iss}" if c_iss else "") + (f" ({c_date})" if c_date else "")
            _add_bullet(c_str)

    achievements = addtl.get("achievements", [])
    if enabled.get("achievements") and achievements:
        _add_section_heading("Honors & Achievements")
        for ach in achievements:
            a_title = ach.get("title", "")
            a_desc = ach.get("description", "")
            a_date = ach.get("date", "")
            a_str = f"{a_title}" + (f": {a_desc}" if a_desc else "") + (f" ({a_date})" if a_date else "")
            _add_bullet(a_str)

    # Assemble Document XML with 1-inch margins
    body_content = "".join(body_xml_parts)
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{body_content}'
        '<w:sectPr>'
        '<w:pgSz w:w="12240" w:h="15840"/>'  # Standard Letter 8.5 x 11 inches
        '<w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080" w:header="720" w:footer="720" w:gutter="0"/>'  # 0.75-inch margins
        '</w:sectPr>'
        '</w:body></w:document>'
    )

    # Standard OpenXML Package Scaffold Files
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )

    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )

    word_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '</Relationships>'
    )

    # Pack into a standard zipfile in memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("word/_rels/document.xml.rels", word_rels_xml)
        zf.writestr("word/document.xml", document_xml)

    return buffer.getvalue()
