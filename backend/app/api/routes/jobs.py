from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.jobs import JobCreateResponse, JobResultsResponse, JobStatusResponse
from app.services.job_service import create_job_from_upload, get_job_or_404, read_results, serialize_job_status

router = APIRouter()
settings = get_settings()


@router.post("", response_model=JobCreateResponse)
def create_job(
    reference_image: UploadFile = File(...),
    mode: str = Form(...),
    target_size: int = Form(64),
    notes: str | None = Form(None),
    session: Session = Depends(get_db),
) -> JobCreateResponse:
    job = create_job_from_upload(
        session,
        reference_image=reference_image,
        mode=mode,
        target_size=target_size,
        notes=notes,
    )
    return JobCreateResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, session: Session = Depends(get_db)) -> JobStatusResponse:
    job = get_job_or_404(session, job_id)
    return serialize_job_status(job)


@router.get("/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(job_id: str, request: Request, session: Session = Depends(get_db)) -> JobResultsResponse:
    job = get_job_or_404(session, job_id)
    return read_results(job, request)


@router.get("/{job_id}/download", name="download_job_results")
def download_job_results(job_id: str, session: Session = Depends(get_db)) -> FileResponse:
    job = get_job_or_404(session, job_id)
    if job.status != "completed" or not job.zip_path:
        raise HTTPException(status_code=409, detail="Job zip is not ready yet.")

    return FileResponse(
        path=str(settings.storage_root_path / job.zip_path),
        filename=f"spriteforge_{job_id}.zip",
        media_type="application/zip",
    )
