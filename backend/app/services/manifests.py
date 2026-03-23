from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from app.models.job import Job
from app.services.datetime_utils import ensure_utc_datetime
from app.services.storage import to_storage_relative_path


def build_manifest(job: Job, final_output_paths: list[Path]) -> dict:
    if not final_output_paths:
        raise ValueError("Cannot build a manifest without any final output assets.")

    outputs = []
    for output_path in final_output_paths:
        if not output_path.exists():
            raise FileNotFoundError(f"Missing final output asset: {output_path.name}")

        with Image.open(output_path) as image:
            width, height = image.size

        label = output_path.stem.replace("_", " ")
        outputs.append(
            {
                "filename": output_path.name,
                "label": label,
                "storage_path": to_storage_relative_path(output_path),
                "width": width,
                "height": height,
            }
        )

    return {
        "job_id": job.id,
        "status": "completed",
        "requested_mode": job.requested_mode,
        "resolved_mode": job.resolved_mode,
        "target_size": job.target_size,
        "provider": job.provider_name,
        "reference_image_path": job.reference_image_path,
        "reference_summary": job.reference_summary,
        "created_at": ensure_utc_datetime(job.created_at).isoformat(),
        "completed_at": ensure_utc_datetime(job.completed_at or datetime.now(timezone.utc)).isoformat(),
        "outputs": outputs,
    }
