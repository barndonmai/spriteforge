from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job


def create_job(
    session: Session,
    *,
    job_id: str,
    requested_mode: str,
    target_size: int,
    notes: str | None,
    provider_name: str,
    reference_image_name: str,
    reference_image_path: str,
) -> Job:
    job = Job(
        id=job_id,
        status="queued",
        requested_mode=requested_mode,
        target_size=target_size,
        notes=notes,
        provider_name=provider_name,
        reference_image_name=reference_image_name,
        reference_image_path=reference_image_path,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_job(session: Session, job_id: str) -> Job | None:
    statement = select(Job).where(Job.id == job_id)
    return session.execute(statement).scalar_one_or_none()


def save_job(session: Session, job: Job) -> Job:
    session.add(job)
    session.commit()
    session.refresh(job)
    return job

