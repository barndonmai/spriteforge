from pathlib import Path
from typing import Any, Literal

from PIL import Image

from app.services.image_utils import (
    build_palette_notes,
    build_silhouette_notes,
    darken_image,
    isolate_main_subject,
    mirror_image,
    normalize_to_canvas,
    save_png,
    tint_image,
)
from app.services.providers.base import CHARACTER_DIRECTIONS, GeneratedAsset, ImageProvider

CHARACTER_KEYWORDS = {
    "avatar",
    "character",
    "face",
    "fighter",
    "hero",
    "humanoid",
    "knight",
    "mage",
    "npc",
    "person",
    "player",
    "portrait",
    "warrior",
    "wizard",
}
CHARACTER_BODY_KEYWORDS = {
    "arm",
    "body",
    "eyes",
    "face",
    "hair",
    "hand",
    "head",
    "leg",
    "limb",
    "torso",
}
OBJECT_KEYWORDS = {
    "bag",
    "bottle",
    "box",
    "brand",
    "case",
    "chest",
    "container",
    "item",
    "logo",
    "object",
    "package",
    "packaging",
    "pouch",
    "product",
    "prop",
    "shopping",
    "sign",
    "tool",
    "weapon",
}


class MockImageProvider(ImageProvider):
    name = "mock"

    def classify_reference(self, reference_image_path: Path, notes: str | None = None) -> Literal["character", "object"]:
        image = Image.open(reference_image_path).convert("RGBA")
        text_blob = f"{reference_image_path.name} {notes or ''}".lower()
        opaque_bbox = image.getchannel("A").getbbox()

        # For the mock provider, object is the safe default.
        # We only return "character" when we see strong text or silhouette evidence
        # of a human-like figure. Product, branding, packaging, and generic prop cues
        # should dominate ambiguous cases so auto mode is less eager.
        object_score = self._count_keyword_hits(text_blob, OBJECT_KEYWORDS)
        character_score = self._count_keyword_hits(text_blob, CHARACTER_KEYWORDS)
        body_score = self._count_keyword_hits(text_blob, CHARACTER_BODY_KEYWORDS)

        if object_score > 0:
            return "object"
        if character_score >= 2 or (character_score >= 1 and body_score >= 1):
            return "character"
        if character_score == 0 and body_score == 0:
            return "object"

        if opaque_bbox and self._looks_human_like(image, opaque_bbox):
            return "character"
        return "object"

    def summarize_reference(self, reference_image_path: Path, mode: Literal["character", "object"], notes: str | None = None) -> dict[str, Any]:
        image = Image.open(reference_image_path).convert("RGBA")
        palette_notes = build_palette_notes(image)
        silhouette_notes = build_silhouette_notes(image)

        if mode == "character":
            return {
                "hair": self._find_keyword(notes, ["short", "long", "spiky", "curly"], fallback="not reliably extracted in mock mode"),
                "clothing": self._find_keyword(
                    notes,
                    ["armor", "robe", "jacket", "hoodie", "uniform"],
                    fallback="derived from the uploaded reference silhouette",
                ),
                "accessories": self._find_keyword(
                    notes,
                    ["hat", "glasses", "cape", "scarf", "sword"],
                    fallback="no clear accessory extracted in mock mode",
                ),
                "palette_notes": palette_notes,
                "silhouette_notes": silhouette_notes,
            }

        return {
            "object_category": self._find_keyword(
                notes,
                ["weapon", "tool", "chest", "potion", "orb", "vehicle"],
                fallback="generic object",
            ),
            "main_shape": self._shape_from_image(image),
            "material_cues": self._find_keyword(
                notes,
                ["wood", "metal", "stone", "cloth", "glass"],
                fallback="material cues approximated from uploaded colors",
            ),
            "palette_notes": palette_notes,
            "silhouette_notes": silhouette_notes,
        }

    def generate_character_directions(
        self,
        *,
        reference_image_path: Path,
        summary: dict[str, Any],
        target_size: int,
        output_dir: Path,
    ) -> list[GeneratedAsset]:
        isolated_subject = isolate_main_subject(Image.open(reference_image_path).convert("RGBA"))
        base_image = normalize_to_canvas(isolated_subject, target_size)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_assets: list[GeneratedAsset] = []
        for label, filename in CHARACTER_DIRECTIONS:
            variant = self._build_character_variant(base_image, label)
            output_path = output_dir / filename
            save_png(variant, output_path)
            generated_assets.append(GeneratedAsset(filename=filename, label=label, path=output_path))

        return generated_assets

    def generate_object_sprite(
        self,
        *,
        reference_image_path: Path,
        summary: dict[str, Any],
        target_size: int,
        output_dir: Path,
    ) -> list[GeneratedAsset]:
        isolated_subject = isolate_main_subject(Image.open(reference_image_path).convert("RGBA"))
        base_image = normalize_to_canvas(isolated_subject, target_size)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / "object.png"
        save_png(base_image, output_path)

        return [GeneratedAsset(filename="object.png", label="object", path=output_path)]

    def _build_character_variant(self, base_image: Image.Image, direction_label: str) -> Image.Image:
        variant = base_image.copy()
        if "right" in direction_label:
            variant = mirror_image(variant)
        if direction_label == "back":
            variant = darken_image(variant, 0.85)
        elif "front" in direction_label:
            variant = tint_image(variant, 1.05)
        elif "back" in direction_label:
            variant = darken_image(variant, 0.9)

        return variant

    def _shape_from_image(self, image: Image.Image) -> str:
        aspect_ratio = image.width / max(image.height, 1)
        if aspect_ratio < 0.75:
            return "vertical"
        if aspect_ratio > 1.25:
            return "horizontal"
        return "compact"

    def _find_keyword(self, notes: str | None, keywords: list[str], fallback: str) -> str:
        if not notes:
            return fallback

        normalized_notes = notes.lower()
        for keyword in keywords:
            if keyword in normalized_notes:
                return keyword
        return fallback

    def _count_keyword_hits(self, text: str, keywords: set[str]) -> int:
        return sum(1 for keyword in keywords if keyword in text)

    def _looks_human_like(self, image: Image.Image, opaque_bbox: tuple[int, int, int, int]) -> bool:
        bbox_width = opaque_bbox[2] - opaque_bbox[0]
        bbox_height = opaque_bbox[3] - opaque_bbox[1]
        if bbox_width <= 0 or bbox_height <= 0:
            return False

        aspect_ratio = bbox_height / bbox_width
        coverage_ratio = (bbox_width * bbox_height) / max(image.width * image.height, 1)
        if aspect_ratio < 1.35:
            return False
        if coverage_ratio < 0.12 or coverage_ratio > 0.72:
            return False

        silhouette = image.crop(opaque_bbox).getchannel("A")
        half_height = max(1, silhouette.height // 2)
        top_half_box = silhouette.crop((0, 0, silhouette.width, half_height)).getbbox()
        bottom_half_box = silhouette.crop((0, half_height, silhouette.width, silhouette.height)).getbbox()
        if not top_half_box or not bottom_half_box:
            return False

        top_width = top_half_box[2] - top_half_box[0]
        bottom_width = bottom_half_box[2] - bottom_half_box[0]

        # Human-like silhouettes tend to have a narrower upper section and
        # a vertically oriented footprint. If that is missing, stay with object.
        return top_width <= bottom_width and bottom_width > silhouette.width * 0.35
