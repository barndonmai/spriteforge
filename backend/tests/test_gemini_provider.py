import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app.services.providers.gemini import (
    GeminiCharacterSummaryResponse,
    GeminiClassificationResponse,
    GeminiImageProvider,
    GeminiObjectSummaryResponse,
)


class GeminiImageProviderTests(unittest.TestCase):
    def test_missing_api_key_raises_clear_error(self) -> None:
        provider = GeminiImageProvider(api_key=None, model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")

        with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY is required"):
            provider.classify_reference(Path("unused.png"))

    def test_classification_uses_structured_response_mode(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        image_path = self._create_temp_image()

        try:
            with patch.object(
                provider,
                "_generate_structured_response",
                return_value=GeminiClassificationResponse(mode="object", rationale="Shopping bag with branding"),
            ) as mocked_generate:
                result = provider.classify_reference(image_path, notes="pink shopping bag")
        finally:
            image_path.unlink(missing_ok=True)

        self.assertEqual(result, "object")
        mocked_generate.assert_called_once()

    def test_summary_returns_object_schema_dump(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        image_path = self._create_temp_image()

        try:
            with patch.object(
                provider,
                "_generate_structured_response",
                return_value=GeminiObjectSummaryResponse(
                    object_category="shopping bag",
                    main_shape="tall rectangular bag with curved handles",
                    material_cues="glossy coated paper",
                    palette_notes="pink body, black handles",
                    silhouette_notes="single centered prop silhouette",
                ),
            ):
                result = provider.summarize_reference(image_path, mode="object", notes="store shopping bag")
        finally:
            image_path.unlink(missing_ok=True)

        self.assertEqual(result["object_category"], "shopping bag")
        self.assertEqual(result["material_cues"], "glossy coated paper")

    def test_summary_returns_character_schema_dump(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        image_path = self._create_temp_image()

        try:
            with patch.object(
                provider,
                "_generate_structured_response",
                return_value=GeminiCharacterSummaryResponse(
                    hair="short dark hair",
                    clothing="blue jacket and boots",
                    accessories="small satchel",
                    palette_notes="blue, tan, dark brown",
                    silhouette_notes="compact humanoid with readable shoulder shape",
                ),
            ):
                result = provider.summarize_reference(image_path, mode="character", notes="adventurer")
        finally:
            image_path.unlink(missing_ok=True)

        self.assertEqual(result["hair"], "short dark hair")
        self.assertEqual(result["accessories"], "small satchel")

    def test_object_generation_returns_saved_png_asset(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        reference_image_path = self._create_temp_image()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "outputs"

            try:
                with patch.object(provider, "_generate_object_image", return_value=Image.new("RGBA", (32, 48), (255, 0, 0, 255))):
                    generated_assets = provider.generate_object_sprite(
                        reference_image_path=reference_image_path,
                        summary={"object_category": "potion bottle"},
                        target_size=64,
                        output_dir=output_dir,
                    )
            finally:
                reference_image_path.unlink(missing_ok=True)

            self.assertEqual(len(generated_assets), 1)
            self.assertEqual(generated_assets[0].filename, "object.png")
            self.assertTrue(generated_assets[0].path.exists())

            saved_image = Image.open(generated_assets[0].path).convert("RGBA")
            self.assertEqual(saved_image.size, (64, 64))
            self.assertEqual(saved_image.getpixel((0, 0))[3], 0)
            self.assertEqual(saved_image.getpixel((63, 63))[3], 0)

    def test_object_generation_surfaces_missing_image_response(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")

        with self.assertRaisesRegex(RuntimeError, "Gemini did not return an image"):
            with patch.object(provider, "_load_sdk", return_value=self._make_fake_sdk_without_image()):
                provider._generate_object_image(
                    reference_image_path=self._create_temp_image(),
                    summary={"object_category": "shopping bag"},
                )

    def _create_temp_image(self) -> Path:
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_file.close()
        Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(temp_file.name, format="PNG")
        return Path(temp_file.name)

    def _make_fake_sdk_without_image(self):
        class FakePart:
            inline_data = None

        class FakeResponse:
            parts = [FakePart()]

        class FakeModels:
            def generate_content(self, **kwargs):
                return FakeResponse()

        class FakeClient:
            def __init__(self, api_key: str):
                self.models = FakeModels()

        class FakeGenAI:
            Client = FakeClient

        class FakePartFactory:
            @staticmethod
            def from_bytes(data: bytes, mime_type: str):
                return {"data": data, "mime_type": mime_type}

        class FakeGenerateContentConfig:
            def __init__(self, response_modalities):
                self.response_modalities = response_modalities

        class FakeTypes:
            Part = FakePartFactory
            GenerateContentConfig = FakeGenerateContentConfig

        return FakeGenAI, FakeTypes
