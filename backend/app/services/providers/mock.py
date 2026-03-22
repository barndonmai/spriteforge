from pathlib import Path
from typing import Any, Literal

from PIL import Image

from app.services.image_utils import (
    build_palette_notes,
    build_silhouette_notes,
    darken_image,
    mirror_image,
    normalize_to_canvas,
    save_png,
    tint_image,
)
from app.services.providers.base import CHARACTER_DIRECTIONS, GeneratedAsset, ImageProvider

CHARACTER_KEYWORDS = {"character", "hero", "npc", "person", "player", "portrait"}
OBJECT_KEYWORDS = {"object", "item", "prop", "weapon", "tool", "pickup"}


class MockImageProvider(ImageProvider):
    name = "mock"

    def classify_reference(self, reference_image_path: Path, notes: str | None = None) -> Literal["character", "object"]:
        image = Image.open(reference_image_path).convert("RGBA")
        text_blob = f"{reference_image_path.name} {notes or ''}".lower()

        if any(keyword in text_blob for keyword in CHARACTER_KEYWORDS):
            return "character"
        if any(keyword in text_blob for keyword in OBJECT_KEYWORDS):
            return "object"

        return "character" if image.height >= image.width else "object"

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
        base_image = normalize_to_canvas(Image.open(reference_image_path).convert("RGBA"), target_size)
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
        base_image = normalize_to_canvas(Image.open(reference_image_path).convert("RGBA"), target_size)
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
