from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import desc, func, or_

from app.database import get_db
from app.models import (
    JobApplication,
    InterviewQuestion,
    JobAnalysis,
    PracticeSession,
    PracticeAnswer,
    SessionStatus,
    ReviewStatus,
    ApplicationStatus,
    Resume
)
from app.schemas import (
    DashboardSummaryResponse,
    DashboardSummaryCards,
    ApplicationFunnelData,
    FunnelStageItem,
    UpcomingDeadlineItem,
    SkillGapSummary,
    SkillGapItem,
    LearningTaskItem,
    InterviewPrepSummary,
    RecentSessionSummary,
    ActiveSessionResumeItem,
    TopicPracticeItem,
    RecommendationItem,
    ResumeOverviewSummary,
    RecentResumeSummary
)
from app.services.resume_service import analyze_resume_quality

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    user_id: int = Query(1, description="Student user ID"),
    db: Session = Depends(get_db)
):
    """
    Unified Career Preparation Dashboard Aggregated Data.
    Calculates live statistics, application funnel, upcoming deadlines, skill gaps,
    interview preparation metrics, and deterministic recommended next actions directly
    from actual database records.
    """
    today = date.today()

    # 1. Query Job Applications
    all_jobs: List[JobApplication] = db.query(JobApplication).filter(
        JobApplication.user_id == user_id
    ).all()

    total_jobs = len(all_jobs)
    status_counts = Counter(job.application_status for job in all_jobs)

    saved_jobs_count = status_counts.get("Saved", 0)
    applied_jobs_count = status_counts.get("Applied", 0)
    assessment_jobs_count = status_counts.get("Assessment", 0)
    interview_jobs_count = status_counts.get("Interview", 0)
    interviews_in_progress = assessment_jobs_count + interview_jobs_count
    offers_received = status_counts.get("Offer", 0)
    rejected_count = status_counts.get("Rejected", 0)
    withdrawn_count = status_counts.get("Withdrawn", 0)

    # Deadlines calculation
    upcoming_deadlines: List[UpcomingDeadlineItem] = []
    approaching_14_days_count = 0

    for job in all_jobs:
        if job.deadline:
            days_diff = (job.deadline - today).days
            is_overdue = days_diff < 0

            if is_overdue:
                urgency = "overdue"
            elif days_diff <= 3:
                urgency = "urgent"
            elif days_diff <= 7:
                urgency = "soon"
            else:
                urgency = "upcoming"

            if days_diff <= 14 or is_overdue:
                approaching_14_days_count += 1

            upcoming_deadlines.append(
                UpcomingDeadlineItem(
                    id=job.id,
                    company_name=job.company_name,
                    job_title=job.job_title,
                    deadline=job.deadline.isoformat(),
                    application_status=job.application_status or "Saved",
                    days_remaining=days_diff,
                    is_overdue=is_overdue,
                    urgency=urgency
                )
            )

    # Sort deadlines: overdue first, then nearest upcoming
    upcoming_deadlines.sort(key=lambda d: (not d.is_overdue, d.days_remaining))

    # Funnel visualization data
    funnel_pipeline = [
        FunnelStageItem(stage="Saved", label="Saved Opportunities", count=saved_jobs_count, color="#0284c7"),
        FunnelStageItem(stage="Applied", label="Applications Submitted", count=applied_jobs_count, color="#4338ca"),
        FunnelStageItem(stage="Assessment", label="Online Assessments", count=assessment_jobs_count, color="#7c3aed"),
        FunnelStageItem(stage="Interview", label="Active Interviews", count=interview_jobs_count, color="#b45309"),
        FunnelStageItem(stage="Offer", label="Offers Extended", count=offers_received, color="#047857"),
    ]

    funnel_outcomes = [
        FunnelStageItem(stage="Rejected", label="Unsuccessful / Rejected", count=rejected_count, color="#dc2626"),
        FunnelStageItem(stage="Withdrawn", label="Applications Withdrawn", count=withdrawn_count, color="#64748b"),
    ]

    # 2. Query Interview Memory Bank
    all_questions: List[InterviewQuestion] = db.query(InterviewQuestion).filter(
        InterviewQuestion.user_id == user_id
    ).all()

    total_questions = len(all_questions)
    q_status_counts = Counter(q.review_status for q in all_questions)

    confident_count = q_status_counts.get("Confident", 0)
    learning_count = q_status_counts.get("Learning", 0)
    new_count = q_status_counts.get("New", 0)
    unmastered_total = learning_count + new_count

    # Topics needing practice (questions with status != 'Confident')
    unmastered_by_topic = Counter(
        q.topic for q in all_questions if q.topic and q.review_status != "Confident"
    )
    topics_needing_practice = [
        TopicPracticeItem(topic=t, unmastered_count=c)
        for t, c in unmastered_by_topic.most_common(5)
    ]

    # 3. Query Mock Practice Sessions
    # Fast count aggregation by status
    status_counts_rows = db.query(
        PracticeSession.status,
        func.count(PracticeSession.id)
    ).filter(
        PracticeSession.user_id == user_id
    ).group_by(PracticeSession.status).all()

    session_counts_map = dict(status_counts_rows)
    completed_sessions_count = session_counts_map.get(SessionStatus.COMPLETED.value, 0)
    in_progress_sessions_count = session_counts_map.get(SessionStatus.IN_PROGRESS.value, 0)

    # Average self-assessment rating query (lightweight projection from attempted answers)
    rating_rows = db.query(PracticeAnswer.self_ratings).join(
        PracticeSession, PracticeAnswer.session_id == PracticeSession.id
    ).filter(
        PracticeSession.user_id == user_id,
        PracticeSession.status == SessionStatus.COMPLETED.value,
        PracticeAnswer.is_attempted == True
    ).all()

    all_ratings = []
    for (r_dict,) in rating_rows:
        if r_dict and isinstance(r_dict, dict):
            for val in r_dict.values():
                if isinstance(val, (int, float)) and 1 <= val <= 5:
                    all_ratings.append(float(val))

    overall_avg_rating = round(sum(all_ratings) / len(all_ratings), 1) if all_ratings else None

    # Load only the 5 most recent sessions with their answers for the summary widget
    recent_sessions = db.query(PracticeSession).options(
        selectinload(PracticeSession.answers)
    ).filter(
        PracticeSession.user_id == user_id
    ).order_by(desc(PracticeSession.created_at)).limit(5).all()

    # Recent practice sessions summary
    recent_sessions_summary: List[RecentSessionSummary] = []
    for s in recent_sessions:
        s_answers = s.answers or []
        s_ratings = []
        for a in s_answers:
            if a.self_ratings and isinstance(a.self_ratings, dict):
                for val in a.self_ratings.values():
                    if isinstance(val, (int, float)) and 1 <= val <= 5:
                        s_ratings.append(float(val))

        s_avg = round(sum(s_ratings) / len(s_ratings), 1) if s_ratings else None
        att_cnt = sum(1 for a in s_answers if a.is_attempted)

        date_str = None
        if s.completed_at:
            date_str = s.completed_at.strftime("%b %d, %Y")
        elif s.created_at:
            date_str = s.created_at.strftime("%b %d, %Y")

        recent_sessions_summary.append(
            RecentSessionSummary(
                id=s.id,
                session_name=s.session_name,
                round_type=s.round_type,
                status=s.status,
                score=s_avg,
                date=date_str,
                attempted_count=att_cnt,
                total_questions=s.total_questions or len(s_answers)
            )
        )

    # Active session to resume if one exists
    active_resume_item: Optional[ActiveSessionResumeItem] = None
    if in_progress_sessions_count > 0:
        latest_active = db.query(PracticeSession).options(
            selectinload(PracticeSession.answers)
        ).filter(
            PracticeSession.user_id == user_id,
            PracticeSession.status == SessionStatus.IN_PROGRESS.value
        ).order_by(desc(PracticeSession.created_at)).first()

        if latest_active:
            active_resume_item = ActiveSessionResumeItem(
                id=latest_active.id,
                session_name=latest_active.session_name,
                round_type=latest_active.round_type,
                current_index=latest_active.current_question_index or 0,
                total_questions=latest_active.total_questions or len(latest_active.answers or [])
            )

    # 4. Query Job Analyses & Skill Gaps
    total_analyses_count = db.query(func.count(JobAnalysis.id)).filter(
        JobAnalysis.user_id == user_id
    ).scalar() or 0

    all_analyses: List[JobAnalysis] = db.query(JobAnalysis).filter(
        JobAnalysis.user_id == user_id
    ).order_by(desc(JobAnalysis.created_at)).limit(20).all()

    missing_required_freq = Counter()
    missing_preferred_freq = Counter()
    skill_job_map = defaultdict(set)

    for analysis in all_analyses:
        company_label = analysis.company_name or "Opportunity"
        if analysis.job_title:
            company_label = f"{company_label} ({analysis.job_title})"

        # Required skills that were missing
        if analysis.missing_skills:
            if isinstance(analysis.missing_skills, list):
                for item in analysis.missing_skills:
                    skill_name = item if isinstance(item, str) else item.get("name") if isinstance(item, dict) else None
                    if skill_name:
                        missing_required_freq[skill_name] += 1
                        skill_job_map[skill_name].add(company_label)

        # Preferred skills that were missing
        if analysis.preferred_skills and isinstance(analysis.preferred_skills, list):
            for item in analysis.preferred_skills:
                skill_name = item.get("skill") if isinstance(item, dict) else item if isinstance(item, str) else None
                # Check if matching
                is_match = False
                if analysis.matching_skills and isinstance(analysis.matching_skills, list):
                    match_names = [m.get("skill", "") if isinstance(m, dict) else str(m) for m in analysis.matching_skills]
                    if skill_name in match_names:
                        is_match = True
                if skill_name and not is_match:
                    missing_preferred_freq[skill_name] += 1
                    skill_job_map[skill_name].add(company_label)

    frequently_missing_req = [
        SkillGapItem(skill=s, frequency=f, associated_jobs=list(skill_job_map[s]))
        for s, f in missing_required_freq.most_common(5)
    ]

    frequently_missing_pref = [
        SkillGapItem(skill=s, frequency=f, associated_jobs=list(skill_job_map[s]))
        for s, f in missing_preferred_freq.most_common(5)
    ]

    # Generate actionable learning tasks from missing skills
    learning_tasks: List[LearningTaskItem] = []
    for gap in frequently_missing_req[:3]:
        learning_tasks.append(
            LearningTaskItem(
                skill=gap.skill,
                type="Required",
                task=f"Build a mini-project or code sample demonstrating {gap.skill} to fulfill key requirements for {', '.join(gap.associated_jobs[:2])}.",
                job_company=gap.associated_jobs[0] if gap.associated_jobs else None
            )
        )

    for gap in frequently_missing_pref[:2]:
        learning_tasks.append(
            LearningTaskItem(
                skill=gap.skill,
                type="Preferred",
                task=f"Explore documentation and best practices for {gap.skill} to gain a competitive edge in interviews.",
                job_company=gap.associated_jobs[0] if gap.associated_jobs else None
            )
        )

    skill_gap_summary = SkillGapSummary(
        total_analyses=total_analyses_count,
        frequently_missing_required=frequently_missing_req,
        frequently_missing_preferred=frequently_missing_pref,
        suggested_learning_tasks=learning_tasks
    )

    interview_prep_summary = InterviewPrepSummary(
        total_questions=total_questions,
        confident_count=confident_count,
        learning_count=learning_count,
        new_count=new_count,
        recent_sessions=recent_sessions_summary,
        topics_needing_practice=topics_needing_practice,
        active_session_to_resume=active_resume_item
    )

    # 5. Query Resumes: single fast count + first() with joinedload
    total_resumes_saved = db.query(func.count(Resume.id)).filter(
        Resume.user_id == user_id
    ).scalar() or 0

    latest_resume = db.query(Resume).options(
        joinedload(Resume.target_job)
    ).filter(
        Resume.user_id == user_id
    ).order_by(desc(Resume.updated_at)).first()

    recent_resume_summary: Optional[RecentResumeSummary] = None
    if latest_resume:
        review_res = analyze_resume_quality(latest_resume)
        crit_issues = review_res.get("critical_issues", [])
        rec_improvements = review_res.get("recommended_improvements", [])
        has_warnings = len(crit_issues) > 0 or len(rec_improvements) > 0

        target_company = None
        if latest_resume.target_job:
            target_company = latest_resume.target_job.company_name

        recent_resume_summary = RecentResumeSummary(
            id=latest_resume.id,
            title=latest_resume.title,
            target_role=latest_resume.target_role,
            target_job_id=latest_resume.target_job_id,
            target_company=target_company,
            completeness_score=review_res.get("overall_score", 0),
            has_unresolved_warnings=has_warnings,
            critical_issues_count=len(crit_issues),
            updated_at=latest_resume.updated_at
        )

    resume_overview = ResumeOverviewSummary(
        total_resumes=total_resumes_saved,
        most_recent_resume=recent_resume_summary
    )

    # 6. Deterministic Recommended Next Steps
    recommended_steps: List[RecommendationItem] = []

    # Rule 1: Urgent / Overdue Application Deadlines
    for d in upcoming_deadlines[:2]:
        if d.is_overdue:
            recommended_steps.append(
                RecommendationItem(
                    id=f"deadline-{d.id}",
                    category="deadline",
                    priority="high",
                    title=f"Application Overdue: {d.company_name}",
                    description=f"The submission deadline for {d.job_title} was {abs(d.days_remaining)} day(s) ago. Update status or withdraw.",
                    action_text="Review Application",
                    action_link=f"/applications?search={d.company_name}"
                )
            )
        elif d.days_remaining <= 3:
            recommended_steps.append(
                RecommendationItem(
                    id=f"deadline-{d.id}",
                    category="deadline",
                    priority="high",
                    title=f"Approaching Deadline: {d.company_name}",
                    description=f"Deadline for {d.job_title} is in {d.days_remaining} day(s). Finalize and submit your application materials.",
                    action_text="View Opportunity",
                    action_link=f"/applications?search={d.company_name}"
                )
            )

    # Rule 2: Resume Quality Review Warning
    if recent_resume_summary and recent_resume_summary.critical_issues_count > 0:
        recommended_steps.append(
            RecommendationItem(
                id=f"resume-critical-{recent_resume_summary.id}",
                category="resume",
                priority="high",
                title=f"Resolve {recent_resume_summary.critical_issues_count} Critical Issue(s) in Resume",
                description=f"'{recent_resume_summary.title}' has formatting or contact gaps that could cause parsing failures in employer ATS systems.",
                action_text="Review & Fix Resume",
                action_link=f"/resume-builder?id={recent_resume_summary.id}&tab=review"
            )
        )
    elif total_resumes_saved == 0:
        recommended_steps.append(
            RecommendationItem(
                id="create-first-resume",
                category="resume",
                priority="medium",
                title="Create an ATS-Friendly Resume",
                description="Build a clean, single-column resume tailored for campus placements and applicant tracking systems.",
                action_text="Create Resume",
                action_link="/resume-builder"
            )
        )

    # Rule 3: Active Interview Stages
    interview_jobs = [j for j in all_jobs if j.application_status in ("Interview", "Assessment")]
    for j in interview_jobs[:2]:
        recommended_steps.append(
            RecommendationItem(
                id=f"interview-prep-{j.id}",
                category="mock_interview",
                priority="high",
                title=f"Prepare for {j.company_name} ({j.application_status} Round)",
                description=f"You are actively interviewing for {j.job_title}. Run a targeted practice session with company-specific questions.",
                action_text="Start Practice Session",
                action_link=f"/practice?job_id={j.id}"
            )
        )

    # Rule 4: Unfinished In-Progress Practice Session
    if active_resume_item:
        recommended_steps.append(
            RecommendationItem(
                id=f"resume-session-{active_resume_item.id}",
                category="mock_interview",
                priority="high",
                title=f"Resume Active Practice: {active_resume_item.session_name}",
                description=f"You have an ongoing {active_resume_item.round_type} session paused on question {active_resume_item.current_index + 1} of {active_resume_item.total_questions}.",
                action_text="Resume Interview",
                action_link="/practice"
            )
        )

    # Rule 5: Saved Jobs without an Analysis
    analyzed_job_ids = {a.job_id for a in all_analyses if a.job_id}
    unanalyzed_jobs = [j for j in all_jobs if j.id not in analyzed_job_ids and j.job_description and len(j.job_description.strip()) > 30]
    for j in unanalyzed_jobs[:2]:
        recommended_steps.append(
            RecommendationItem(
                id=f"analyze-job-{j.id}",
                category="analysis",
                priority="medium",
                title=f"Analyze Job Description: {j.company_name}",
                description=f"Discover required technical skills and calculate match percentage for {j.job_title}.",
                action_text="Analyze Job",
                action_link=f"/job-analyzer?job_id={j.id}"
            )
        )

    # Rule 6: Top Missing Skill Gap
    if frequently_missing_req:
        top_skill = frequently_missing_req[0]
        recommended_steps.append(
            RecommendationItem(
                id=f"skill-gap-{top_skill.skill}",
                category="skill_gap",
                priority="medium",
                title=f"Skill Gap Detected: {top_skill.skill}",
                description=f"'{top_skill.skill}' was missing in {top_skill.frequency} analysis report(s). Practice technical questions in this domain.",
                action_text="Browse Questions",
                action_link=f"/questions?search={top_skill.skill}"
            )
        )

    # Rule 7: Questions marked 'Learning' or 'New'
    if learning_count > 0:
        recommended_steps.append(
            RecommendationItem(
                id="unmastered-questions",
                category="question_review",
                priority="low",
                title=f"Revisit {learning_count} Questions in 'Learning' Status",
                description="Refine your answers using the STAR method and review expected technical talking points.",
                action_text="Review Questions",
                action_link="/questions?review_status=Learning"
            )
        )

    # Fallback if no records exist
    if not recommended_steps:
        recommended_steps.append(
            RecommendationItem(
                id="first-step-save-job",
                category="general",
                priority="high",
                title="Save Your First Job Opportunity",
                description="Start your placement prep by adding a job opportunity to track deadlines and analyze requirements.",
                action_text="Add Job Opportunity",
                action_link="/applications"
            )
        )
        recommended_steps.append(
            RecommendationItem(
                id="first-step-add-question",
                category="general",
                priority="medium",
                title="Add Questions to Interview Memory Bank",
                description="Save real questions encountered in campus screenings, online assessments, and mock rounds.",
                action_text="Add Question",
                action_link="/questions"
            )
        )

    summary_cards = DashboardSummaryCards(
        total_saved_jobs=saved_jobs_count,
        applications_submitted=applied_jobs_count,
        interviews_in_progress=interviews_in_progress,
        offers_received=offers_received,
        rejected_count=rejected_count,
        withdrawn_count=withdrawn_count,
        total_jobs=total_jobs,
        upcoming_deadlines_count=approaching_14_days_count,
        total_questions_saved=total_questions,
        questions_confident=confident_count,
        questions_learning=unmastered_total,
        sessions_completed=completed_sessions_count,
        sessions_in_progress=in_progress_sessions_count,
        average_self_assessment=overall_avg_rating,
        total_resumes_saved=total_resumes_saved
    )

    funnel_data = ApplicationFunnelData(
        pipeline=funnel_pipeline,
        outcomes=funnel_outcomes
    )

    return DashboardSummaryResponse(
        summary_cards=summary_cards,
        application_funnel=funnel_data,
        upcoming_deadlines=upcoming_deadlines,
        skill_gap_summary=skill_gap_summary,
        interview_prep_summary=interview_prep_summary,
        resume_overview=resume_overview,
        recommended_next_steps=recommended_steps[:6]
    )
