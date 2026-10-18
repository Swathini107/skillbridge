import re
from typing import Dict, List, Optional, Tuple, Any

# ============================================================================
# SKILL DICTIONARY: Domains, Canonical Names, and Recognized Aliases
# ============================================================================

SKILL_CATALOG = [
    # --- Frontend Development ---
    {
        "skill": "JavaScript",
        "category": "Frontend",
        "aliases": [r"\bjavascript\b", r"\bjs\b", r"\becmascript\b", r"\bes6\b", r"\bes202[0-9]\b"],
    },
    {
        "skill": "TypeScript",
        "category": "Frontend",
        "aliases": [r"\btypescript\b", r"\bts\b"],
    },
    {
        "skill": "React",
        "category": "Frontend",
        "aliases": [r"\breact(?:\.js|js)?\b", r"\breact\s+framework\b"],
    },
    {
        "skill": "Next.js",
        "category": "Frontend",
        "aliases": [r"\bnext(?:\.js|js)?\b"],
    },
    {
        "skill": "Vue.js",
        "category": "Frontend",
        "aliases": [r"\bvue(?:\.js|js)?\b", r"\bvue3\b"],
    },
    {
        "skill": "Angular",
        "category": "Frontend",
        "aliases": [r"\bangular(?:\.js|js)?\b"],
    },
    {
        "skill": "HTML",
        "category": "Frontend",
        "aliases": [r"\bhtml5?\b"],
    },
    {
        "skill": "CSS",
        "category": "Frontend",
        "aliases": [r"\bcss3?\b", r"\bmodern\s+css\b"],
    },
    {
        "skill": "Tailwind CSS",
        "category": "Frontend",
        "aliases": [r"\btailwind(?:\s*css)?\b"],
    },
    {
        "skill": "Redux",
        "category": "Frontend",
        "aliases": [r"\bredux(?:\s+toolkit)?\b"],
    },

    # --- Backend & Full-Stack Development ---
    {
        "skill": "Python",
        "category": "Backend",
        "aliases": [r"\bpython3?\b", r"\bpython\s+programming\b"],
    },
    {
        "skill": "Node.js",
        "category": "Backend",
        "aliases": [r"\bnode(?:\.js|js)?\b", r"\bnode\s+runtime\b"],
    },
    {
        "skill": "Express",
        "category": "Backend",
        "aliases": [r"\bexpress(?:\.js|js)?\b"],
    },
    {
        "skill": "FastAPI",
        "category": "Backend",
        "aliases": [r"\bfastapi\b"],
    },
    {
        "skill": "Flask",
        "category": "Backend",
        "aliases": [r"\bflask\b"],
    },
    {
        "skill": "Django",
        "category": "Backend",
        "aliases": [r"\bdjango\b"],
    },
    {
        "skill": "REST APIs",
        "category": "Backend",
        "aliases": [r"\brestful?\s+apis?\b", r"\brest\s+apis?\b", r"\brestful\b", r"\bapi\s+development\b"],
    },
    {
        "skill": "GraphQL",
        "category": "Backend",
        "aliases": [r"\bgraphql\b"],
    },

    # --- Databases & Storage ---
    {
        "skill": "SQL",
        "category": "Database",
        "aliases": [r"\bsql\b", r"\bstructured\s+query\s+language\b", r"\brdbms\b"],
    },
    {
        "skill": "PostgreSQL",
        "category": "Database",
        "aliases": [r"\bpostgres(?:ql)?\b"],
    },
    {
        "skill": "SQLite",
        "category": "Database",
        "aliases": [r"\bsqlite3?\b"],
    },
    {
        "skill": "MySQL",
        "category": "Database",
        "aliases": [r"\bmysql\b"],
    },
    {
        "skill": "MongoDB",
        "category": "Database",
        "aliases": [r"\bmongodb?\b", r"\bno\s*sql\b"],
    },
    {
        "skill": "Redis",
        "category": "Database",
        "aliases": [r"\bredis\b"],
    },

    # --- Data Science, Analysis & Machine Learning ---
    {
        "skill": "Pandas",
        "category": "Data Science",
        "aliases": [r"\bpandas\b"],
    },
    {
        "skill": "NumPy",
        "category": "Data Science",
        "aliases": [r"\bnumpy\b"],
    },
    {
        "skill": "Scikit-learn",
        "category": "Data Science",
        "aliases": [r"\bscikit-learn\b", r"\bsklearn\b", r"\bscikit\s+learn\b"],
    },
    {
        "skill": "Machine Learning",
        "category": "Data Science",
        "aliases": [r"\bmachine\s+learning\b", r"\bml\b"],
    },
    {
        "skill": "Deep Learning",
        "category": "Data Science",
        "aliases": [r"\bdeep\s+learning\b", r"\bneural\s+networks\b"],
    },
    {
        "skill": "Natural Language Processing",
        "category": "Data Science",
        "aliases": [r"\bnatural\s+language\s+processing\b", r"\bnlp\b", r"\btext\s+mining\b"],
    },
    {
        "skill": "Exploratory Data Analysis",
        "category": "Data Science",
        "aliases": [r"\bexploratory\s+data\s+analysis\b", r"\beda\b"],
    },
    {
        "skill": "Statistics",
        "category": "Data Science",
        "aliases": [r"\bstatistics\b", r"\bstatistical\s+(?:modeling|methods|analysis|testing)\b"],
    },
    {
        "skill": "Data Visualization",
        "category": "Data Science",
        "aliases": [r"\bdata\s+visualization\b", r"\bmatplotlib\b", r"\bseaborn\b", r"\btableau\b", r"\bpower\s*bi\b"],
    },
    {
        "skill": "PyTorch",
        "category": "Data Science",
        "aliases": [r"\bpytorch\b"],
    },
    {
        "skill": "TensorFlow",
        "category": "Data Science",
        "aliases": [r"\btensorflow\b", r"\btf\b"],
    },

    # --- Core Software Engineering & Systems ---
    {
        "skill": "Data Structures & Algorithms",
        "category": "Software Engineering",
        "aliases": [
            r"\bdata\s+structures\s+(?:and|&)\s+algorithms\b",
            r"\bdata\s+structures\b",
            r"\balgorithms\b",
            r"\bdsa\b"
        ],
    },
    {
        "skill": "Git",
        "category": "Software Engineering",
        "aliases": [r"\bgit\s+version\s+control\b", r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"],
    },
    {
        "skill": "Docker",
        "category": "DevOps",
        "aliases": [r"\bdocker\b", r"\bcontainers?\b", r"\bcontainerization\b"],
    },
    {
        "skill": "Kubernetes",
        "category": "DevOps",
        "aliases": [r"\bkubernetes\b", r"\bk8s\b"],
    },
    {
        "skill": "CI/CD",
        "category": "DevOps",
        "aliases": [r"\bci\/cd\b", r"\bcontinuous\s+integration\b", r"\bgithub\s+actions\b"],
    },
    {
        "skill": "Linux",
        "category": "Software Engineering",
        "aliases": [r"\blinux\b", r"\bunix\b", r"\bbash\b", r"\bshell\s+scripting\b"],
    },
    {
        "skill": "Object-Oriented Programming",
        "category": "Software Engineering",
        "aliases": [r"\bobject-oriented\s+programming\b", r"\bobject\s+oriented\s+programming\b", r"\boop\b"],
    },
    {
        "skill": "C++",
        "category": "Software Engineering",
        "aliases": [r"\bc\+\+\b", r"\bcpp\b"],
    },
    {
        "skill": "Java",
        "category": "Software Engineering",
        "aliases": [r"\bjava\b(?!\s*script)"],
    },
    {
        "skill": "C#",
        "category": "Software Engineering",
        "aliases": [r"\bc#\b", r"\bc-sharp\b", r"\b\.net\b"],
    },
    {
        "skill": "Go",
        "category": "Software Engineering",
        "aliases": [r"\bgolang\b", r"\bgo\s+language\b"],
    },
]

# Actionable Recommendation Templates
SKILL_ACTION_TEMPLATES: Dict[str, Dict[str, str]] = {
    "React": {
        "action": "Build a modular, component-driven project with React 19 (hooks, state management, API fetching) and document concepts in a clean README.",
        "topic": "React Hooks, Virtual DOM, Component Lifecycle, State Management"
    },
    "JavaScript": {
        "action": "Practice core JavaScript mechanics: asynchronous Promises, event loop, closures, destructuring, and ES6+ modules.",
        "topic": "Async/Await, Closures, DOM manipulation, ES6+"
    },
    "TypeScript": {
        "action": "Refactor a JavaScript project to TypeScript with strict type definitions, custom interfaces, and generics.",
        "topic": "Static Typing, Interfaces, Generics, Type Narrowing"
    },
    "Python": {
        "action": "Implement clean, idiomatic Python code with type hints, list/dict comprehensions, virtual environments, and unit tests.",
        "topic": "Pythonic conventions, OOP, pytest, standard libraries"
    },
    "SQL": {
        "action": "Practice relational schema design and complex SQL queries involving JOINs, GROUP BY aggregations, window functions, and indexing.",
        "topic": "Relational Modeling, Query Optimization, Subqueries, Normalization"
    },
    "FastAPI": {
        "action": "Develop a REST API with FastAPI, Pydantic validation models, OpenAPI docs, and SQLite/PostgreSQL integration.",
        "topic": "FastAPI Dependency Injection, Pydantic v2, ASGI, Swagger UI"
    },
    "Node.js": {
        "action": "Create a backend service with Node.js and Express handling authentication, middleware, and database connectivity.",
        "topic": "Event Loop, Express middleware, RESTful routing, npm modules"
    },
    "Docker": {
        "action": "Write a multi-stage Dockerfile to containerize a full-stack application and orchestrate services using docker-compose.",
        "topic": "Containerization, Port Mapping, Volumes, Multi-stage builds"
    },
    "Git": {
        "action": "Master collaborative Git workflows: feature branches, PR reviews, rebasing, resolving merge conflicts, and GitHub Actions.",
        "topic": "Git Branching, Pull Requests, Merge Conflicts, Semantic Commits"
    },
    "Pandas": {
        "action": "Analyze a real-world tabular dataset with Pandas: handling missing values, filtering, groupby aggregations, and pivot tables.",
        "topic": "DataFrame manipulation, Data Cleaning, Merging & Reshaping"
    },
    "Machine Learning": {
        "action": "Train, evaluate, and tune baseline regression and classification models with Scikit-learn; document train-test splits and evaluation metrics.",
        "topic": "Supervised Learning, Model Evaluation, Cross-validation, Hyperparameter tuning"
    },
    "Data Structures & Algorithms": {
        "action": "Practice 2-3 LeetCode problems daily focusing on arrays, two pointers, hash maps, binary search, trees, and dynamic programming.",
        "topic": "Time & Space Complexity (Big-O), Hash Tables, Trees, Graphs"
    },
    "REST APIs": {
        "action": "Design and document RESTful endpoints following standard HTTP methods, status codes, query filtering, and JSON payloads.",
        "topic": "HTTP verbs, Status Codes, Idempotency, API Versioning"
    },
    "HTML": {
        "action": "Ensure semantic HTML5 structure, ARIA accessibility attributes, and responsive meta tags on all user-facing web pages.",
        "topic": "Semantic Elements, Web Accessibility (a11y), Forms"
    },
    "CSS": {
        "action": "Master responsive CSS layouts using Flexbox, CSS Grid, media queries, and design token variables.",
        "topic": "Flexbox, Grid, Responsive Design, CSS Variables"
    },
    "Tailwind CSS": {
        "action": "Build a responsive dashboard component using Tailwind utility classes, custom theme tokens, and responsive prefixes.",
        "topic": "Utility-first CSS, Responsive Breakpoints, Custom Plugins"
    },
    "PostgreSQL": {
        "action": "Set up a local PostgreSQL database, write DDL schemas with foreign keys, and run EXPLAIN ANALYZE on complex queries.",
        "topic": "ACID Transactions, Foreign Keys, Query Optimization"
    },
    "MongoDB": {
        "action": "Model a document-based schema in MongoDB, create compound indexes, and practice aggregation pipelines.",
        "topic": "NoSQL Modeling, BSON, Aggregation Framework"
    },
    "Exploratory Data Analysis": {
        "action": "Perform thorough EDA on a Kaggle dataset: analyze distribution, detect outliers, compute correlations, and generate visualizations.",
        "topic": "Data Distributions, Correlation Matrices, Outlier Detection"
    },
    "Data Visualization": {
        "action": "Create insightful visual charts (boxplots, scatterplots, heatmaps) using Matplotlib, Seaborn, or interactive charting libraries.",
        "topic": "Visual Encoding, Chart Selection, Color Palettes"
    },
    "CI/CD": {
        "action": "Set up a GitHub Actions workflow that automatically runs test suites, linting, and build steps on every push.",
        "topic": "Automated Testing Pipelines, Build Triggers, Artifacts"
    },
    "Linux": {
        "action": "Practice shell navigation, file permissions (chmod/chown), process inspection (ps/top), and writing basic Bash scripts.",
        "topic": "Shell Scripting, SSH, File Systems, CLI tools"
    },
    "Object-Oriented Programming": {
        "action": "Design an extensible system applying encapsulation, inheritance, polymorphism, and SOLID design principles.",
        "topic": "SOLID Principles, Design Patterns, Class Hierarchies"
    }
}


# ============================================================================
# EXTRACTION & SECTION SEGMENTATION ENGINE
# ============================================================================

REQUIRED_SECTION_PATTERNS = [
    r"^(?:[\#\*\-\s]*)(?:basic|minimum|required|must[\s\-]have|core|mandatory)(?:\s+(?:qualifications?|requirements?|skills?|experience|criteria|what\s+you(?:'ll)?\s+need))?[\:\s]*$",
    r"^(?:[\#\*\-\s]*)(?:requirements?|qualifications?|what\s+we(?:'re)?\s+looking\s+for|what\s+you\s+bring|who\s+you\s+are)[\:\s]*$",
]

PREFERRED_SECTION_PATTERNS = [
    r"^(?:[\#\*\-\s]*)(?:preferred|desired|nice[\s\-]to[\s\-]have|bonus|plus(?:ses)?|good\s+to\s+have|additional)(?:\s+(?:qualifications?|requirements?|skills?|experience|plusses|criteria))?[\:\s]*$",
    r"^(?:[\#\*\-\s]*)(?:what\s+will\s+set\s+you\s+apart|bonus\s+points?|it(?:'s)?\s+a\s+plus)[\:\s]*$",
]


def segment_sections(text: str) -> Dict[str, str]:
    """
    Splits job description text into logical sections based on detected headers.
    Returns dictionary with keys 'required', 'preferred', and 'other'.
    """
    sections = {"required": "", "preferred": "", "other": ""}

    lines = text.split("\n")
    current_section = "other"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for Preferred headers
        is_pref_header = any(re.search(pat, stripped, re.IGNORECASE) for pat in PREFERRED_SECTION_PATTERNS)
        if is_pref_header:
            current_section = "preferred"
            continue

        # Check for Required headers
        is_req_header = any(re.search(pat, stripped, re.IGNORECASE) for pat in REQUIRED_SECTION_PATTERNS)
        if is_req_header:
            current_section = "required"
            continue

        # Check if line looks like an unrelated header that exits the requirements block
        is_generic_header = re.match(r"^[A-Z][A-Za-z\s]{3,25}:?$", stripped) and (
            "about" in stripped.lower()
            or "benefits" in stripped.lower()
            or "perks" in stripped.lower()
            or "company" in stripped.lower()
            or "salary" in stripped.lower()
        )
        if is_generic_header:
            current_section = "other"

        sections[current_section] += " " + stripped

    return sections


def extract_skills_from_text(text: str) -> List[Dict[str, str]]:
    """
    Finds all catalog skills present in the provided text snippet.
    Returns list of dicts: {"skill": str, "category": str, "matched_alias": str}
    """
    found_skills = []
    seen = set()

    for item in SKILL_CATALOG:
        skill_name = item["skill"]
        if skill_name in seen:
            continue

        for alias_pattern in item["aliases"]:
            match = re.search(alias_pattern, text, re.IGNORECASE)
            if match:
                matched_phrase = match.group(0).strip()
                found_skills.append({
                    "skill": skill_name,
                    "category": item["category"],
                    "matched_alias": matched_phrase
                })
                seen.add(skill_name)
                break

    return found_skills


def extract_other_requirements(text: str) -> List[Dict[str, str]]:
    """
    Detects education, experience level, and cloud/developer tool mentions.
    """
    other_reqs = []

    # Education patterns
    edu_patterns = [
        (r"\b(?:bachelor'?s?|master'?s?|b\.?s\.?|m\.?s\.?|ph\.?d\.?|degree)\b.*?\b(?:computer\s+science|software\s+engineering|stem|data\s+science|informatics|related\s+field)\b", "Education", "Degree in Computer Science or related STEM field"),
        (r"\bcurrently\s+enrolled\s+in\s+a\s+(?:bachelor|master|degree)\b", "Education", "Currently enrolled in university degree program"),
        (r"\b(?:recent\s+graduate|new\s+grad(?:uate)?|graduating\s+in\s+202[0-9])\b", "Education", "New graduate or upcoming graduation date")
    ]
    for pat, category, label in edu_patterns:
        if re.search(pat, text, re.IGNORECASE):
            other_reqs.append({"type": category, "detail": label})
            break

    # Experience level
    exp_patterns = [
        (r"\b(?:0[\-\s]2|1[\-\s]3|0[\-\s]1|\b1\+?|\b2\+?)\s+years?(?:\s+of)?\s+experience\b", "Experience", "Entry-level / 0-2 years of relevant experience or coursework"),
        (r"\b(?:internship|intern|co[\-\s]op)\b", "Experience", "Internship / Co-op student opportunity")
    ]
    for pat, category, label in exp_patterns:
        if re.search(pat, text, re.IGNORECASE):
            other_reqs.append({"type": category, "detail": label})
            break

    # Cloud platforms & tooling
    cloud_patterns = [
        (r"\b(?:aws|amazon\s+web\s+services)\b", "Tooling / Cloud", "Amazon Web Services (AWS)"),
        (r"\b(?:azure|microsoft\s+azure)\b", "Tooling / Cloud", "Microsoft Azure"),
        (r"\b(?:gcp|google\s+cloud(?:\s+platform)?)\b", "Tooling / Cloud", "Google Cloud Platform (GCP)")
    ]
    for pat, category, label in cloud_patterns:
        if re.search(pat, text, re.IGNORECASE):
            other_reqs.append({"type": category, "detail": label})

    return other_reqs


# ============================================================================
# MAIN ANALYSIS & COMPARISON ENGINE
# ============================================================================

def analyze_job_and_profile(
    job_description: str,
    resume_or_profile_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs transparent rule-based job description analysis and profile comparison.
    """
    cleaned_jd = job_description.strip()
    if len(cleaned_jd) < 20:
        raise ValueError("Job description is too short to analyze. Please provide at least a few sentences of job details.")

    # 1. Segment Job Description into Sections
    sections = segment_sections(cleaned_jd)
    req_text = sections["required"]
    pref_text = sections["preferred"]
    other_text = sections["other"]

    # 2. Extract Skills by Section
    required_skills = extract_skills_from_text(req_text)
    preferred_skills = extract_skills_from_text(pref_text)

    # Skills already claimed in required/preferred
    claimed_skills = {s["skill"] for s in required_skills} | {s["skill"] for s in preferred_skills}

    # Extract any remaining skills found in unclassified text
    unclassified_all = extract_skills_from_text(other_text)
    unclassified_skills = [s for s in unclassified_all if s["skill"] not in claimed_skills]

    # If no required or preferred sections were detected at all, all extracted skills are unclassified
    # But check sentence level context for clues:
    if not required_skills and not preferred_skills and unclassified_skills:
        reclassified_req = []
        reclassified_pref = []
        still_unclassified = []

        sentences = re.split(r"[\.\n\•\-\*\;]", cleaned_jd)
        for skill_item in unclassified_skills:
            skill = skill_item["skill"]
            # Look at sentences mentioning this skill
            matched_sentences = [
                sent for sent in sentences
                if re.search(r"\b" + re.escape(skill_item["matched_alias"]) + r"\b", sent, re.IGNORECASE)
            ]
            assigned = False
            for sent in matched_sentences:
                s_lower = sent.lower()
                if any(w in s_lower for w in ["must have", "required", "require", "minimum", "essential", "needed"]):
                    reclassified_req.append(skill_item)
                    assigned = True
                    break
                elif any(w in s_lower for w in ["plus", "preferred", "bonus", "nice to have", "desired", "ideal"]):
                    reclassified_pref.append(skill_item)
                    assigned = True
                    break

            if not assigned:
                still_unclassified.append(skill_item)

        required_skills = reclassified_req
        preferred_skills = reclassified_pref
        unclassified_skills = still_unclassified

    # 3. Detect Other Non-Technical Requirements
    other_requirements = extract_other_requirements(cleaned_jd)

    # 4. Extract User Profile Skills from Resume Text
    user_skills_list = []
    user_skill_map = {}
    if resume_or_profile_text and resume_or_profile_text.strip():
        user_skills_list = extract_skills_from_text(resume_or_profile_text)
        user_skill_map = {s["skill"]: s["matched_alias"] for s in user_skills_list}

    # 5. Compare Job Requirements vs. User Profile
    matching_required = []
    missing_required = []
    for s in required_skills:
        skill_name = s["skill"]
        if skill_name in user_skill_map:
            matching_required.append({
                "skill": skill_name,
                "category": s["category"],
                "type": "required",
                "matched_alias": s["matched_alias"],
                "user_matched_alias": user_skill_map[skill_name],
                "explanation": f"Recognized '{s['matched_alias']}' in job requirements and '{user_skill_map[skill_name]}' in your profile."
            })
        else:
            missing_required.append({
                "skill": skill_name,
                "category": s["category"],
                "type": "required",
                "matched_alias": s["matched_alias"],
                "explanation": f"Identified '{s['matched_alias']}' as required by employer, but not detected in your resume/profile."
            })

    matching_preferred = []
    missing_preferred = []
    for s in preferred_skills:
        skill_name = s["skill"]
        if skill_name in user_skill_map:
            matching_preferred.append({
                "skill": skill_name,
                "category": s["category"],
                "type": "preferred",
                "matched_alias": s["matched_alias"],
                "user_matched_alias": user_skill_map[skill_name],
                "explanation": f"Recognized '{s['matched_alias']}' in preferred qualifications and '{user_skill_map[skill_name]}' in your profile."
            })
        else:
            missing_preferred.append({
                "skill": skill_name,
                "category": s["category"],
                "type": "preferred",
                "matched_alias": s["matched_alias"],
                "explanation": f"Identified '{s['matched_alias']}' in preferred qualifications; not detected in your resume/profile."
            })

    matching_unclassified = []
    missing_unclassified = []
    for s in unclassified_skills:
        skill_name = s["skill"]
        if skill_name in user_skill_map:
            matching_unclassified.append({
                "skill": skill_name,
                "category": s["category"],
                "type": "unclassified",
                "matched_alias": s["matched_alias"],
                "user_matched_alias": user_skill_map[skill_name],
                "explanation": f"Detected '{s['matched_alias']}' in job posting and '{user_skill_map[skill_name]}' in your profile."
            })
        else:
            missing_unclassified.append({
                "skill": skill_name,
                "category": s["category"],
                "type": "unclassified",
                "matched_alias": s["matched_alias"],
                "explanation": f"Mentioned in job description as '{s['matched_alias']}'; not detected in your profile."
            })

    # Combined summary lists
    matching_skills = matching_required + matching_preferred + matching_unclassified
    missing_skills = missing_required + missing_preferred + missing_unclassified

    # 6. Calculate Transparent Match Score
    total_req = len(required_skills)
    total_pref = len(preferred_skills)
    total_unclass = len(unclassified_skills)
    match_score: Optional[float] = None
    score_breakdown: Dict[str, Any] = {}

    if not resume_or_profile_text or not resume_or_profile_text.strip():
        score_breakdown = {
            "has_profile": False,
            "message": "Enter your skills or paste resume text above to compute your match score."
        }
    elif total_req == 0 and total_pref == 0 and total_unclass == 0:
        match_score = None
        score_breakdown = {
            "has_profile": True,
            "message": "No recognizable technical skills were detected in the job description to calculate a coverage percentage."
        }
    elif total_req > 0 and total_pref > 0:
        req_cov = len(matching_required) / total_req
        pref_cov = len(matching_preferred) / total_pref
        raw_score = (0.7 * req_cov + 0.3 * pref_cov) * 100
        match_score = round(raw_score, 1)
        score_breakdown = {
            "has_profile": True,
            "required_coverage": f"{len(matching_required)} of {total_req} ({round(req_cov * 100)}%)",
            "preferred_coverage": f"{len(matching_preferred)} of {total_pref} ({round(pref_cov * 100)}%)",
            "weighting": "70% Required + 30% Preferred",
            "formula": "Score = (0.70 × Required Coverage) + (0.30 × Preferred Coverage)",
            "message": "Rule-based estimate of keyword coverage against explicit job requirements."
        }
    elif total_req > 0 and total_pref == 0:
        req_cov = len(matching_required) / total_req
        match_score = round(req_cov * 100, 1)
        score_breakdown = {
            "has_profile": True,
            "required_coverage": f"{len(matching_required)} of {total_req} ({round(req_cov * 100)}%)",
            "preferred_coverage": "None detected in posting",
            "weighting": "100% Required",
            "formula": "Score = Required Skills Coverage (no preferred section detected)",
            "message": "Calculated entirely from explicit required qualifications."
        }
    elif total_req == 0 and total_pref > 0:
        pref_cov = len(matching_preferred) / total_pref
        match_score = round(pref_cov * 100, 1)
        score_breakdown = {
            "has_profile": True,
            "required_coverage": "None explicitly labeled",
            "preferred_coverage": f"{len(matching_preferred)} of {total_pref} ({round(pref_cov * 100)}%)",
            "weighting": "100% Preferred",
            "formula": "Score = Preferred Skills Coverage",
            "message": "Calculated from preferred qualifications detected in posting."
        }
    else:
        # Only unclassified skills detected
        unclass_cov = len(matching_unclassified) / total_unclass
        match_score = round(unclass_cov * 100, 1)
        score_breakdown = {
            "has_profile": True,
            "required_coverage": f"{len(matching_unclassified)} of {total_unclass} ({round(unclass_cov * 100)}%)",
            "preferred_coverage": "Unclassified headings",
            "weighting": "100% General Skills Coverage",
            "formula": "Score = Matching Skills / Total Detected Skills",
            "message": "Posting lacks explicit 'Required' vs 'Preferred' headers; calculated across all detected technical skills."
        }

    # 7. Generate Prioritized Actionable Recommendations
    recommendations = []
    rec_counter = 1

    # High Priority: Missing required skills
    for m in missing_required:
        skill_name = m["skill"]
        template = SKILL_ACTION_TEMPLATES.get(skill_name, {
            "action": f"Review standard documentation and build a focused sample project demonstrating practical competency in {skill_name}.",
            "topic": f"{skill_name} core fundamentals and best practices"
        })
        recommendations.append({
            "id": f"rec-{rec_counter}",
            "skill": skill_name,
            "priority": "High",
            "reason": f"Required qualification in {skill_name} not detected in your current profile.",
            "suggested_action": template["action"],
            "learning_topic": template["topic"],
            "completed": False
        })
        rec_counter += 1

    # Medium Priority: Missing preferred skills
    for m in missing_preferred:
        skill_name = m["skill"]
        template = SKILL_ACTION_TEMPLATES.get(skill_name, {
            "action": f"Familiarize yourself with {skill_name} basics to stand out as a competitive applicant.",
            "topic": f"{skill_name} introductory concepts"
        })
        recommendations.append({
            "id": f"rec-{rec_counter}",
            "skill": skill_name,
            "priority": "Medium",
            "reason": f"Preferred bonus skill in {skill_name} that can distinguish your application.",
            "suggested_action": template["action"],
            "learning_topic": template["topic"],
            "completed": False
        })
        rec_counter += 1

    # Normal Priority: Missing unclassified skills (if no required/preferred existed)
    if total_req == 0 and total_pref == 0:
        for m in missing_unclassified:
            skill_name = m["skill"]
            template = SKILL_ACTION_TEMPLATES.get(skill_name, {
                "action": f"Explore practical applications of {skill_name} relevant to this job description.",
                "topic": f"{skill_name} overview"
            })
            recommendations.append({
                "id": f"rec-{rec_counter}",
                "skill": skill_name,
                "priority": "Normal",
                "reason": f"Technical skill mentioned in posting: {skill_name}.",
                "suggested_action": template["action"],
                "learning_topic": template["topic"],
                "completed": False
            })
            rec_counter += 1

    return {
        "match_score": match_score,
        "score_breakdown": score_breakdown,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "unclassified_skills": unclassified_skills,
        "other_requirements": other_requirements,
        "user_detected_skills": user_skills_list,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "matching_required": matching_required,
        "missing_required": missing_required,
        "matching_preferred": matching_preferred,
        "missing_preferred": missing_preferred,
        "recommendations": recommendations,
        "disclaimer": "This score is a transparent, rule-based estimate of keyword and skill coverage. It is not an AI hiring prediction or guarantee of interview selection."
    }
