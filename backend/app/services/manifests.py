from datetime import datetime, timezone
from pathlib import Path

from app.models.job import Job
from app.services.storage import to_storage_relative_path


def build_manifest(job: Job, final_output_paths: list[Path]) -> dict:
    outputs = []
    for output_path in final_output_paths:
        label = output_path.stem.replace("_", " ")
        outputs.append(
            {
                "filename": output_path.name,
                "label": label,
                "storage_path": to_storage_relative_path(output_path),
            }
        )

    return {
        "job_id": job.id,
        "status": job.status,
        "requested_mode": job.requested_mode,
        "resolved_mode": job.resolved_mode,
        "target_size": job.target_size,
        "provider": job.provider_name,
        "reference_image_path": job.reference_image_path,
        "reference_summary": job.reference_summary,
        "created_at": job.created_at.astimezone(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "outputs": outputs,
    }

