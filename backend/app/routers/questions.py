from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func, case

from app.database import get_db
from app.models import InterviewQuestion, JobApplication, User
from app.schemas import (
    InterviewQuestionCreate,
    InterviewQuestionUpdate,
    InterviewQuestionStatusUpdate,
    InterviewQuestionRead,
    QuestionStatsResponse
)

router = APIRouter(prefix="/questions", tags=["Interview Questions"])


@router.get("", response_model=List[InterviewQuestionRead])
def list_questions(
    search: Optional[str] = Query(None, description="Search question text, topic, company, role, or tags"),
    round_type: Optional[str] = Query(None, description="Filter by round type (Technical, HR, Aptitude, Behavioral, System Design)"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (Beginner, Intermediate, Advanced)"),
    review_status: Optional[str] = Query(None, description="Filter by review status (New, Learning, Confident)"),
    company_name: Optional[str] = Query(None, description="Filter by company name"),
    job_role: Optional[str] = Query(None, description="Filter by job role"),
    topic: Optional[str] = Query(None, description="Filter by specific topic"),
    job_id: Optional[int] = Query(None, description="Filter by linked job application ID"),
    sort_by: str = Query("recent", description="Sort by: recent, interview_date, difficulty, company"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Optional maximum number of records to return"),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    List interview memory bank questions with comprehensive filtering, search, and sorting.
    """
    query = db.query(InterviewQuestion).filter(InterviewQuestion.user_id == 1)

    # Search filter (case-insensitive across key text attributes)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                InterviewQuestion.question_text.ilike(term),
                InterviewQuestion.topic.ilike(term),
                InterviewQuestion.company_name.ilike(term),
                InterviewQuestion.job_role.ilike(term),
                InterviewQuestion.tags.ilike(term),
                InterviewQuestion.original_answer.ilike(term),
                InterviewQuestion.expected_answer.ilike(term),
                InterviewQuestion.improvement_notes.ilike(term)
            )
        )

    # Exact / normalized category filters
    if round_type and round_type.strip():
        query = query.filter(InterviewQuestion.round_type.ilike(round_type.strip()))

    if difficulty and difficulty.strip():
        query = query.filter(InterviewQuestion.difficulty.ilike(difficulty.strip()))

    if review_status and review_status.strip():
        query = query.filter(InterviewQuestion.review_status.ilike(review_status.strip()))

    if company_name and company_name.strip():
        query = query.filter(InterviewQuestion.company_name.ilike(company_name.strip()))

    if job_role and job_role.strip():
        query = query.filter(InterviewQuestion.job_role.ilike(f"%{job_role.strip()}%"))

    if topic and topic.strip():
        query = query.filter(InterviewQuestion.topic.ilike(f"%{topic.strip()}%"))

    if job_id is not None:
        query = query.filter(InterviewQuestion.job_id == job_id)

    # Sorting
    is_desc = order.lower() == "desc"

    if sort_by == "interview_date":
        sort_col = InterviewQuestion.interview_date
        query = query.order_by(desc(sort_col).nullslast() if is_desc else asc(sort_col).nullsfirst())
    elif sort_by == "company":
        sort_col = InterviewQuestion.company_name
        query = query.order_by(desc(sort_col) if is_desc else asc(sort_col))
    elif sort_by == "difficulty":
        # Order custom priority: Beginner (1) < Intermediate (2) < Advanced (3)
        diff_order = case(
            (InterviewQuestion.difficulty == "Beginner", 1),
            (InterviewQuestion.difficulty == "Intermediate", 2),
            (InterviewQuestion.difficulty == "Advanced", 3),
            else_=0
        )
        query = query.order_by(desc(diff_order) if is_desc else asc(diff_order))
    else:  # Default: recent (created_at)
        query = query.order_by(desc(InterviewQuestion.created_at) if is_desc else asc(InterviewQuestion.created_at))

    if limit is not None:
        query = query.limit(limit).offset(offset)

    return query.all()


@router.get("/stats", response_model=QuestionStatsResponse)
def get_question_stats(db: Session = Depends(get_db)):
    """
    Retrieve live preparation statistics from actual database records via lightweight column projection.
    """
    user_id = 1
    rows = db.query(
        InterviewQuestion.round_type,
        InterviewQuestion.review_status,
        InterviewQuestion.difficulty
    ).filter(InterviewQuestion.user_id == user_id).all()

    total = len(rows)
    technical = 0
    hr_behavioral = 0
    confident = 0
    needs_review = 0

    by_round: dict = {}
    by_status: dict = {}
    by_difficulty: dict = {}

    for round_type, review_status, difficulty in rows:
        r = round_type or "Unclassified"
        by_round[r] = by_round.get(r, 0) + 1
        if r.lower() == "technical":
            technical += 1
        elif r.lower() in ("hr", "behavioral"):
            hr_behavioral += 1

        s = review_status or "New"
        by_status[s] = by_status.get(s, 0) + 1
        if s.lower() == "confident":
            confident += 1
        elif s.lower() in ("new", "learning"):
            needs_review += 1

        d = difficulty or "Intermediate"
        by_difficulty[d] = by_difficulty.get(d, 0) + 1

    return QuestionStatsResponse(
        total=total,
        technical=technical,
        hr_behavioral=hr_behavioral,
        confident=confident,
        needs_review=needs_review,
        by_round=by_round,
        by_status=by_status,
        by_difficulty=by_difficulty
    )


@router.get("/{question_id}", response_model=InterviewQuestionRead)
def get_question(question_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full details of a specific interview question by ID.
    """
    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == question_id,
        InterviewQuestion.user_id == 1
    ).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview question with ID {question_id} not found."
        )

    return question


@router.post("", response_model=InterviewQuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(
    item: InterviewQuestionCreate,
    db: Session = Depends(get_db)
):
    """
    Save a new interview question encountered during recruitment.
    """
    # Ensure default user exists
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, name="Student Demo", email="student@skillbridge.edu")
        db.add(user)
        db.commit()

    company_name = item.company_name
    job_role = item.job_role

    # If linked to a saved job, verify it exists and backfill company/role if omitted
    if item.job_id:
        job = db.query(JobApplication).filter(JobApplication.id == item.job_id).first()
        if job:
            if not company_name:
                company_name = job.company_name
            if not job_role:
                job_role = job.job_title

    new_q = InterviewQuestion(
        user_id=1,
        job_id=item.job_id,
        question_text=item.question_text,
        round_type=item.round_type or "Technical",
        topic=item.topic,
        difficulty=item.difficulty or "Intermediate",
        company_name=company_name,
        job_role=job_role,
        job_title=job_role,  # Legacy field sync
        interview_date=item.interview_date,
        source=item.source or "Personal interview",
        original_answer=item.original_answer,
        personal_answer=item.original_answer,  # Legacy field sync
        expected_answer=item.expected_answer,
        improvement_notes=item.improvement_notes,
        tags=item.tags,
        review_status=item.review_status or "New",
        question_category=(item.round_type or "Technical").upper(),
        interview_round="FIRST_ROUND",
        practice_status="NOT_PRACTICED"
    )

    db.add(new_q)
    db.commit()
    db.refresh(new_q)
    return new_q


@router.put("/{question_id}", response_model=InterviewQuestionRead)
def update_question(
    question_id: int,
    item: InterviewQuestionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing interview question's details, notes, or reflection.
    """
    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == question_id,
        InterviewQuestion.user_id == 1
    ).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview question with ID {question_id} not found."
        )

    update_data = item.model_dump(exclude_unset=True)

    # If linking or changing linked job
    if "job_id" in update_data and update_data["job_id"] is not None:
        job = db.query(JobApplication).filter(JobApplication.id == update_data["job_id"]).first()
        if job:
            if not update_data.get("company_name") and not question.company_name:
                update_data["company_name"] = job.company_name
            if not update_data.get("job_role") and not question.job_role:
                update_data["job_role"] = job.job_title

    for key, value in update_data.items():
        setattr(question, key, value)

    # Sync legacy fields if affected
    if "job_role" in update_data:
        question.job_title = update_data["job_role"]
    if "original_answer" in update_data:
        question.personal_answer = update_data["original_answer"]

    question.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(question)
    return question


@router.patch("/{question_id}/status")
def update_question_status(
    question_id: int,
    status_payload: InterviewQuestionStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Quickly update review status (New, Learning, Confident) without editing other fields.
    """
    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == question_id,
        InterviewQuestion.user_id == 1
    ).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview question with ID {question_id} not found."
        )

    question.review_status = status_payload.review_status
    question.updated_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "id": question_id,
        "review_status": question.review_status,
        "message": f"Review status updated to {question.review_status}."
    }


@router.delete("/{question_id}", status_code=status.HTTP_200_OK)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Permanently delete an interview question.
    """
    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.id == question_id,
        InterviewQuestion.user_id == 1
    ).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview question with ID {question_id} not found."
        )

    db.delete(question)
    db.commit()
    return {
        "success": True,
        "message": f"Interview question #{question_id} was successfully deleted."
    }
