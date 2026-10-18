"""
SkillBridge Resume Builder API Router
Provides REST endpoints for:
- Full CRUD management of student resume drafts
- Duplicating and versioning resumes for multiple target roles
- Explainable ATS quality review and action-verb insights
- Job-specific keyword tailoring against saved opportunities
- Native ATS-compliant Word (.docx) file export
- High-quality student sample resume template
"""

from typing import List, Optional
from datetime import datetime, timezone
import re
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Resume, JobApplication, JobAnalysis
from app.schemas import (
    ResumeCreate,
    ResumeUpdate,
    ResumeRead,
    ResumeListItem,
    ResumeReviewResponse,
    ResumeTailorResponse
)
from app.services.resume_service import (
    analyze_resume_quality,
    tailor_resume_to_job,
    generate_docx_resume,
    SAMPLE_RESUMES
)

router = APIRouter(prefix="/resumes", tags=["ATS Resume Builder"])


@router.get("", response_model=List[ResumeListItem])
def list_resumes(
    search: Optional[str] = Query(None, description="Search resume title or target role"),
    db: Session = Depends(get_db)
):
    """
    List all saved resume drafts for the current user.
    """
    query = db.query(Resume).filter(Resume.user_id == 1)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(Resume.title.ilike(term) | Resume.target_role.ilike(term))

    resumes = query.order_by(desc(Resume.updated_at)).all()

    items = []
    for r in resumes:
        # Calculate a quick quality score for list display
        r_dict = {
            "id": r.id,
            "contact_info": r.contact_info,
            "summary": r.summary,
            "skills": r.skills,
            "education": r.education,
            "projects": r.projects,
            "experience": r.experience,
            "section_config": r.section_config
        }
        review = analyze_resume_quality(r_dict)
        items.append(
            ResumeListItem(
                id=r.id,
                title=r.title,
                target_role=r.target_role,
                target_job_id=r.target_job_id,
                target_company=r.target_job.company_name if r.target_job else None,
                template_id=r.template_id,
                completeness_score=review["overall_score"],
                created_at=r.created_at,
                updated_at=r.updated_at
            )
        )
    return items


