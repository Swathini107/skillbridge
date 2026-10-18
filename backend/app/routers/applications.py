from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, and_, asc, desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JobApplication, User
from app.schemas import (
    JobApplicationCreate,
    JobApplicationUpdate,
    JobApplicationStatusUpdate,
    JobApplicationRead,
    ApplicationStatsResponse,
    VALID_STATUSES
)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("/stats", response_model=ApplicationStatsResponse)
def get_application_stats(db: Session = Depends(get_db)):
    """
    Get aggregated application metrics for the student career dashboard.
    Counts are computed live from actual database records via SQL aggregation.
    """
    today = date.today()
    next_week = today + timedelta(days=7)

    # Perform SQL GROUP BY aggregation scoped to current user
    status_rows = db.query(
        JobApplication.application_status,
        func.count(JobApplication.id)
    ).filter(
        JobApplication.user_id == 1
    ).group_by(JobApplication.application_status).all()

    status_counts = {s: 0 for s in VALID_STATUSES}
    total_jobs = 0
    for st, count in status_rows:
        total_jobs += count
        current_status = st
        if current_status == "Interviewing":
            current_status = "Interview"
        if current_status in status_counts:
            status_counts[current_status] += count

    # Approaching deadlines: within 7 days from today and not closed
    approaching = db.query(JobApplication).filter(
        and_(
            JobApplication.user_id == 1,
            JobApplication.deadline.isnot(None),
            JobApplication.deadline >= today,
            JobApplication.deadline <= next_week,
            JobApplication.application_status.notin_(["Rejected", "Withdrawn", "REJECTED", "WITHDRAWN"])
        )
    ).count()

    total_saved = status_counts["Saved"]
    apps_submitted = status_counts["Applied"]
    interviews = status_counts["Interview"] + status_counts["Assessment"]
    offers = status_counts["Offer"]

    return ApplicationStatsResponse(
        total_saved_jobs=total_saved,
        applications_submitted=apps_submitted,
        interviews_in_progress=interviews,
        offers_received=offers,
        total_jobs=total_jobs,
        approaching_deadlines=approaching,
        status_breakdown=status_counts
    )


@router.get("", response_model=List[JobApplicationRead])
def list_applications(
    search: Optional[str] = Query(None, description="Search across company name, role, or required skills"),
    status: Optional[str] = Query(None, description="Filter by application status"),
    work_mode: Optional[str] = Query(None, description="Filter by work mode (On-site, Hybrid, Remote)"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type (Internship, Full-time, Part-time)"),
    sort_by: Optional[str] = Query("recent", description="Sort by: recent, deadline, company"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Optional maximum number of records to return"),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all job opportunities with flexible search, filter, and sorting options.
    """
    query = db.query(JobApplication).filter(JobApplication.user_id == 1)

    # 1. Search Query
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                JobApplication.company_name.ilike(term),
                JobApplication.job_title.ilike(term),
                JobApplication.skills.ilike(term)
            )
        )

    # 2. Status Filter
    if status and status.strip():
        target_status = status.strip().capitalize()
        if target_status == "Interviewing":
            target_status = "Interview"
        query = query.filter(JobApplication.application_status == target_status)

    # 3. Work Mode Filter
    if work_mode and work_mode.strip():
        query = query.filter(JobApplication.work_mode == work_mode.strip())

    # 4. Employment Type Filter
    if employment_type and employment_type.strip():
        query = query.filter(JobApplication.employment_type == employment_type.strip())

    # 5. Sorting
    is_asc = sort_order.lower() == "asc" if sort_order else False

    if sort_by == "deadline":
        # Put null deadlines at the end
        if is_asc:
            query = query.order_by(
                JobApplication.deadline.is_(None),
                asc(JobApplication.deadline)
            )
        else:
            query = query.order_by(
                JobApplication.deadline.is_(None),
                desc(JobApplication.deadline)
            )
    elif sort_by == "company":
        query = query.order_by(
            asc(func.lower(JobApplication.company_name)) if is_asc else desc(func.lower(JobApplication.company_name))
        )
    else:
        # Default: recently created
        query = query.order_by(
            asc(JobApplication.created_at) if is_asc else desc(JobApplication.created_at)
        )

    if limit is not None:
        query = query.limit(limit).offset(offset)

    return query.all()


@router.post("", response_model=JobApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    application_in: JobApplicationCreate,
    db: Session = Depends(get_db)
):
    """
    Save a new job opportunity with validation and default demo user attribution.
    """
    user_id = application_in.user_id or 1
    # Check that user exists; if not create default
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=1, name="Student Demo", email="student@skillbridge.edu")
        db.add(user)
        db.commit()
        db.refresh(user)

    data = application_in.model_dump()
    data["user_id"] = user.id

    new_application = JobApplication(**data)
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    return new_application


@router.get("/{application_id}", response_model=JobApplicationRead)
def get_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve details for a specific job application by ID.
    """
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == 1
    ).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with ID {application_id} not found."
        )
    return application


@router.put("/{application_id}", response_model=JobApplicationRead)
def update_application(
    application_id: int,
    application_in: JobApplicationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update details of an existing job application.
    """
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == 1
    ).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with ID {application_id} not found."
        )

    update_data = application_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)

    application.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return application


@router.patch("/{application_id}/status", response_model=JobApplicationRead)
def update_application_status(
    application_id: int,
    status_in: JobApplicationStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Quickly update the application status for an opportunity.
    """
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == 1
    ).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with ID {application_id} not found."
        )

    application.application_status = status_in.application_status
    application.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=status.HTTP_200_OK)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a saved job opportunity.
    """
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == 1
    ).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with ID {application_id} not found."
        )

    db.delete(application)
    db.commit()
    return {"message": f"Job application '{application.job_title}' at '{application.company_name}' was successfully deleted."}
