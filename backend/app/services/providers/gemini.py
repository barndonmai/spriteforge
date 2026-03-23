import mimetypes
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ValidationError
from PIL import Image

from app.services.image_utils import prepare_object_sprite_asset, save_png
from app.services.providers.base import GeneratedAsset, ImageProvider


class GeminiClassificationResponse(BaseModel):
    mode: Literal["character", "object"]
    rationale: str


class GeminiCharacterSummaryResponse(BaseModel):
    hair: str
    clothing: str
    accessories: str
    palette_notes: str
    silhouette_notes: str


class GeminiObjectSummaryResponse(BaseModel):
    object_category: str
    main_shape: str
    material_cues: str
    palette_notes: str
    silhouette_notes: str


class GeminiImageProvider(ImageProvider):
    name = "gemini"

    def __init__(self, api_key: str | None, model_name: str, image_model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.image_model_name = image_model_name

    def classify_reference(self, reference_image_path: Path, notes: str | None = None) -> Literal["character", "object"]:
        self._ensure_configured()
        response = self._generate_structured_response(
            reference_image_path=reference_image_path,
            prompt=self._build_classification_prompt(notes),
            schema_model=GeminiClassificationResponse,
        )
        return response.mode

    def summarize_reference(self, reference_image_path: Path, mode: Literal["character", "object"], notes: str | None = None) -> dict[str, Any]:
        self._ensure_configured()
        if mode == "character":
            response = self._generate_structured_response(
                reference_image_path=reference_image_path,
                prompt=self._build_character_summary_prompt(notes),
                schema_model=GeminiCharacterSummaryResponse,
            )
            return response.model_dump()

        response = self._generate_structured_response(
            reference_image_path=reference_image_path,
            prompt=self._build_object_summary_prompt(notes),
            schema_model=GeminiObjectSummaryResponse,
        )
        return response.model_dump()

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
            "Gemini character generation is not enabled yet. Keep SPRITEFORGE_PROVIDER=mock for asset generation."
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
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_image = self._generate_object_image(
            reference_image_path=reference_image_path,
            summary=summary,
        )
        prepared_image = self._prepare_generated_object_image(generated_image, target_size)

        output_path = output_dir / "object.png"
        save_png(prepared_image, output_path)
        return [GeneratedAsset(filename="object.png", label="object", path=output_path)]

    def _ensure_configured(self) -> None:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required when SPRITEFORGE_PROVIDER=gemini.")
        if not self.model_name:
            raise RuntimeError("GEMINI_MODEL is required when SPRITEFORGE_PROVIDER=gemini.")
        if not self.image_model_name:
            raise RuntimeError("GEMINI_IMAGE_MODEL is required when SPRITEFORGE_PROVIDER=gemini.")

    def _generate_structured_response(
        self,
        *,
        reference_image_path: Path,
        prompt: str,
        schema_model: type[BaseModel],
    ) -> BaseModel:
        genai, genai_types = self._load_sdk()

        mime_type = mimetypes.guess_type(reference_image_path.name)[0] or "image/png"
        image_bytes = reference_image_path.read_bytes()
        client = genai.Client(api_key=self.api_key)

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": schema_model.model_json_schema(),
                },
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc

        if not getattr(response, "text", None):
            raise RuntimeError("Gemini returned an empty response while generating structured output.")

        try:
            return schema_model.model_validate_json(response.text)
        except ValidationError as exc:
            raise RuntimeError(f"Gemini returned invalid structured JSON: {exc}") from exc

    def _build_classification_prompt(self, notes: str | None) -> str:
        note_text = notes.strip() if notes else "No user notes provided."
        return (
            "You are classifying a reference image for a 2D game asset workflow. "
            "Return 'character' only when the image strongly represents a person, humanoid, or character design. "
            "Return 'object' for props, items, products, bags, tools, packaging, signs, weapons, and ambiguous non-human subjects. "
            f"User notes: {note_text}"
        )

    def _build_character_summary_prompt(self, notes: str | None) -> str:
        note_text = notes.strip() if notes else "No user notes provided."
        return (
            "Summarize this image as a game-ready character reference. "
            "Keep each field concise and practical for sprite generation. "
            "Focus only on visible or strongly implied traits. "
            f"User notes: {note_text}"
        )

    def _build_object_summary_prompt(self, notes: str | None) -> str:
        note_text = notes.strip() if notes else "No user notes provided."
        return (
            "Summarize this image as a game-ready object or prop reference. "
            "Keep each field concise and practical for sprite generation. "
            "Focus only on visible or strongly implied traits. "
            f"User notes: {note_text}"
        )

    def _load_sdk(self):
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "google-genai is required for SPRITEFORGE_PROVIDER=gemini. Install backend dependencies from requirements.txt."
            ) from exc

        return genai, types

    def _generate_object_image(self, *, reference_image_path: Path, summary: dict[str, Any]) -> Image.Image:
        genai, genai_types = self._load_sdk()
        mime_type = mimetypes.guess_type(reference_image_path.name)[0] or "image/png"
        image_bytes = reference_image_path.read_bytes()
        client = genai.Client(api_key=self.api_key)

        prompt = self._build_object_generation_prompt(summary)

        try:
            response = client.models.generate_content(
                model=self.image_model_name,
                contents=[
                    prompt,
                    genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config=genai_types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini object generation request failed: {exc}") from exc

        for part in getattr(response, "parts", []) or []:
            if getattr(part, "inline_data", None) is not None:
                try:
                    sdk_image = part.as_image()
                    if sdk_image is None or not getattr(sdk_image, "image_bytes", None):
                        raise RuntimeError("Gemini returned an image part without decodable image bytes.")
                    return Image.open(BytesIO(sdk_image.image_bytes)).convert("RGBA")
                except Exception as exc:
                    raise RuntimeError(f"Gemini returned an unreadable generated image: {exc}") from exc

        raise RuntimeError("Gemini did not return an image for object generation.")

    def _prepare_generated_object_image(self, generated_image: Image.Image, target_size: int) -> Image.Image:
        return prepare_object_sprite_asset(generated_image, target_size)

    def _build_object_generation_prompt(self, summary: dict[str, Any]) -> str:
        category = summary.get("object_category", "object or prop")
        shape = summary.get("main_shape", "clean readable silhouette")
        materials = summary.get("material_cues", "simple material cues")
        palette = summary.get("palette_notes", "cohesive colors")
        silhouette = summary.get("silhouette_notes", "single centered subject")

        return (
            "Using the provided reference image, generate a single centered pixel-art object sprite for a 2D game asset pipeline. "
            "Render only the main object with no scene, no tabletop, no hand, no packaging layout, and no extra props. "
            "Use a transparent background if supported; otherwise keep the background flat, plain, and easy to remove. "
            "Prioritize a strong readable silhouette at small sizes, simple clustered pixel shapes, and clean sprite-like proportions over glossy illustration detail. "
            "Preserve the object's core identity, overall shape, and major colors, but simplify tiny print, tiny logos, micro-texture, and unnecessary surface details. "
            "Make it feel like a clean game-ready inventory or prop sprite rather than a tiny product photo or app icon. "
            "Keep the subject centered, isolated, and visually balanced with one object only. "
            "Do not add text, labels, watermarks, borders, shadows outside the object, background scenery, extra objects, hands, or characters. "
            f"Object category: {category}. "
            f"Main shape: {shape}. "
            f"Material cues: {materials}. "
            f"Palette notes: {palette}. "
            f"Silhouette notes: {silhouette}."
        )
