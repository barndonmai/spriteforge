from pathlib import Path
from typing import Any, Literal

from app.services.providers.base import GeneratedAsset, ImageProvider


class GeminiImageProvider(ImageProvider):
    name = "gemini"

    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def classify_reference(self, reference_image_path: Path, notes: str | None = None) -> Literal["character", "object"]:
        self._ensure_configured()
        raise NotImplementedError(
            "GeminiImageProvider is scaffolded but not implemented yet. Use SPRITEFORGE_PROVIDER=mock for the working local MVP."
        )

    def summarize_reference(self, reference_image_path: Path, mode: Literal["character", "object"], notes: str | None = None) -> dict[str, Any]:
        self._ensure_configured()
        raise NotImplementedError(
            "Gemini reference summarization is scaffolded but not implemented yet. Use the mock provider for now."
        )

    def generate_character_directions(
        self,
        *,
        reference_image_path: Path,
        summary: dict[str, Any],
        target_size: int,
        output_dir: Path,
    ) -> list[GeneratedAsset]:
        self._ensure_configured()
        raise NotImplementedError(
            "Gemini character generation is scaffolded but not implemented yet. The interface and wiring are ready for a later implementation."
        )

    def generate_object_sprite(
        self,
        *,
        reference_image_path: Path,
        summary: dict[str, Any],
        target_size: int,
        output_dir: Path,
    ) -> list[GeneratedAsset]:
        self._ensure_configured()
        raise NotImplementedError(
            "Gemini object generation is scaffolded but not implemented yet. The interface and wiring are ready for a later implementation."
        )

    def _ensure_configured(self) -> None:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required when SPRITEFORGE_PROVIDER=gemini.")

