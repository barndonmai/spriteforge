from app.services.job_runner import process_job
from app.tasks.celery_app import celery_app


@celery_app.task(name="spriteforge.process_job")
def process_job_task(job_id: str) -> None:
    process_job(job_id)

