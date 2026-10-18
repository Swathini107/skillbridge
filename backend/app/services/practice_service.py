"""
SkillBridge — Day 5: Mock Interview Practice Studio Service
Handles question selection, personalization matching based on saved jobs and Day 3 analyses,
session lifecycle, and transparent performance report generation.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.models import (
    User,
    JobApplication,
    InterviewQuestion,
    JobAnalysis,
    PracticeSession,
    PracticeAnswer,
    SessionStatus,
    RoundType
)
from app.schemas import (
    PracticeSessionCreate,
    PracticePreviewResponse,
    PracticePreviewQuestion,
    CustomQuestionInput,
    PracticeSessionReport,
    PracticeAnswerRead,
    CRITERIA_LABELS,
    UNIVERSAL_CRITERIA,
    TECHNICAL_CRITERIA,
    HR_CRITERIA
)


def format_duration(seconds: int) -> str:
    """Format seconds into a friendly human-readable duration (e.g. '12m 45s')."""
    if seconds <= 0:
        return "0s"
    minutes = seconds // 60
    rem_secs = seconds % 60
    if minutes > 0 and rem_secs > 0:
        return f"{minutes}m {rem_secs}s"
    elif minutes > 0:
        return f"{minutes}m"
    return f"{rem_secs}s"


def get_applicable_criteria(round_type: str) -> List[str]:
    """Return applicable self-assessment criteria keys for a given interview round."""
    criteria = list(UNIVERSAL_CRITERIA)
    normalized = round_type.lower() if round_type else ""
    if normalized in ["technical", "aptitude", "system design", "system_design"]:
        criteria.extend(TECHNICAL_CRITERIA)
    elif normalized in ["hr", "behavioral"]:
        criteria.extend(HR_CRITERIA)
    else:
        # For mixed or custom rounds, provide standard technical criteria
        criteria.extend(TECHNICAL_CRITERIA)
    return criteria


def get_star_prompts() -> Dict[str, str]:
    """Return structured preparation guidance prompts for HR/Behavioral questions."""
    return {
        "S": "Situation: Set the scene and give the necessary details of your example.",
        "T": "Task: Describe what your responsibility was in that situation.",
        "A": "Action: Explain exactly what steps you took to address the challenge.",
        "R": "Result: Share what outcomes were achieved, quantified where possible."
    }


def select_practice_questions(
    db: Session,
    user_id: int,
    round_type: str = "Technical",
    job_id: Optional[int] = None,
    target_company: Optional[str] = None,
    target_role: Optional[str] = None,
    question_source: Optional[str] = "Memory Bank",
    selected_topic: Optional[str] = None,
    difficulty: str = "Mixed",
    requested_count: int = 5,
    custom_question: Optional[CustomQuestionInput] = None
) -> Tuple[List[Dict[str, Any]], int, Optional[str], List[str], Optional[str], Optional[str]]:
    """
    Select and rank questions for a practice session using SkillBridge data.
    Incorporates:
    - Saved job details (company, role, description, skills)
    - Day 3 analysis gaps (missing required and preferred skills)
    - Difficulty and round constraints
    - Custom manual question if provided
    Never duplicates questions merely to satisfy requested count.
    """
    selected_questions: List[Dict[str, Any]] = []
    targeted_skills: List[str] = []
    matched_company = target_company
    matched_role = target_role

    # 1. Inspect saved job and associated JobAnalysis if job_id is provided
    job_record: Optional[JobApplication] = None
    if job_id:
        job_record = db.query(JobApplication).filter(
            JobApplication.id == job_id,
            JobApplication.user_id == user_id
        ).first()

        if job_record:
            if not matched_company:
                matched_company = job_record.company_name
            if not matched_role:
                matched_role = job_record.job_title

            # Check for latest JobAnalysis for this job
            latest_analysis = db.query(JobAnalysis).filter(
                JobAnalysis.job_id == job_id,
                JobAnalysis.user_id == user_id
            ).order_by(desc(JobAnalysis.created_at)).first()

            if latest_analysis and latest_analysis.missing_skills:
                # missing_skills may be stored as a list of strings or dicts
                if isinstance(latest_analysis.missing_skills, list):
                    for item in latest_analysis.missing_skills:
                        if isinstance(item, str):
                            targeted_skills.append(item)
                        elif isinstance(item, dict) and "name" in item:
                            targeted_skills.append(item["name"])

    # If target_company/role still not set, but target_company was provided manually
    company_filter = (matched_company or "").strip().lower()
    role_filter = (matched_role or "").strip().lower()

    # 2. Query question candidates from InterviewQuestion
    query = db.query(InterviewQuestion).filter(InterviewQuestion.user_id == user_id)

    # Filter by round type if specified and not empty
    if round_type and round_type != "All":
        query = query.filter(InterviewQuestion.round_type == round_type)

    # Filter by difficulty if specific difficulty requested
    if difficulty and difficulty != "Mixed":
        query = query.filter(InterviewQuestion.difficulty == difficulty)

    # Filter by topic if question source is Topic
    if question_source == "Topic" and selected_topic:
        query = query.filter(
            or_(
                InterviewQuestion.topic.ilike(f"%{selected_topic}%"),
                InterviewQuestion.tags.ilike(f"%{selected_topic}%")
            )
        )

    all_candidates: List[InterviewQuestion] = query.all()

    # If no questions found with strict round filter, fall back gracefully to all questions in repo
    if not all_candidates:
        all_candidates = db.query(InterviewQuestion).filter(
            InterviewQuestion.user_id == user_id
        ).all()

    total_available = len(all_candidates)

    # 3. Score and prioritize candidates based on SkillBridge personalization data
    scored_candidates: List[Tuple[float, InterviewQuestion, str]] = []

    for q in all_candidates:
        score = 10.0
        reason = f"Memory Bank match ({q.round_type} - {q.topic or 'General'})"

        # Explicit link to this saved job
        if job_id and q.job_id == job_id:
            score += 60.0
            reason = f"Directly linked to saved job: {job_record.company_name if job_record else 'Target Opportunity'}"

        # Company name match
        elif company_filter and q.company_name and (company_filter in q.company_name.lower() or q.company_name.lower() in company_filter):
            score += 35.0
            reason = f"Targeted for company: {q.company_name}"

        # Role name match
        if role_filter and q.job_role and (role_filter in q.job_role.lower() or q.job_role.lower() in role_filter):
            score += 25.0
            if "Targeted" not in reason and "Directly" not in reason:
                reason = f"Targeted for role: {q.job_role}"

        # Targeted missing skill gap from Job Description Analyzer
        if targeted_skills:
            q_text = (q.question_text or "").lower()
            q_topic = (q.topic or "").lower()
            q_tags = (q.tags or "").lower()
            for skill in targeted_skills:
                s_lower = skill.lower()
                if s_lower in q_topic or s_lower in q_tags or s_lower in q_text:
                    score += 40.0
                    reason = f"Targets identified skill gap: {skill}"
                    break

        # Difficulty alignment
        if difficulty and difficulty != "Mixed" and q.difficulty == difficulty:
            score += 15.0

        # Review status: Prioritize 'New' and 'Learning' questions over 'Confident' questions
        if q.review_status == "Learning":
            score += 10.0
        elif q.review_status == "New":
            score += 5.0

        scored_candidates.append((score, q, reason))

    # Sort descending by score
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    # Add custom manual question first if supplied
    used_q_ids = set()
    if custom_question and custom_question.question_text.strip():
        selected_questions.append({
            "id": None,
            "question_text": custom_question.question_text.strip(),
            "round_type": custom_question.round_type or round_type,
            "topic": custom_question.topic or "Custom",
            "difficulty": custom_question.difficulty or (difficulty if difficulty != "Mixed" else "Intermediate"),
            "company_name": matched_company,
            "job_role": matched_role,
            "expected_answer": custom_question.expected_answer,
            "relevance_reason": "Custom manual question added for this session"
        })

    # Pick top distinct questions up to requested_count
    for _, q, reason in scored_candidates:
        if len(selected_questions) >= requested_count:
            break
        if q.id not in used_q_ids:
            used_q_ids.add(q.id)
            selected_questions.append({
                "id": q.id,
                "question_text": q.question_text,
                "round_type": q.round_type,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "company_name": q.company_name,
                "job_role": q.job_role,
                "expected_answer": q.expected_answer,
                "relevance_reason": reason
            })

    # Build warning if fewer suitable questions are available
    warning = None
    if len(selected_questions) < requested_count:
        if len(selected_questions) == 0:
            warning = (
                f"No suitable questions found in the Interview Memory Bank matching '{round_type}'."
                " Add questions in the Memory Bank or create a custom question to practice."
            )
        else:
            warning = (
                f"Only {len(selected_questions)} suitable question(s) available in the repository. "
                "Starting a focused session with all available matching questions without duplicate padding."
            )

    return (
        selected_questions,
        total_available,
        warning,
        targeted_skills[:5],
        matched_company,
        matched_role
    )


def preview_practice_session(
    db: Session,
    user_id: int,
    request_data: Any
) -> PracticePreviewResponse:
    """Generate a preview of the practice session before the student starts."""
    (
        questions,
        total_avail,
        warning,
        skills,
        company,
        role
    ) = select_practice_questions(
        db=db,
        user_id=user_id,
        round_type=request_data.round_type or "Technical",
        job_id=request_data.job_id,
        target_company=request_data.target_company,
        target_role=request_data.target_role,
        question_source=request_data.question_source or "Memory Bank",
        selected_topic=request_data.selected_topic,
        difficulty=request_data.difficulty or "Mixed",
        requested_count=request_data.question_count or 5,
        custom_question=request_data.custom_question
    )

    preview_items = [
        PracticePreviewQuestion(
            id=q["id"],
            question_text=q["question_text"],
            round_type=q["round_type"],
            topic=q.get("topic"),
            difficulty=q["difficulty"],
            company_name=q.get("company_name"),
            job_role=q.get("job_role"),
            expected_answer=q.get("expected_answer"),
            relevance_reason=q.get("relevance_reason")
        )
        for q in questions
    ]

    return PracticePreviewResponse(
        total_available=total_avail,
        requested_count=request_data.question_count or 5,
        selected_count=len(preview_items),
        warning=warning,
        target_company=company,
        target_role=role,
        personalized_skills_targeted=skills,
        questions=preview_items
    )


def create_practice_session(
    db: Session,
    user_id: int,
    session_in: PracticeSessionCreate
) -> PracticeSession:
    """Initialize and persist a new practice session with populated questions."""
    (
        questions,
        _,
        _,
        _,
        company,
        role
    ) = select_practice_questions(
        db=db,
        user_id=user_id,
        round_type=session_in.round_type or "Technical",
        job_id=session_in.job_id,
        target_company=session_in.target_company,
        target_role=session_in.target_role,
        question_source=session_in.question_source or "Memory Bank",
        selected_topic=session_in.selected_topic,
        difficulty=session_in.difficulty or "Mixed",
        requested_count=session_in.question_count or 5,
        custom_question=session_in.custom_question
    )

    if not questions:
        raise ValueError(
            "Cannot create practice session: No matching questions found in Interview Memory Bank. "
            "Please add questions first or include a custom question."
        )

    # Create session record
    session_record = PracticeSession(
        user_id=user_id,
        job_id=session_in.job_id,
        session_name=session_in.session_name,
        target_company=company or session_in.target_company,
        target_role=role or session_in.target_role,
        round_type=session_in.round_type or "Technical",
        question_source=session_in.question_source or "Memory Bank",
        selected_topic=session_in.selected_topic,
        difficulty=session_in.difficulty or "Mixed",
        time_limit_minutes=session_in.time_limit_minutes,
        status=SessionStatus.IN_PROGRESS.value,
        total_questions=len(questions),
        current_question_index=0,
        duration_seconds=0
    )
    db.add(session_record)
    db.flush()  # Populates session_record.id

    # Create ordered answer slots for each question
    for idx, q_data in enumerate(questions):
        answer_record = PracticeAnswer(
            session_id=session_record.id,
            question_id=q_data["id"],
            order_index=idx,
            question_text=q_data["question_text"],
            round_type=q_data["round_type"],
            topic=q_data.get("topic"),
            difficulty=q_data["difficulty"],
            expected_answer=q_data.get("expected_answer"),
            answer_text="",
            is_attempted=False,
            is_skipped=False,
            self_ratings=None,
            went_well=None,
            was_difficult=None,
            need_to_learn=None,
            better_approach=None,
            time_spent_seconds=0
        )
        db.add(answer_record)

    db.commit()
    db.refresh(session_record)
    return session_record


def generate_session_report(session: PracticeSession) -> PracticeSessionReport:
    """
    Generate a transparent, data-driven performance summary report for a completed session.
    Calculates statistics directly from saved user ratings and responses without hallucinating scores.
    """
    answers = session.answers or []
    total_q = session.total_questions or len(answers)
    attempted = sum(1 for a in answers if a.is_attempted)
    skipped = sum(1 for a in answers if a.is_skipped)
    unanswered = max(0, total_q - attempted - skipped)

    completion_rate = round((attempted / total_q) * 100.0, 1) if total_q > 0 else 0.0

    # Aggregate self-assessment ratings
    criteria_totals: Dict[str, float] = {}
    criteria_counts: Dict[str, int] = {}
    all_scores: List[int] = []

    for a in answers:
        if a.self_ratings and isinstance(a.self_ratings, dict):
            for criterion, score in a.self_ratings.items():
                if isinstance(score, (int, float)) and 1 <= score <= 5:
                    criteria_totals[criterion] = criteria_totals.get(criterion, 0.0) + float(score)
                    criteria_counts[criterion] = criteria_counts.get(criterion, 0) + 1
                    all_scores.append(int(score))

    scores_available = len(all_scores) > 0
    overall_avg: Optional[float] = None
    criteria_averages: Dict[str, float] = {}
    strongest_areas: List[str] = []
    areas_for_improvement: List[str] = []

    if scores_available:
        overall_avg = round(sum(all_scores) / len(all_scores), 1)
        for crit, total_score in criteria_totals.items():
            count = criteria_counts[crit]
            avg = round(total_score / count, 1)
            criteria_averages[crit] = avg

        # Sort criteria by score
        sorted_crit = sorted(criteria_averages.items(), key=lambda x: x[1], reverse=True)
        for crit, score in sorted_crit:
            label = CRITERIA_LABELS.get(crit, crit.replace("_", " ").title())
            if score >= 3.8:
                strongest_areas.append(f"{label} ({score}/5.0)")
            elif score <= 3.2:
                areas_for_improvement.append(f"{label} ({score}/5.0)")

        # Fallbacks if all scores are similar
        if not strongest_areas and sorted_crit:
            top_crit, top_score = sorted_crit[0]
            top_label = CRITERIA_LABELS.get(top_crit, top_crit.replace("_", " ").title())
            strongest_areas.append(f"{top_label} ({top_score}/5.0)")

        if not areas_for_improvement and sorted_crit and len(sorted_crit) > 1:
            low_crit, low_score = sorted_crit[-1]
            if low_score < 4.5:
                low_label = CRITERIA_LABELS.get(low_crit, low_crit.replace("_", " ").title())
                areas_for_improvement.append(f"{low_label} ({low_score}/5.0)")

    # Practical recommendations based on empirical performance
    recommendations: List[str] = []
    if skipped > 0:
        recommendations.append(
            f"You skipped {skipped} question(s). Revisit these topics in the Interview Memory Bank to draft structured talking points."
        )

    if scores_available:
        if "answer_structure" in criteria_averages and criteria_averages["answer_structure"] < 3.8:
            recommendations.append(
                "Strengthen your answer structure: Practice structuring behavioral stories using the STAR method (Situation, Task, Action, Result) with quantified business impact."
            )
        if "technical_correctness" in criteria_averages and criteria_averages["technical_correctness"] < 3.8:
            recommendations.append(
                "Focus on edge-case analysis and time/space complexity before diving into coding solutions."
            )
        if "clarity" in criteria_averages and criteria_averages["clarity"] < 3.8:
            recommendations.append(
                "Practice the 'Bottom Line Up Front' technique: State your thesis or key conclusion in the first 15 seconds."
            )
        if "problem_solving" in criteria_averages and criteria_averages["problem_solving"] < 3.8:
            recommendations.append(
                "Clarify assumptions and outline high-level trade-offs before jumping to technical implementations."
            )

    if not recommendations:
        if attempted == total_q:
            recommendations.append(
                "Excellent session! All questions attempted. To prepare for on-site rounds, try decreasing your practice time limit."
            )
        else:
            recommendations.append(
                "Continue consistent practice sessions and record honest reflections after each answer to track confidence gains."
            )

    # Format duration
    duration_str = format_duration(session.duration_seconds or 0)

    # Convert answers to Pydantic models
    answer_reads = [PracticeAnswerRead.model_validate(a) for a in answers]

    return PracticeSessionReport(
        session_id=session.id,
        session_name=session.session_name,
        target_company=session.target_company,
        target_role=session.target_role,
        round_type=session.round_type,
        difficulty=session.difficulty,
        status=session.status,
        duration_seconds=session.duration_seconds or 0,
        duration_formatted=duration_str,
        time_limit_minutes=session.time_limit_minutes,
        started_at=session.started_at,
        completed_at=session.completed_at,
        total_questions=total_q,
        questions_attempted=attempted,
        questions_skipped=skipped,
        questions_unanswered=unanswered,
        completion_rate_percentage=completion_rate,
        scores_available=scores_available,
        overall_average_score=overall_avg,
        criteria_averages=criteria_averages,
        strongest_areas=strongest_areas,
        areas_for_improvement=areas_for_improvement,
        recommendations=recommendations,
        answers=answer_reads
    )
