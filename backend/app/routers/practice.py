from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.database import get_db
from app.models import PracticeSession, PracticeAnswer, SessionStatus, InterviewQuestion, JobApplication
from app.schemas import (
    PracticeSessionCreate,
    PracticeSessionRead,
    PracticeSessionListItem,
    PracticeSessionReport,
    PracticePreviewRequest,
    PracticePreviewResponse,
    PracticeAnswerUpdate,
    PracticeAnswerRead
)
from app.services.practice_service import (
    preview_practice_session,
    create_practice_session,
    generate_session_report
)

router = APIRouter(prefix="/practice", tags=["Mock Interview Practice Studio"])


@router.post("/preview", response_model=PracticePreviewResponse)
def preview_session(
    payload: PracticePreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a preview of matching questions and targeted skills based on the configuration
    and SkillBridge data prior to starting the mock interview.
    """
    try:
        preview = preview_practice_session(db=db, user_id=1, request_data=payload)
        return preview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate practice session preview: {str(e)}"
        )


@router.post("/sessions", response_model=PracticeSessionRead, status_code=status.HTTP_201_CREATED)
def start_practice_session(
    payload: PracticeSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Configure and begin a new mock interview practice session.
    Populates ordered questions using SkillBridge personalization and Interview Memory Bank.
    """
    try:
        session_record = create_practice_session(db=db, user_id=1, session_in=payload)
        return session_record
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while starting the practice session: {str(e)}"
        )


@router.get("/sessions", response_model=List[PracticeSessionListItem])
def list_practice_sessions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: In Progress, Completed, Abandoned"),
    round_type: Optional[str] = Query(None, description="Filter by round type: Technical, HR, etc."),
    search: Optional[str] = Query(None, description="Search session name, target company, or role"),
    db: Session = Depends(get_db)
):
    """
    Retrieve previous mock interview sessions for practice history tracking.
    """
    query = db.query(PracticeSession).filter(PracticeSession.user_id == 1)

    if status_filter and status_filter != "All":
        query = query.filter(PracticeSession.status.ilike(status_filter.strip()))

    if round_type and round_type != "All":
        query = query.filter(PracticeSession.round_type.ilike(round_type.strip()))

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                PracticeSession.session_name.ilike(term),
                PracticeSession.target_company.ilike(term),
                PracticeSession.target_role.ilike(term)
            )
        )

    sessions = query.order_by(desc(PracticeSession.created_at)).all()

    # Build summary list items with calculated stats
    results = []
    for s in sessions:
        answers = s.answers or []
        attempted_count = sum(1 for a in answers if a.is_attempted)

        # Calculate average rating if ratings exist
        all_ratings = []
        for a in answers:
            if a.self_ratings and isinstance(a.self_ratings, dict):
                for val in a.self_ratings.values():
                    if isinstance(val, (int, float)) and 1 <= val <= 5:
                        all_ratings.append(float(val))

        avg_score = round(sum(all_ratings) / len(all_ratings), 1) if all_ratings else None

        results.append(
            PracticeSessionListItem(
                id=s.id,
                session_name=s.session_name,
                target_company=s.target_company,
                target_role=s.target_role,
                round_type=s.round_type,
                difficulty=s.difficulty,
                status=s.status,
                total_questions=s.total_questions or len(answers),
                attempted_count=attempted_count,
                average_score=avg_score,
                duration_seconds=s.duration_seconds or 0,
                started_at=s.started_at,
                completed_at=s.completed_at,
                created_at=s.created_at
            )
        )

    return results


