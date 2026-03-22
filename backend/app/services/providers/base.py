from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

CHARACTER_DIRECTIONS: list[tuple[str, str]] = [
    ("front", "front.png"),
    ("back", "back.png"),
    ("left", "left.png"),
    ("right", "right.png"),
    ("front left", "front_left.png"),
    ("front right", "front_right.png"),
    ("back left", "back_left.png"),
    ("back right", "back_right.png"),
]


@dataclass(slots=True)
class GeneratedAsset:
    filename: str
    label: str
    path: Path


class ImageProvider(ABC):
    name: str

    @abstractmethod
    def classify_reference(self, reference_image_path: Path, notes: str | None = None) -> Literal["character", "object"]:
        raise NotImplementedError

    @abstractmethod
    def summarize_reference(self, reference_image_path: Path, mode: Literal["character", "object"], notes: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate_character_directions(
        self,
        *,
        reference_image_path: Path,
        summary: dict[str, Any],
        target_size: int,
        output_dir: Path,
    ) -> list[GeneratedAsset]:
        raise NotImplementedError

    @abstractmethod
    def generate_object_sprite(
        self,
        *,
        reference_image_path: Path,
        summary: dict[str, Any],
        target_size: int,
        output_dir: Path,
    ) -> list[GeneratedAsset]:
        raise NotImplementedError

