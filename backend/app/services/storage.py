import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings

settings = get_settings()


def ensure_storage_root() -> Path:
    storage_root = settings.storage_root_path
    storage_root.mkdir(parents=True, exist_ok=True)
    (storage_root / "references").mkdir(parents=True, exist_ok=True)
    (storage_root / "outputs").mkdir(parents=True, exist_ok=True)
    return storage_root


def get_reference_directory(job_id: str) -> Path:
    return ensure_storage_root() / "references" / job_id


def get_output_directory(job_id: str) -> Path:
    return ensure_storage_root() / "outputs" / job_id


def get_raw_output_directory(job_id: str) -> Path:
    directory = get_output_directory(job_id) / "raw"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_final_output_directory(job_id: str) -> Path:
    directory = get_output_directory(job_id) / "final"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_reference_upload(job_id: str, upload: UploadFile) -> tuple[Path, str]:
    extension = Path(upload.filename or "").suffix.lower() or ".png"
    filename = f"reference{extension}"
    reference_directory = get_reference_directory(job_id)
    reference_directory.mkdir(parents=True, exist_ok=True)
    destination = reference_directory / filename

    upload.file.seek(0)
    with destination.open("wb") as destination_file:
        shutil.copyfileobj(upload.file, destination_file)

    return destination, to_storage_relative_path(destination)


def get_manifest_path(job_id: str) -> Path:
    return get_output_directory(job_id) / "manifest.json"


def get_zip_path(job_id: str) -> Path:
    return get_output_directory(job_id) / f"spriteforge_{job_id}.zip"


def to_storage_relative_path(path: Path) -> str:
    return str(path.relative_to(settings.storage_root_path)).replace("\\", "/")


def make_unique_filename(prefix: str, extension: str) -> str:
    return f"{prefix}_{uuid4().hex}{extension}"

