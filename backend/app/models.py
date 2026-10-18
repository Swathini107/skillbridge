import enum
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    JSON,
    func
)
from sqlalchemy.orm import relationship
from app.database import Base


class ApplicationStatus(str, enum.Enum):
    """Status tracking for student job applications."""
    SAVED = "Saved"
    APPLIED = "Applied"
    ASSESSMENT = "Assessment"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


class WorkMode(str, enum.Enum):
    """Workplace arrangement."""
    ONSITE = "On-site"
    HYBRID = "Hybrid"
    REMOTE = "Remote"


class EmploymentType(str, enum.Enum):
    """Employment classification."""
    INTERNSHIP = "Internship"
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"


class RoundType(str, enum.Enum):
    """Interview round classification."""
    TECHNICAL = "Technical"
    HR = "HR"
    APTITUDE = "Aptitude"
    BEHAVIORAL = "Behavioral"
    SYSTEM_DESIGN = "System Design"


class DifficultyLevel(str, enum.Enum):
    """Interview question difficulty."""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class QuestionSource(str, enum.Enum):
    """Origin source of interview question."""
    PERSONAL_INTERVIEW = "Personal interview"
    RECRUITER = "Recruiter"
    ONLINE_ASSESSMENT = "Online assessment"
    PEER = "Peer"
    OTHER = "Other"


class ReviewStatus(str, enum.Enum):
    """Mastery and revision status for interview preparation."""
    NEW = "New"
    LEARNING = "Learning"
    CONFIDENT = "Confident"


class SessionStatus(str, enum.Enum):
    """Practice session progression status."""
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    ABANDONED = "Abandoned"


