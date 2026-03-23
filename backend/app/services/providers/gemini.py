import mimetypes
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ValidationError
from PIL import Image

from app.services.image_utils import remove_chroma_green_background, save_png
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
    key_identifying_features: str


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
        keyed_image = remove_chroma_green_background(generated_image)

        output_path = output_dir / "object.png"
        save_png(keyed_image, output_path)
        return [GeneratedAsset(filename="object.png", label="object", path=output_path, skip_postprocessing=True)]

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
            "Capture the main object category, overall shape, material cues, dominant colors, silhouette notes, and key identifying features. "
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

    def _build_object_generation_prompt(self, summary: dict[str, Any]) -> str:
        category = self._sanitize_object_category(summary.get("object_category", "object"))
        shape = summary.get("main_shape", "overall silhouette from the reference image")
        palette = summary.get("palette_notes", "major colors from the reference image")
        material_cues = summary.get("material_cues", "surface and material cues from the reference image")
        silhouette_notes = summary.get("silhouette_notes", "clean front-facing object silhouette")
        key_features = self._sanitize_key_identifying_features(
            summary.get("key_identifying_features", "main identifying features from the reference image")
        )

        return (
            f"Create a pixel art sprite of only the main {category} from the reference image.\n\n"
            "Highest priority:\n"
            "- the output must read immediately as pixel art first\n"
            "- if any instruction conflicts with strong pixel-art readability, choose the more sprite-like pixel art interpretation\n"
            "- preserve identity through simplified pixel-art shapes and color blocks, not through literal product-render detail\n\n"
            "Reference summary:\n"
            f"- object category: {category}\n"
            f"- silhouette notes: {silhouette_notes}\n"
            f"- dominant colors: {palette}\n"
            f"- material cues: {material_cues}\n"
            f"- key identifying features: {key_features}\n\n"
            "Requirements:\n"
            f"- preserve the original object's silhouette and proportions ({shape})\n"
            "- preserve the major visual traits that make the object recognizable\n"
            "- keep the dominant colors consistent with the reference summary\n"
            "- preserve the key identifying features in a simplified, readable way\n"
            "- treat tiny branding text, repeated printed words, micro labels, and fine typography as optional details; simplify or omit them unless they are essential to the silhouette\n"
            "- simplify secondary surface graphics, side-panel copy, dense packaging text, and other non-structural print details for readability at sprite size\n"
            "- preserve readable negative space, holes, handles, and cutouts when they are part of the object's identity\n"
            "- use subtle dimensional form when it improves readability at sprite size\n"
            "- for objects with depth, prefer a gentle 3/4 sprite view with a visible side plane or top rim rather than a completely flat front view\n"
            "- use simple pixel-art shading to describe volume and edge planes without turning it into a realistic render\n"
            "- render this as true pixel art, not a painted cutout or product render\n"
            "- use a low native sprite resolution with crisp square pixels, hard edges, and a restrained color count\n"
            "- avoid soft airbrushing, photographic textures, smooth gradients, subpixel blur, or high-resolution print detail\n"
            "- place the object on a flat solid studio green-screen background using the exact vivid chroma-key color #00FF00 (RGB 0,255,0)\n"
            "- every background pixel outside the object must be that exact #00FF00 color with no shading, no lighting variation, no texture, no gradient, no checkerboard, and no color noise\n"
            "- that exact #00FF00 background will be removed in post-processing, so do not use that green on the object itself, in edge anti-aliasing, in reflections, in shadows, or in color spill\n"
            "- do not tint, soften, stylize, anti-alias, or approximate the green background; keep it as a hard exact chroma-key green screen color\n"
            "- keep all pixels outside the object on that same exact solid green background and do not include any other scene elements\n"
            "- do not include small branding text, tiny print, table, chairs, wall, floor, shadows outside the object, or any background elements other than the solid green backdrop\n"
            "- centered in frame\n"
            "- object should fill most of the canvas without being cropped\n"
            "- clean readable silhouette for a 2D game asset\n"
            "- game-ready object sprite\n"
            "- simplify details, but do not deform or over-stylize the object\n"
            "- avoid turning it into a generic icon, blob, chibi mascot object, glossy illustration, or product mockup\n"
            "- avoid extreme perspective tilt or dramatic camera angles"
        )

    def _sanitize_object_category(self, category: Any) -> str:
        normalized = str(category).strip() or "object"
        for prefix in ("branded ", "logo ", "packaged ", "product "):
            if normalized.lower().startswith(prefix):
                return normalized[len(prefix):]
        return normalized

    def _sanitize_key_identifying_features(self, key_features: Any) -> str:
        text = str(key_features).strip()
        if not text:
            return "main identifying features from the reference image"

        filtered_parts: list[str] = []
        for raw_part in re.split(r"[;,]", text):
            part = raw_part.strip()
            lowered = part.lower()
            if not part:
                continue
            if any(keyword in lowered for keyword in ("branding", "typography", "text", "label", "word", "printed", "logo", "slogan")):
                continue
            filtered_parts.append(part)

        if not filtered_parts:
            return "main structural features from the reference image"
        return ", ".join(filtered_parts)