@router.post("", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
def create_resume(
    payload: ResumeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new resume draft.
    """
    # Verify target job exists if provided
    if payload.target_job_id:
        job = db.query(JobApplication).filter(
            JobApplication.id == payload.target_job_id,
            JobApplication.user_id == 1
        ).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target job application with ID {payload.target_job_id} not found."
            )

    new_resume = Resume(
        user_id=1,
        title=payload.title.strip() or "Untitled Resume",
        target_job_id=payload.target_job_id,
        target_role=payload.target_role,
        template_id=payload.template_id or "classic_ats",
        contact_info=payload.contact_info.model_dump(),
        summary=payload.summary or "",
        skills=[s.model_dump() for s in payload.skills],
        education=[e.model_dump() for e in payload.education],
        projects=[p.model_dump() for p in payload.projects],
        experience=[ex.model_dump() for ex in payload.experience],
        additional_sections=payload.additional_sections.model_dump(),
        section_config=payload.section_config.model_dump()
    )

    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    return new_resume


@router.get("/sample", response_model=ResumeCreate)
def get_sample_resume():
    """
    Returns an industry-standard, un-hallucinated student resume template.
    """
    return SAMPLE_RESUMES["software_engineering"]


@router.get("/{resume_id}", response_model=ResumeRead)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve single saved resume by ID.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == 1
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )

    return resume


@router.put("/{resume_id}", response_model=ResumeRead)
def update_resume(
    resume_id: int,
    payload: ResumeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing resume draft.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == 1
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )

    if payload.target_job_id is not None:
        if payload.target_job_id > 0:
            job = db.query(JobApplication).filter(
                JobApplication.id == payload.target_job_id,
                JobApplication.user_id == 1
            ).first()
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Target job application with ID {payload.target_job_id} not found."
                )
            resume.target_job_id = payload.target_job_id
        else:
            resume.target_job_id = None

    if payload.title is not None:
        resume.title = payload.title.strip() or resume.title
    if payload.target_role is not None:
        resume.target_role = payload.target_role
    if payload.template_id is not None:
        resume.template_id = payload.template_id
    if payload.contact_info is not None:
        resume.contact_info = payload.contact_info.model_dump()
    if payload.summary is not None:
        resume.summary = payload.summary
    if payload.skills is not None:
        resume.skills = [s.model_dump() for s in payload.skills]
    if payload.education is not None:
        resume.education = [e.model_dump() for e in payload.education]
    if payload.projects is not None:
        resume.projects = [p.model_dump() for p in payload.projects]
    if payload.experience is not None:
        resume.experience = [ex.model_dump() for ex in payload.experience]
    if payload.additional_sections is not None:
        resume.additional_sections = payload.additional_sections.model_dump()
    if payload.section_config is not None:
        resume.section_config = payload.section_config.model_dump()

    resume.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/{resume_id}/duplicate", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
def duplicate_resume(
    resume_id: int,
    new_title: Optional[str] = Query(None, description="New title for duplicated resume"),
    db: Session = Depends(get_db)
):
    """
    Duplicate an existing resume draft for role-specific tailoring.
    """
    source = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == 1
    ).first()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source resume with ID {resume_id} not found."
        )

    title = new_title.strip() if new_title and new_title.strip() else f"{source.title} (Copy)"

    cloned = Resume(
        user_id=source.user_id,
        title=title,
        target_job_id=source.target_job_id,
        target_role=source.target_role,
        template_id=source.template_id,
        contact_info=source.contact_info,
        summary=source.summary,
        skills=source.skills,
        education=source.education,
        projects=source.projects,
        experience=source.experience,
        additional_sections=source.additional_sections,
        section_config=source.section_config
    )

    db.add(cloned)
    db.commit()
    db.refresh(cloned)
    return cloned


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a saved resume. Never mutates or deletes underlying jobs.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == 1
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )

    db.delete(resume)
    db.commit()
    return {"ok": True, "message": f"Resume {resume_id} successfully deleted."}


@router.post("/{resume_id}/review", response_model=ResumeReviewResponse)
def review_resume(
    resume_id: int,
    db: Session = Depends(get_db)
):
    """
    Run transparent, rule-based quality review checking ATS compliance,
    action verbs, and formatting.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == 1
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )

    resume_dict = {
        "id": resume.id,
        "contact_info": resume.contact_info,
        "summary": resume.summary,
        "skills": resume.skills,
        "education": resume.education,
        "projects": resume.projects,
        "experience": resume.experience,
        "section_config": resume.section_config,
        "additional_sections": resume.additional_sections
    }

    review = analyze_resume_quality(resume_dict)
    return review


@router.post("/{resume_id}/tailor/{job_id}", response_model=ResumeTailorResponse)
def tailor_resume(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Tailor resume against a saved job opportunity and existing JD analyzer results.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == 1
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )

    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == 1
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with ID {job_id} not found."
        )

    # Check for latest analysis associated with this job
    analysis = db.query(JobAnalysis).filter(
        JobAnalysis.job_id == job_id,
        JobAnalysis.user_id == 1
    ).order_by(desc(JobAnalysis.created_at)).first()

    resume_dict = {
        "id": resume.id,
        "contact_info": resume.contact_info,
        "summary": resume.summary,
        "skills": resume.skills,
        "education": resume.education,
        "projects": resume.projects,
        "experience": resume.experience,
        "additional_sections": resume.additional_sections
    }

    job_dict = {
        "id": job.id,
        "company_name": job.company_name,
        "job_title": job.job_title,
        "job_description": job.job_description,
        "skills": job.skills,
        "notes": job.notes
    }

    analysis_dict = None
    if analysis:
        analysis_dict = {
            "required_skills": analysis.required_skills,
            "preferred_skills": analysis.preferred_skills,
            "match_score": analysis.match_score
        }

    tailor_result = tailor_resume_to_job(resume_dict, job_dict, analysis_dict)
    return tailor_result


@router.get("/{resume_id}/export/docx")
def export_docx(
    resume_id: int,
    db: Session = Depends(get_db)
):
    """
    Export ATS-compliant single-column Microsoft Word (.docx) document.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == 1
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )

    resume_dict = {
        "id": resume.id,
        "title": resume.title,
        "contact_info": resume.contact_info,
        "summary": resume.summary,
        "skills": resume.skills,
        "education": resume.education,
        "projects": resume.projects,
        "experience": resume.experience,
        "additional_sections": resume.additional_sections,
        "section_config": resume.section_config
    }

    docx_bytes = generate_docx_resume(resume_dict)

    # Safe filename sanitization
    clean_title = re.sub(r"[^\w\-_.]", "_", resume.title)
    encoded_filename = urllib.parse.quote(f"{clean_title}.docx")

    headers = {
        "Content-Disposition": f'attachment; filename="{clean_title}.docx"; filename*=UTF-8\'\'{encoded_filename}'
    }

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers
    )