# Retain legacy aliases for backwards compatibility
QuestionCategory = RoundType
InterviewRound = RoundType
PracticeStatus = ReviewStatus


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    applications = relationship(
        "JobApplication",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    interview_questions = relationship(
        "InterviewQuestion",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    analyses = relationship(
        "JobAnalysis",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    practice_sessions = relationship(
        "PracticeSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Required core fields
    company_name = Column(String(150), nullable=False, index=True)
    job_title = Column(String(150), nullable=False, index=True)
    application_status = Column(
        String(50),
        default=ApplicationStatus.SAVED.value,
        index=True,
        nullable=False
    )

    # Additional metadata fields
    job_description = Column(Text, nullable=True)
    job_url = Column(String(500), nullable=True)
    company_url = Column(String(500), nullable=True)
    location = Column(String(150), nullable=True)
    work_mode = Column(String(50), nullable=True, index=True)
    employment_type = Column(String(50), nullable=True, index=True)
    skills = Column(Text, nullable=True)
    deadline = Column(Date, nullable=True, index=True)
    application_date = Column(Date, nullable=True)
    interview_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="applications")
    questions = relationship("InterviewQuestion", back_populates="job", foreign_keys="[InterviewQuestion.job_id]")

    def __repr__(self):
        return f"<JobApplication(id={self.id}, company='{self.company_name}', title='{self.job_title}', status='{self.application_status}')>"


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    job_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Core Question Details
    question_text = Column(Text, nullable=False)
    round_type = Column(
        String(50),
        default=RoundType.TECHNICAL.value,
        index=True,
        nullable=False
    )
    topic = Column(String(100), nullable=True, index=True)
    difficulty = Column(
        String(50),
        default=DifficultyLevel.INTERMEDIATE.value,
        index=True,
        nullable=False
    )

    # Context / Opportunity Metadata
    company_name = Column(String(150), nullable=True, index=True)
    job_role = Column(String(150), nullable=True)
    interview_date = Column(Date, nullable=True, index=True)
    source = Column(
        String(50),
        default=QuestionSource.PERSONAL_INTERVIEW.value,
        nullable=False
    )

    # Student Memory Bank & Reflection
    original_answer = Column(Text, nullable=True)
    expected_answer = Column(Text, nullable=True)
    improvement_notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # Comma-separated or JSON list of strings

    # Confidence / Preparation Status
    review_status = Column(
        String(50),
        default=ReviewStatus.NEW.value,
        index=True,
        nullable=False
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)

    # Legacy column compatibility
    job_title = Column(String(150), nullable=True)
    personal_answer = Column(Text, nullable=True)
    question_category = Column(String(50), default="TECHNICAL", nullable=True)
    interview_round = Column(String(50), default="FIRST_ROUND", nullable=True)
    practice_status = Column(String(50), default="NOT_PRACTICED", nullable=True)

    # Relationships
    user = relationship("User", back_populates="interview_questions")
    job = relationship("JobApplication", back_populates="questions", foreign_keys=[job_id])

    def __repr__(self):
        return f"<InterviewQuestion(id={self.id}, round='{self.round_type}', topic='{self.topic}', status='{self.review_status}')>"


class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    job_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    company_name = Column(String(150), nullable=True)
    job_title = Column(String(150), nullable=True)
    match_score = Column(Float, nullable=True)

    # Structured JSON analysis records
    required_skills = Column(JSON, nullable=True)
    preferred_skills = Column(JSON, nullable=True)
    unclassified_skills = Column(JSON, nullable=True)
    other_requirements = Column(JSON, nullable=True)
    matching_skills = Column(JSON, nullable=True)
    missing_skills = Column(JSON, nullable=True)
    score_breakdown = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="analyses")
    job = relationship("JobApplication", backref="analyses")

    def __repr__(self):
        return f"<JobAnalysis(id={self.id}, company='{self.company_name}', role='{self.job_title}', score={self.match_score})>"


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    job_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    session_name = Column(String(150), nullable=False)
    target_company = Column(String(150), nullable=True)
    target_role = Column(String(150), nullable=True)
    round_type = Column(
        String(50),
        default=RoundType.TECHNICAL.value,
        index=True,
        nullable=False
    )
    question_source = Column(
        String(100),
        default="Memory Bank",
        nullable=False
    )
    selected_topic = Column(String(100), nullable=True)
    difficulty = Column(
        String(50),
        default="Mixed",
        nullable=False
    )
    time_limit_minutes = Column(Integer, nullable=True)
    status = Column(
        String(50),
        default=SessionStatus.IN_PROGRESS.value,
        index=True,
        nullable=False
    )
    total_questions = Column(Integer, default=0)
    current_question_index = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="practice_sessions")
    job = relationship("JobApplication", backref="practice_sessions")
    answers = relationship(
        "PracticeAnswer",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="PracticeAnswer.order_index"
    )

    def __repr__(self):
        return f"<PracticeSession(id={self.id}, name='{self.session_name}', round='{self.round_type}', status='{self.status}')>"


class PracticeAnswer(Base):
    __tablename__ = "practice_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id = Column(
        Integer,
        ForeignKey("interview_questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    order_index = Column(Integer, nullable=False, default=0, index=True)

    # Snapshot of question details at time of practice
    question_text = Column(Text, nullable=False)
    round_type = Column(String(50), nullable=False)
    topic = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=False)
    expected_answer = Column(Text, nullable=True)

    # Student submission
    answer_text = Column(Text, nullable=True)
    is_attempted = Column(Boolean, default=False, nullable=False)
    is_skipped = Column(Boolean, default=False, nullable=False)

    # Structured Self-Assessment ratings (JSON dict mapping criteria -> 1-5 rating)
    self_ratings = Column(JSON, nullable=True)

    # Qualitative reflection notes
    went_well = Column(Text, nullable=True)
    was_difficult = Column(Text, nullable=True)
    need_to_learn = Column(Text, nullable=True)
    better_approach = Column(Text, nullable=True)

    time_spent_seconds = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    session = relationship("PracticeSession", back_populates="answers")
    question = relationship("InterviewQuestion")

    def __repr__(self):
        return f"<PracticeAnswer(id={self.id}, session_id={self.session_id}, order={self.order_index}, attempted={self.is_attempted})>"


# ============================================================================
# ATS-FRIENDLY RESUME BUILDER MODEL
# ============================================================================

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        default=1
    )
    title = Column(String(150), nullable=False, default="Software Engineer Resume")
    target_job_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    target_role = Column(String(100), nullable=True)
    template_id = Column(String(50), nullable=False, default="classic_ats")

    # Structured sections
    contact_info = Column(JSON, nullable=False, default=dict)
    summary = Column(Text, nullable=True)
    skills = Column(JSON, nullable=False, default=list)
    education = Column(JSON, nullable=False, default=list)
    projects = Column(JSON, nullable=False, default=list)
    experience = Column(JSON, nullable=False, default=list)
    additional_sections = Column(JSON, nullable=False, default=dict)
    section_config = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    user = relationship("User")
    target_job = relationship("JobApplication")

    def __repr__(self):
        return f"<Resume(id={self.id}, title='{self.title}', target_role='{self.target_role}')>"