@router.get("/sessions/{session_id}", response_model=PracticeSessionRead)
def get_practice_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve practice session details, state, and all populated questions/answers.
    """
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == 1
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice session with ID {session_id} not found."
        )

    return session


@router.put("/sessions/{session_id}/answers/{answer_id}", response_model=PracticeAnswerRead)
def update_practice_answer(
    session_id: int,
    answer_id: int,
    payload: PracticeAnswerUpdate,
    current_index: Optional[int] = Query(None, description="Optional current question index on session"),
    duration_seconds: Optional[int] = Query(None, description="Optional total duration so far in seconds"),
    db: Session = Depends(get_db)
):
    """
    Autosave answer text, submission state, self-assessment criteria ratings, or qualitative reflections.
    """
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == 1
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice session with ID {session_id} not found."
        )

    answer = db.query(PracticeAnswer).filter(
        PracticeAnswer.id == answer_id,
        PracticeAnswer.session_id == session_id
    ).first()

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Answer with ID {answer_id} not found in this practice session."
        )

    # Update session progress metadata if passed
    if current_index is not None and 0 <= current_index < session.total_questions:
        session.current_question_index = current_index
    if duration_seconds is not None and duration_seconds >= 0:
        session.duration_seconds = duration_seconds

    # Update answer fields
    if payload.answer_text is not None:
        answer.answer_text = payload.answer_text
        # If student wrote answer text and didn't explicitly set is_attempted, mark attempted
        if payload.is_attempted is None and payload.answer_text.strip():
            answer.is_attempted = True
            answer.is_skipped = False

    if payload.is_attempted is not None:
        answer.is_attempted = payload.is_attempted
        if payload.is_attempted:
            answer.is_skipped = False

    if payload.is_skipped is not None:
        answer.is_skipped = payload.is_skipped
        if payload.is_skipped:
            answer.is_attempted = False

    if payload.self_ratings is not None:
        # Merge or replace ratings
        current_ratings = dict(answer.self_ratings or {})
        current_ratings.update(payload.self_ratings)
        answer.self_ratings = current_ratings

    if payload.went_well is not None:
        answer.went_well = payload.went_well
    if payload.was_difficult is not None:
        answer.was_difficult = payload.was_difficult
    if payload.need_to_learn is not None:
        answer.need_to_learn = payload.need_to_learn
    if payload.better_approach is not None:
        answer.better_approach = payload.better_approach
    if payload.time_spent_seconds is not None:
        answer.time_spent_seconds = payload.time_spent_seconds

    db.commit()
    db.refresh(answer)
    return answer


@router.post("/sessions/{session_id}/finish", response_model=PracticeSessionReport)
def finish_practice_session(
    session_id: int,
    payload: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    Complete the practice session and generate a transparent performance summary report.
    """
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == 1
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice session with ID {session_id} not found."
        )

    # Update duration if provided
    if payload and "duration_seconds" in payload:
        dur = payload["duration_seconds"]
        if isinstance(dur, (int, float)) and dur >= 0:
            session.duration_seconds = int(dur)

    session.status = SessionStatus.COMPLETED.value
    session.completed_at = datetime.now(timezone.utc)

    # Check answers: if an answer has text but is_attempted was False, mark it attempted
    for a in session.answers:
        if a.answer_text and a.answer_text.strip() and not a.is_skipped:
            a.is_attempted = True

    db.commit()
    db.refresh(session)

    report = generate_session_report(session)
    return report


@router.post("/sessions/{session_id}/resume", response_model=PracticeSessionRead)
def resume_practice_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Resume an in-progress or paused practice session.
    """
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == 1
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice session with ID {session_id} not found."
        )

    if session.status != SessionStatus.IN_PROGRESS.value:
        # Re-activate session for continuation
        session.status = SessionStatus.IN_PROGRESS.value
        db.commit()
        db.refresh(session)

    return session


@router.get("/sessions/{session_id}/report", response_model=PracticeSessionReport)
def get_session_report(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve performance summary report for a completed mock interview session.
    """
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == 1
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice session with ID {session_id} not found."
        )

    report = generate_session_report(session)
    return report


@router.delete("/sessions/{session_id}")
def delete_practice_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a practice session and its recorded answers.
    Guarantees non-mutation: Original Interview Memory Bank questions and Job Applications are NOT deleted.
    """
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id,
        PracticeSession.user_id == 1
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice session with ID {session_id} not found."
        )

    db.delete(session)
    db.commit()

    return {
        "message": f"Practice session '{session.session_name}' and its answers deleted successfully.",
        "id": session_id
    }
