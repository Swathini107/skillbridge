from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import JobAnalysis, JobApplication, User
from app.schemas import (
    AnalyzeRequest,
    AnalysisResponse,
    AnalysisHistoryItem
)
from app.services.skill_extractor import analyze_job_and_profile

router = APIRouter(prefix="/analyzer", tags=["Job Analyzer"])


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
def run_analysis(
    req: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Extracts requirements, compares with candidate resume/profile,
    calculates match percentage, and optionally stores analysis history in SQLite.
    """
    # 1. If job_id is provided, verify job exists and populate metadata if empty
    company_name = req.company_name
    job_title = req.job_title

    if req.job_id:
        job = db.query(JobApplication).filter(JobApplication.id == req.job_id).first()
        if job:
            if not company_name:
                company_name = job.company_name
            if not job_title:
                job_title = job.job_title

    # 2. Run rule-based NLP extraction and scoring
    try:
        result = analyze_job_and_profile(
            job_description=req.job_description,
            resume_or_profile_text=req.resume_or_profile_text
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )

    saved_id = None
    created_at = None

    # 3. Persist analysis history if requested
    if req.save_analysis:
        # Ensure default demo user exists
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = User(id=1, name="Student Demo", email="student@skillbridge.edu")
            db.add(user)
            db.commit()
            db.refresh(user)

        new_analysis = JobAnalysis(
            user_id=user.id,
            job_id=req.job_id,
            company_name=company_name,
            job_title=job_title,
            match_score=result["match_score"],
            required_skills=result["required_skills"],
            preferred_skills=result["preferred_skills"],
            unclassified_skills=result["unclassified_skills"],
            other_requirements=result["other_requirements"],
            matching_skills=result["matching_skills"],
            missing_skills=result["missing_skills"],
            score_breakdown=result["score_breakdown"],
            recommendations=result["recommendations"]
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        saved_id = new_analysis.id
        created_at = new_analysis.created_at

    return AnalysisResponse(
        id=saved_id,
        job_id=req.job_id,
        company_name=company_name,
        job_title=job_title,
        match_score=result["match_score"],
        score_breakdown=result["score_breakdown"],
        required_skills=result["required_skills"],
        preferred_skills=result["preferred_skills"],
        unclassified_skills=result["unclassified_skills"],
        other_requirements=result["other_requirements"],
        user_detected_skills=result["user_detected_skills"],
        matching_skills=result["matching_skills"],
        missing_skills=result["missing_skills"],
        matching_required=result["matching_required"],
        missing_required=result["missing_required"],
        matching_preferred=result["matching_preferred"],
        missing_preferred=result["missing_preferred"],
        recommendations=result["recommendations"],
        disclaimer=result["disclaimer"],
        created_at=created_at
    )


@router.get("/history", response_model=List[AnalysisHistoryItem])
def get_analysis_history(
    db: Session = Depends(get_db)
):
    """
    List past job description analyses ordered from most recent to oldest.
    """
    # Uses default demo student (user_id=1)
    analyses = db.query(JobAnalysis).filter(JobAnalysis.user_id == 1).order_by(desc(JobAnalysis.created_at)).all()

    history_items = []
    for item in analyses:
        matching = item.matching_skills or []
        missing = item.missing_skills or []
        req_skills = item.required_skills or []

        history_items.append(
            AnalysisHistoryItem(
                id=item.id,
                job_id=item.job_id,
                company_name=item.company_name,
                job_title=item.job_title,
                match_score=item.match_score,
                matching_count=len(matching),
                missing_count=len(missing),
                required_count=len(req_skills),
                created_at=item.created_at
            )
        )
    return history_items


@router.get("/history/{analysis_id}", response_model=AnalysisResponse)
def get_single_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve full structured results of a past analysis.
    """
    analysis = db.query(JobAnalysis).filter(
        JobAnalysis.id == analysis_id,
        JobAnalysis.user_id == 1
    ).first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis record with ID {analysis_id} not found."
        )

    # Reconstitute matching/missing subsets for detailed UI viewing
    all_matching = analysis.matching_skills or []
    all_missing = analysis.missing_skills or []

    matching_required = [m for m in all_matching if m.get("type") == "required"]
    missing_required = [m for m in all_missing if m.get("type") == "required"]
    matching_preferred = [m for m in all_matching if m.get("type") == "preferred"]
    missing_preferred = [m for m in all_missing if m.get("type") == "preferred"]

    return AnalysisResponse(
        id=analysis.id,
        job_id=analysis.job_id,
        company_name=analysis.company_name,
        job_title=analysis.job_title,
        match_score=analysis.match_score,
        score_breakdown=analysis.score_breakdown or {},
        required_skills=analysis.required_skills or [],
        preferred_skills=analysis.preferred_skills or [],
        unclassified_skills=analysis.unclassified_skills or [],
        other_requirements=analysis.other_requirements or [],
        user_detected_skills=[],
        matching_skills=all_matching,
        missing_skills=all_missing,
        matching_required=matching_required,
        missing_required=missing_required,
        matching_preferred=matching_preferred,
        missing_preferred=missing_preferred,
        recommendations=analysis.recommendations or [],
        disclaimer="This score is a transparent, rule-based estimate of keyword and skill coverage. It is not an AI hiring prediction or guarantee of interview selection.",
        created_at=analysis.created_at
    )


@router.delete("/history/{analysis_id}", status_code=status.HTTP_200_OK)
def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Permanently delete a saved analysis history record.
    """
    analysis = db.query(JobAnalysis).filter(
        JobAnalysis.id == analysis_id,
        JobAnalysis.user_id == 1
    ).first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis record with ID {analysis_id} not found."
        )

    db.delete(analysis)
    db.commit()
    return {"success": True, "message": f"Analysis record #{analysis_id} successfully deleted."}
