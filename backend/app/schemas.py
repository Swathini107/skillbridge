from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator, Field


class HealthResponse(BaseModel):
    status: str
    app: str


# --- User Schemas ---
class UserBase(BaseModel):
    name: str
    email: str


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Job Application Schemas ---
VALID_STATUSES = ["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected", "Withdrawn"]
VALID_WORK_MODES = ["On-site", "Hybrid", "Remote"]
VALID_EMPLOYMENT_TYPES = ["Internship", "Full-time", "Part-time"]


class JobApplicationBase(BaseModel):
    company_name: str
    job_title: str
    application_status: Optional[str] = "Saved"
    job_description: Optional[str] = Field(None, max_length=50000)
    job_url: Optional[str] = Field(None, max_length=1000)
    company_url: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    work_mode: Optional[str] = None
    employment_type: Optional[str] = None
    skills: Optional[str] = Field(None, max_length=5000)
    deadline: Optional[date] = None
    application_date: Optional[date] = None
    interview_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=20000)

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        trimmed = v.strip() if v else ""
        if not trimmed:
            raise ValueError("Company name is required and cannot be blank.")
        return trimmed

    @field_validator("job_title")
    @classmethod
    def validate_job_title(cls, v: str) -> str:
        trimmed = v.strip() if v else ""
        if not trimmed:
            raise ValueError("Job title/role is required and cannot be blank.")
        return trimmed

    @field_validator("application_status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if not v:
            return "Saved"
        # Map common case variants
        normalized = v.capitalize()
        # Handle special cases like 'Interviewing' -> 'Interview'
        if normalized == "Interviewing":
            normalized = "Interview"
        if normalized not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values: {', '.join(VALID_STATUSES)}")
        return normalized

    @field_validator("work_mode")
    @classmethod
    def validate_work_mode(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        # Normalize
        lookup = {
            "on-site": "On-site",
            "onsite": "On-site",
            "hybrid": "Hybrid",
            "remote": "Remote"
        }
        val = lookup.get(v.strip().lower())
        if not val:
            raise ValueError(f"Invalid work mode '{v}'. Allowed values: {', '.join(VALID_WORK_MODES)}")
        return val

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        lookup = {
            "internship": "Internship",
            "full-time": "Full-time",
            "fulltime": "Full-time",
            "part-time": "Part-time",
            "parttime": "Part-time"
        }
        val = lookup.get(v.strip().lower())
        if not val:
            raise ValueError(f"Invalid employment type '{v}'. Allowed values: {', '.join(VALID_EMPLOYMENT_TYPES)}")
        return val


class JobApplicationCreate(JobApplicationBase):
    user_id: Optional[int] = 1


class JobApplicationUpdate(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    application_status: Optional[str] = None
    job_description: Optional[str] = None
    job_url: Optional[str] = None
    company_url: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    employment_type: Optional[str] = None
    skills: Optional[str] = None
    deadline: Optional[date] = None
    application_date: Optional[date] = None
    interview_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Company name cannot be blank.")
            return trimmed
        return v

    @field_validator("job_title")
    @classmethod
    def validate_job_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Job title cannot be blank.")
            return trimmed
        return v

    @field_validator("application_status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            normalized = v.capitalize()
            if normalized == "Interviewing":
                normalized = "Interview"
            if normalized not in VALID_STATUSES:
                raise ValueError(f"Invalid status '{v}'. Allowed values: {', '.join(VALID_STATUSES)}")
            return normalized
        return v


class JobApplicationStatusUpdate(BaseModel):
    application_status: str

    @field_validator("application_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        normalized = v.capitalize()
        if normalized == "Interviewing":
            normalized = "Interview"
        if normalized not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed values: {', '.join(VALID_STATUSES)}")
        return normalized


class JobApplicationRead(JobApplicationBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatsResponse(BaseModel):
    total_saved_jobs: int
    applications_submitted: int
    interviews_in_progress: int
    offers_received: int
    total_jobs: int
    approaching_deadlines: int
    status_breakdown: Dict[str, int]


# --- Interview Question Schemas ---
class InterviewQuestionBase(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    question_text: str
    question_category: Optional[str] = "TECHNICAL"
    interview_round: Optional[str] = "FIRST_ROUND"
    personal_answer: Optional[str] = None
    practice_status: Optional[str] = "NOT_PRACTICED"


class InterviewQuestionCreate(InterviewQuestionBase):
    user_id: int


class InterviewQuestionRead(InterviewQuestionBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Job Description Analyzer Schemas ---
class AnalyzeRequest(BaseModel):
    job_description: str = Field(..., max_length=50000)
    resume_or_profile_text: Optional[str] = Field(None, max_length=50000)
    job_id: Optional[int] = None
    company_name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=200)
    save_analysis: Optional[bool] = True

    @field_validator("job_description")
    @classmethod
    def validate_job_description(cls, v: str) -> str:
        trimmed = v.strip() if v else ""
        if not trimmed:
            raise ValueError("Job description cannot be empty. Please paste or select a job description.")
        if len(trimmed) < 20:
            raise ValueError("Job description is too short (minimum 20 characters required for meaningful analysis).")
        return trimmed


class AnalysisResponse(BaseModel):
    id: Optional[int] = None
    job_id: Optional[int] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    match_score: Optional[float] = None
    score_breakdown: Dict[str, Any]
    required_skills: List[Dict[str, Any]]
    preferred_skills: List[Dict[str, Any]]
    unclassified_skills: List[Dict[str, Any]]
    other_requirements: List[Dict[str, Any]]
    user_detected_skills: List[Dict[str, Any]]
    matching_skills: List[Dict[str, Any]]
    missing_skills: List[Dict[str, Any]]
    matching_required: List[Dict[str, Any]]
    missing_required: List[Dict[str, Any]]
    matching_preferred: List[Dict[str, Any]]
    missing_preferred: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    disclaimer: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisHistoryItem(BaseModel):
    id: int
    job_id: Optional[int] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    match_score: Optional[float] = None
    matching_count: int
    missing_count: int
    required_count: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# INTERVIEW MEMORY BANK SCHEMAS
# ============================================================================

VALID_ROUND_TYPES = ["Technical", "HR", "Aptitude", "Behavioral", "System Design"]
VALID_DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
VALID_SOURCES = ["Personal interview", "Recruiter", "Online assessment", "Peer", "Other"]
VALID_REVIEW_STATUSES = ["New", "Learning", "Confident"]


class InterviewQuestionBase(BaseModel):
    question_text: str = Field(..., max_length=5000)
    round_type: Optional[str] = "Technical"
    topic: Optional[str] = Field(None, max_length=200)
    difficulty: Optional[str] = "Intermediate"
    company_name: Optional[str] = Field(None, max_length=200)
    job_role: Optional[str] = Field(None, max_length=200)
    job_id: Optional[int] = None
    interview_date: Optional[date] = None
    source: Optional[str] = "Personal interview"
    original_answer: Optional[str] = Field(None, max_length=20000)
    expected_answer: Optional[str] = Field(None, max_length=20000)
    improvement_notes: Optional[str] = Field(None, max_length=20000)
    tags: Optional[str] = Field(None, max_length=2000)
    review_status: Optional[str] = "New"

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v: str) -> str:
        trimmed = v.strip() if v else ""
        if not trimmed:
            raise ValueError("Question text is required and cannot be blank.")
        if len(trimmed) < 5:
            raise ValueError("Question text must be at least 5 characters long.")
        return trimmed

    @field_validator("round_type")
    @classmethod
    def validate_round_type(cls, v: Optional[str]) -> str:
        if not v:
            return "Technical"
        # Map common case variants
        lookup = {
            "technical": "Technical",
            "hr": "HR",
            "aptitude": "Aptitude",
            "behavioral": "Behavioral",
            "system design": "System Design",
            "system_design": "System Design"
        }
        val = lookup.get(v.strip().lower())
        if not val or val not in VALID_ROUND_TYPES:
            raise ValueError(f"Invalid round type '{v}'. Allowed values: {', '.join(VALID_ROUND_TYPES)}")
        return val

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> str:
        if not v:
            return "Intermediate"
        lookup = {
            "beginner": "Beginner",
            "intermediate": "Intermediate",
            "advanced": "Advanced"
        }
        val = lookup.get(v.strip().lower())
        if not val or val not in VALID_DIFFICULTIES:
            raise ValueError(f"Invalid difficulty '{v}'. Allowed values: {', '.join(VALID_DIFFICULTIES)}")
        return val

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: Optional[str]) -> str:
        if not v:
            return "Personal interview"
        lookup = {
            "personal interview": "Personal interview",
            "recruiter": "Recruiter",
            "online assessment": "Online assessment",
            "peer": "Peer",
            "other": "Other"
        }
        val = lookup.get(v.strip().lower())
        if not val or val not in VALID_SOURCES:
            return "Other"
        return val

    @field_validator("review_status")
    @classmethod
    def validate_review_status(cls, v: Optional[str]) -> str:
        if not v:
            return "New"
        lookup = {
            "new": "New",
            "learning": "Learning",
            "confident": "Confident"
        }
        val = lookup.get(v.strip().lower())
        if not val or val not in VALID_REVIEW_STATUSES:
            raise ValueError(f"Invalid review status '{v}'. Allowed values: {', '.join(VALID_REVIEW_STATUSES)}")
        return val


class InterviewQuestionCreate(InterviewQuestionBase):
    pass


class InterviewQuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    round_type: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    company_name: Optional[str] = None
    job_role: Optional[str] = None
    job_id: Optional[int] = None
    interview_date: Optional[date] = None
    source: Optional[str] = None
    original_answer: Optional[str] = None
    expected_answer: Optional[str] = None
    improvement_notes: Optional[str] = None
    tags: Optional[str] = None
    review_status: Optional[str] = None

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Question text cannot be blank.")
        if len(trimmed) < 5:
            raise ValueError("Question text must be at least 5 characters long.")
        return trimmed

    @field_validator("round_type")
    @classmethod
    def validate_round_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        lookup = {
            "technical": "Technical",
            "hr": "HR",
            "aptitude": "Aptitude",
            "behavioral": "Behavioral",
            "system design": "System Design",
            "system_design": "System Design"
        }
        val = lookup.get(v.strip().lower())
        if not val or val not in VALID_ROUND_TYPES:
            raise ValueError(f"Invalid round type '{v}'. Allowed values: {', '.join(VALID_ROUND_TYPES)}")
        return val

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        lookup = {
            "beginner": "Beginner",
            "intermediate": "Intermediate",
            "advanced": "Advanced"
        }
        val = lookup.get(v.strip().lower())
        if not val or val not in VALID_DIFFICULTIES:
            raise ValueError(f"Invalid difficulty '{v}'. Allowed values: {', '.join(VALID_DIFFICULTIES)}")
        return val

    @field_validator("review_status")
    @classmethod
    def validate_review_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        lookup = {
            "new": "New",
            "learning": "Learning",
            "confident": "Confident"
        }
        val = lookup.get(v.strip().lower())
        if not val or val not in VALID_REVIEW_STATUSES:
            raise ValueError(f"Invalid review status '{v}'. Allowed values: {', '.join(VALID_REVIEW_STATUSES)}")
        return val


class InterviewQuestionStatusUpdate(BaseModel):
    review_status: str

    @field_validator("review_status")
    @classmethod
    def validate_review_status(cls, v: str) -> str:
        lookup = {
            "new": "New",
            "learning": "Learning",
            "confident": "Confident"
        }
        val = lookup.get(v.strip().lower()) if v else None
        if not val or val not in VALID_REVIEW_STATUSES:
            raise ValueError(f"Invalid review status '{v}'. Allowed values: {', '.join(VALID_REVIEW_STATUSES)}")
        return val


class InterviewQuestionRead(InterviewQuestionBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QuestionStatsResponse(BaseModel):
    total: int
    technical: int
    hr_behavioral: int
    confident: int
    needs_review: int
    by_round: Dict[str, int]
    by_status: Dict[str, int]
    by_difficulty: Dict[str, int]


# ============================================================================
# MOCK INTERVIEW PRACTICE STUDIO SCHEMAS
# ============================================================================

VALID_PRACTICE_ROUNDS = ["Technical", "HR", "Aptitude", "Behavioral", "System Design"]
VALID_PRACTICE_DIFFICULTIES = ["Beginner", "Intermediate", "Advanced", "Mixed"]
VALID_PRACTICE_STATUSES = ["In Progress", "Completed", "Abandoned"]
VALID_QUESTION_SOURCES = ["Memory Bank", "Company/Job", "Topic", "Custom"]

# Criteria by round type
UNIVERSAL_CRITERIA = ["clarity", "completeness", "confidence"]
TECHNICAL_CRITERIA = ["technical_correctness", "problem_solving"]
HR_CRITERIA = ["answer_structure", "specific_examples"]

CRITERIA_LABELS = {
    "clarity": "Clarity of Communication",
    "completeness": "Completeness & Depth",
    "confidence": "Delivery Confidence",
    "technical_correctness": "Technical Correctness",
    "problem_solving": "Problem-Solving Approach",
    "answer_structure": "Answer Structure (e.g. STAR)",
    "specific_examples": "Specific & Concrete Examples"
}


class CustomQuestionInput(BaseModel):
    """Manually added question for current practice session."""
    question_text: str
    round_type: Optional[str] = "Technical"
    topic: Optional[str] = "Custom"
    difficulty: Optional[str] = "Intermediate"
    expected_answer: Optional[str] = None

    @field_validator("question_text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        trimmed = v.strip() if v else ""
        if not trimmed or len(trimmed) < 5:
            raise ValueError("Custom question text must be at least 5 characters long.")
        return trimmed


class PracticePreviewRequest(BaseModel):
    """Payload to preview questions and personalization matching before starting."""
    session_name: Optional[str] = "Mock Interview Session"
    round_type: Optional[str] = "Technical"
    job_id: Optional[int] = None
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    question_source: Optional[str] = "Memory Bank"
    selected_topic: Optional[str] = None
    question_count: Optional[int] = 5
    difficulty: Optional[str] = "Mixed"
    time_limit_minutes: Optional[int] = None
    custom_question: Optional[CustomQuestionInput] = None


class PracticePreviewQuestion(BaseModel):
    id: Optional[int] = None
    question_text: str
    round_type: str
    topic: Optional[str] = None
    difficulty: str
    company_name: Optional[str] = None
    job_role: Optional[str] = None
    expected_answer: Optional[str] = None
    relevance_reason: Optional[str] = None


class PracticePreviewResponse(BaseModel):
    total_available: int
    requested_count: int
    selected_count: int
    warning: Optional[str] = None
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    personalized_skills_targeted: List[str] = []
    questions: List[PracticePreviewQuestion] = []


class PracticeSessionCreate(BaseModel):
    """Payload to initialize and begin a practice session."""
    session_name: str
    round_type: Optional[str] = "Technical"
    job_id: Optional[int] = None
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    question_source: Optional[str] = "Memory Bank"
    selected_topic: Optional[str] = None
    question_count: Optional[int] = 5
    difficulty: Optional[str] = "Mixed"
    time_limit_minutes: Optional[int] = None
    custom_question: Optional[CustomQuestionInput] = None
    user_id: Optional[int] = 1

    @field_validator("session_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip() if v else ""
        if not trimmed:
            raise ValueError("Session name is required and cannot be blank.")
        return trimmed

    @field_validator("round_type")
    @classmethod
    def validate_round(cls, v: Optional[str]) -> str:
        if not v:
            return "Technical"
        lookup = {
            "technical": "Technical",
            "hr": "HR",
            "aptitude": "Aptitude",
            "behavioral": "Behavioral",
            "system design": "System Design",
            "system_design": "System Design"
        }
        val = lookup.get(v.strip().lower())
        if not val or val not in VALID_PRACTICE_ROUNDS:
            raise ValueError(f"Invalid round type '{v}'. Allowed values: {', '.join(VALID_PRACTICE_ROUNDS)}")
        return val

    @field_validator("difficulty")
    @classmethod
    def validate_diff(cls, v: Optional[str]) -> str:
        if not v:
            return "Mixed"
        lookup = {
            "beginner": "Beginner",
            "intermediate": "Intermediate",
            "advanced": "Advanced",
            "mixed": "Mixed"
        }
        val = lookup.get(v.strip().lower())
        if not val or val not in VALID_PRACTICE_DIFFICULTIES:
            raise ValueError(f"Invalid difficulty '{v}'. Allowed values: {', '.join(VALID_PRACTICE_DIFFICULTIES)}")
        return val

    @field_validator("question_count")
    @classmethod
    def validate_count(cls, v: Optional[int]) -> int:
        if v is None:
            return 5
        if v not in [5, 10, 15]:
            # Default to nearest or allow 1-15 for custom tests
            if v < 1:
                return 5
            if v > 15:
                return 15
        return v

    @field_validator("time_limit_minutes")
    @classmethod
    def validate_time_limit(cls, v: Optional[int]) -> Optional[int]:
        if v in [None, 0, -1]:
            return None
        if v not in [5, 10, 15, 20]:
            # Accept any reasonable positive integer up to 120 minutes
            if 1 <= v <= 120:
                return v
            raise ValueError("Time limit must be 5, 10, 15, 20 minutes, or None (no limit).")
        return v


class PracticeAnswerUpdate(BaseModel):
    """Payload to save answer or submit self-assessment ratings."""
    answer_text: Optional[str] = Field(None, max_length=30000)
    is_attempted: Optional[bool] = None
    is_skipped: Optional[bool] = None
    self_ratings: Optional[Dict[str, int]] = None
    went_well: Optional[str] = Field(None, max_length=10000)
    was_difficult: Optional[str] = Field(None, max_length=10000)
    need_to_learn: Optional[str] = Field(None, max_length=10000)
    better_approach: Optional[str] = Field(None, max_length=10000)
    time_spent_seconds: Optional[int] = None

    @field_validator("self_ratings")
    @classmethod
    def validate_ratings(cls, v: Optional[Dict[str, int]]) -> Optional[Dict[str, int]]:
        if not v:
            return v
        for criterion, score in v.items():
            if not isinstance(score, int) or score < 1 or score > 5:
                raise ValueError(f"Rating for '{criterion}' must be an integer between 1 and 5.")
        return v


class PracticeAnswerRead(BaseModel):
    id: int
    session_id: int
    question_id: Optional[int] = None
    order_index: int
    question_text: str
    round_type: str
    topic: Optional[str] = None
    difficulty: str
    expected_answer: Optional[str] = None
    answer_text: Optional[str] = None
    is_attempted: bool = False
    is_skipped: bool = False
    self_ratings: Optional[Dict[str, Any]] = None
    went_well: Optional[str] = None
    was_difficult: Optional[str] = None
    need_to_learn: Optional[str] = None
    better_approach: Optional[str] = None
    time_spent_seconds: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PracticeSessionRead(BaseModel):
    id: int
    user_id: int
    job_id: Optional[int] = None
    session_name: str
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    round_type: str
    question_source: str
    selected_topic: Optional[str] = None
    difficulty: str
    time_limit_minutes: Optional[int] = None
    status: str
    total_questions: int
    current_question_index: int
    duration_seconds: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    answers: List[PracticeAnswerRead] = []

    model_config = ConfigDict(from_attributes=True)


class PracticeSessionListItem(BaseModel):
    """Summary item for session history list."""
    id: int
    session_name: str
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    round_type: str
    difficulty: str
    status: str
    total_questions: int
    attempted_count: int
    average_score: Optional[float] = None
    duration_seconds: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PracticeSessionReport(BaseModel):
    """Comprehensive performance summary report for completed practice sessions."""
    session_id: int
    session_name: str
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    round_type: str
    difficulty: str
    status: str
    duration_seconds: int
    duration_formatted: str
    time_limit_minutes: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_questions: int
    questions_attempted: int
    questions_skipped: int
    questions_unanswered: int
    completion_rate_percentage: float
    scores_available: bool
    overall_average_score: Optional[float] = None
    criteria_averages: Dict[str, float] = {}
    strongest_areas: List[str] = []
    areas_for_improvement: List[str] = []
    recommendations: List[str] = []
    answers: List[PracticeAnswerRead] = []


# ============================================================================
# UNIFIED CAREER PREPARATION DASHBOARD SCHEMAS
# ============================================================================

class DashboardSummaryCards(BaseModel):
    total_saved_jobs: int
    applications_submitted: int
    interviews_in_progress: int
    offers_received: int
    rejected_count: int
    withdrawn_count: int
    total_jobs: int
    upcoming_deadlines_count: int
    total_questions_saved: int
    questions_confident: int
    questions_learning: int
    sessions_completed: int
    sessions_in_progress: int
    average_self_assessment: Optional[float] = None
    total_resumes_saved: int = 0


class FunnelStageItem(BaseModel):
    stage: str
    label: str
    count: int
    color: str


class ApplicationFunnelData(BaseModel):
    pipeline: List[FunnelStageItem]
    outcomes: List[FunnelStageItem]


class UpcomingDeadlineItem(BaseModel):
    id: int
    company_name: str
    job_title: str
    deadline: str
    application_status: str
    days_remaining: int
    is_overdue: bool
    urgency: str  # "overdue", "urgent", "soon", "upcoming"


class SkillGapItem(BaseModel):
    skill: str
    frequency: int
    associated_jobs: List[str]


class LearningTaskItem(BaseModel):
    skill: str
    type: str  # "Required" or "Preferred"
    task: str
    job_id: Optional[int] = None
    job_company: Optional[str] = None


class SkillGapSummary(BaseModel):
    total_analyses: int
    frequently_missing_required: List[SkillGapItem] = []
    frequently_missing_preferred: List[SkillGapItem] = []
    suggested_learning_tasks: List[LearningTaskItem] = []


class RecentSessionSummary(BaseModel):
    id: int
    session_name: str
    round_type: str
    status: str
    score: Optional[float] = None
    date: Optional[str] = None
    attempted_count: int
    total_questions: int


class ActiveSessionResumeItem(BaseModel):
    id: int
    session_name: str
    round_type: str
    current_index: int
    total_questions: int


class TopicPracticeItem(BaseModel):
    topic: str
    unmastered_count: int


class InterviewPrepSummary(BaseModel):
    total_questions: int
    confident_count: int
    learning_count: int
    new_count: int
    recent_sessions: List[RecentSessionSummary] = []
    topics_needing_practice: List[TopicPracticeItem] = []
    active_session_to_resume: Optional[ActiveSessionResumeItem] = None


class RecommendationItem(BaseModel):
    id: str
    category: str  # "deadline", "analysis", "skill_gap", "question_review", "mock_interview", "resume", "general"
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    action_text: str
    action_link: str


class RecentResumeSummary(BaseModel):
    id: int
    title: str
    target_role: Optional[str] = None
    target_job_id: Optional[int] = None
    target_company: Optional[str] = None
    completeness_score: Optional[int] = None
    has_unresolved_warnings: bool = False
    critical_issues_count: int = 0
    updated_at: Optional[datetime] = None


class ResumeOverviewSummary(BaseModel):
    total_resumes: int
    most_recent_resume: Optional[RecentResumeSummary] = None


class DashboardSummaryResponse(BaseModel):
    summary_cards: DashboardSummaryCards
    application_funnel: ApplicationFunnelData
    upcoming_deadlines: List[UpcomingDeadlineItem] = []
    skill_gap_summary: SkillGapSummary
    interview_prep_summary: InterviewPrepSummary
    resume_overview: Optional[ResumeOverviewSummary] = None
    recommended_next_steps: List[RecommendationItem] = []


# ============================================================================
# ATS-FRIENDLY RESUME BUILDER SCHEMAS
# ============================================================================

class ContactInfo(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""


class SkillCategory(BaseModel):
    category: str
    items: List[str] = []


class EducationItem(BaseModel):
    id: Optional[str] = None
    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: str = ""
    graduation_date: str = ""
    gpa_or_grade: str = ""
    coursework: str = ""


class ProjectItem(BaseModel):
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    technologies: List[str] = []
    github_url: str = ""
    live_url: str = ""
    bullets: List[str] = []


class ExperienceItem(BaseModel):
    id: Optional[str] = None
    organization: str = ""
    job_title: str = ""
    employment_type: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: List[str] = []


class CertificationItem(BaseModel):
    id: Optional[str] = None
    name: str = ""
    issuer: str = ""
    date: str = ""
    url: str = ""


class AchievementItem(BaseModel):
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    date: str = ""


class LeadershipItem(BaseModel):
    id: Optional[str] = None
    role: str = ""
    organization: str = ""
    bullets: List[str] = []


class LanguageItem(BaseModel):
    id: Optional[str] = None
    language: str = ""
    proficiency: str = ""


class AdditionalSections(BaseModel):
    certifications: List[CertificationItem] = []
    achievements: List[AchievementItem] = []
    leadership: List[LeadershipItem] = []
    languages: List[LanguageItem] = []


class SectionConfig(BaseModel):
    order: List[str] = [
        "contact",
        "summary",
        "skills",
        "education",
        "projects",
        "experience",
        "certifications",
        "achievements",
        "leadership",
        "languages"
    ]
    enabled: Dict[str, bool] = {
        "contact": True,
        "summary": True,
        "skills": True,
        "education": True,
        "projects": True,
        "experience": True,
        "certifications": False,
        "achievements": False,
        "leadership": False,
        "languages": False
    }


class ResumeBase(BaseModel):
    title: str = Field("Software Engineer Resume", max_length=200)
    target_job_id: Optional[int] = None
    target_role: Optional[str] = Field(None, max_length=200)
    template_id: str = "classic_ats"
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = Field("", max_length=10000)
    skills: List[SkillCategory] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    additional_sections: AdditionalSections = Field(default_factory=AdditionalSections)
    section_config: SectionConfig = Field(default_factory=SectionConfig)


class ResumeCreate(ResumeBase):
    pass


class ResumeUpdate(BaseModel):
    title: Optional[str] = None
    target_job_id: Optional[int] = None
    target_role: Optional[str] = None
    template_id: Optional[str] = None
    contact_info: Optional[ContactInfo] = None
    summary: Optional[str] = None
    skills: Optional[List[SkillCategory]] = None
    education: Optional[List[EducationItem]] = None
    projects: Optional[List[ProjectItem]] = None
    experience: Optional[List[ExperienceItem]] = None
    additional_sections: Optional[AdditionalSections] = None
    section_config: Optional[SectionConfig] = None


class ResumeRead(ResumeBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeListItem(BaseModel):
    id: int
    title: str
    target_role: Optional[str] = None
    target_job_id: Optional[int] = None
    target_company: Optional[str] = None
    template_id: str
    completeness_score: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewIssueItem(BaseModel):
    rule_id: str
    category: str  # "critical", "improvement", "optional"
    title: str
    detail: str
    action_hint: str
    section: Optional[str] = None


class BulletInsightItem(BaseModel):
    section: str
    item_title: str
    bullet_index: int
    bullet_text: str
    has_action_verb: bool
    detected_action_verb: Optional[str] = None
    has_vague_phrase: bool
    flagged_phrase: Optional[str] = None
    improvement_suggestion: Optional[str] = None


class ResumeReviewResponse(BaseModel):
    resume_id: int
    overall_score: int  # 0 to 100
    score_breakdown: Dict[str, int]
    critical_issues: List[ReviewIssueItem] = []
    recommended_improvements: List[ReviewIssueItem] = []
    optional_refinements: List[ReviewIssueItem] = []
    bullet_insights: List[BulletInsightItem] = []
    summary_critique: str


class KeywordCategoryItem(BaseModel):
    keyword: str
    category: Optional[str] = None
    location_in_resume: Optional[str] = None


class ResumeTailorResponse(BaseModel):
    resume_id: int
    job_id: int
    company_name: str
    job_title: str
    keyword_match_score: float  # 0 to 100 percentage
    keyword_match_percentage: Optional[float] = None
    present_keywords: List[KeywordCategoryItem] = []
    missing_required_keywords: List[KeywordCategoryItem] = []
    missing_preferred_keywords: List[KeywordCategoryItem] = []
    alignment_suggestions: List[str] = []
    truthful_alignment_suggestions: List[str] = []
    recommended_additions: List[str] = []
