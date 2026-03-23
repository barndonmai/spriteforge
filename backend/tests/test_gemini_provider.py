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
                    key_identifying_features="two dark handles and a central front symbol",
                ),
            ):
                result = provider.summarize_reference(image_path, mode="object", notes="store shopping bag")
        finally:
            image_path.unlink(missing_ok=True)

        self.assertEqual(result["object_category"], "shopping bag")
        self.assertEqual(result["material_cues"], "glossy coated paper")
        self.assertEqual(result["key_identifying_features"], "two dark handles and a central front symbol")

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

        generated_image = Image.new("RGBA", (32, 48), (149, 181, 128, 255))
        for x in range(6, 26):
            for y in range(8, 42):
                generated_image.putpixel((x, y), (255, 0, 0, 255))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "outputs"

            try:
                with patch.object(provider, "_generate_object_image", return_value=generated_image):
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
            self.assertTrue(generated_assets[0].skip_postprocessing)

            saved_image = Image.open(generated_assets[0].path).convert("RGBA")
            self.assertEqual(saved_image.size, (32, 48))
            self.assertEqual(saved_image.getpixel((0, 0))[3], 0)
            self.assertEqual(saved_image.getpixel((31, 47))[3], 0)
            self.assertEqual(saved_image.getpixel((10, 10))[3], 255)

    def test_object_generation_removes_enclosed_green_screen_regions(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        reference_image_path = self._create_temp_image()

        generated_image = Image.new("RGBA", (64, 64), (149, 181, 128, 255))
        for x in range(16, 48):
            for y in range(24, 58):
                generated_image.putpixel((x, y), (240, 185, 208, 255))
        for x in range(22, 28):
            for y in range(10, 38):
                generated_image.putpixel((x, y), (28, 28, 28, 255))
        for x in range(36, 42):
            for y in range(10, 38):
                generated_image.putpixel((x, y), (28, 28, 28, 255))
        for x in range(22, 42):
            for y in range(10, 18):
                generated_image.putpixel((x, y), (28, 28, 28, 255))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "outputs"

            try:
                with patch.object(provider, "_generate_object_image", return_value=generated_image):
                    generated_assets = provider.generate_object_sprite(
                        reference_image_path=reference_image_path,
                        summary={"object_category": "shopping bag"},
                        target_size=64,
                        output_dir=output_dir,
                    )
            finally:
                reference_image_path.unlink(missing_ok=True)

            saved_image = Image.open(generated_assets[0].path).convert("RGBA")
            self.assertEqual(saved_image.getpixel((0, 0))[3], 0)
            self.assertEqual(saved_image.getpixel((32, 20))[3], 0)
            self.assertEqual(saved_image.getpixel((24, 22))[3], 255)

    def test_object_generation_despills_green_edges(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        reference_image_path = self._create_temp_image()

        generated_image = Image.new("RGBA", (32, 32), (149, 181, 128, 255))
        for x in range(8, 24):
            for y in range(8, 24):
                generated_image.putpixel((x, y), (245, 185, 207, 255))
        generated_image.putpixel((8, 16), (166, 195, 144, 255))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "outputs"

            try:
                with patch.object(provider, "_generate_object_image", return_value=generated_image):
                    generated_assets = provider.generate_object_sprite(
                        reference_image_path=reference_image_path,
                        summary={"object_category": "shopping bag"},
                        target_size=64,
                        output_dir=output_dir,
                    )
            finally:
                reference_image_path.unlink(missing_ok=True)

            saved_image = Image.open(generated_assets[0].path).convert("RGBA")
            red, green, blue, alpha = saved_image.getpixel((8, 16))
            self.assertEqual(alpha, 255)
            self.assertLessEqual(green, max(red, blue) + 8)

    def test_object_generation_removes_residual_green_corner_fragments(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        reference_image_path = self._create_temp_image()

        generated_image = Image.new("RGBA", (40, 40), (149, 181, 128, 255))
        for x in range(10, 30):
            for y in range(10, 32):
                generated_image.putpixel((x, y), (240, 185, 207, 255))
        for x in range(0, 3):
            for y in range(0, 3):
                generated_image.putpixel((x, y), (162, 190, 140, 255))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "outputs"

            try:
                with patch.object(provider, "_generate_object_image", return_value=generated_image):
                    generated_assets = provider.generate_object_sprite(
                        reference_image_path=reference_image_path,
                        summary={"object_category": "prop"},
                        target_size=64,
                        output_dir=output_dir,
                    )
            finally:
                reference_image_path.unlink(missing_ok=True)

            saved_image = Image.open(generated_assets[0].path).convert("RGBA")
            self.assertEqual(saved_image.getpixel((0, 0))[3], 0)
            self.assertEqual(saved_image.getpixel((1, 1))[3], 0)
            self.assertEqual(saved_image.getpixel((20, 20))[3], 255)

    def test_object_generation_removes_connected_green_shadow_regions(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        reference_image_path = self._create_temp_image()

        generated_image = Image.new("RGBA", (48, 48), (149, 181, 128, 255))
        for x in range(10, 28):
            for y in range(10, 34):
                generated_image.putpixel((x, y), (240, 185, 207, 255))
        for x in range(26, 40):
            for y in range(34, 42):
                generated_image.putpixel((x, y), (130, 160, 89, 255))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "outputs"

            try:
                with patch.object(provider, "_generate_object_image", return_value=generated_image):
                    generated_assets = provider.generate_object_sprite(
                        reference_image_path=reference_image_path,
                        summary={"object_category": "prop"},
                        target_size=64,
                        output_dir=output_dir,
                    )
            finally:
                reference_image_path.unlink(missing_ok=True)

            saved_image = Image.open(generated_assets[0].path).convert("RGBA")
            self.assertEqual(saved_image.getpixel((32, 38))[3], 0)
            self.assertEqual(saved_image.getpixel((18, 20))[3], 255)

    def test_object_generation_keeps_fully_opaque_image_when_gemini_returns_one(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        reference_image_path = self._create_temp_image()

        try:
            with patch.object(provider, "_generate_object_image", return_value=Image.new("RGBA", (32, 48), (255, 255, 255, 255))):
                generated_assets = provider.generate_object_sprite(
                    reference_image_path=reference_image_path,
                    summary={"object_category": "can"},
                    target_size=64,
                    output_dir=Path(tempfile.mkdtemp()) / "outputs",
                )
        finally:
            reference_image_path.unlink(missing_ok=True)

        self.assertEqual(len(generated_assets), 1)
        self.assertTrue(generated_assets[0].path.exists())

    def test_object_generation_preserves_transparent_asset_without_finalization(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")
        reference_image_path = self._create_temp_image()

        generated_image = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        for x in range(28, 68):
            for y in range(24, 80):
                generated_image.putpixel((x, y), (246, 182, 210, 255))
        for x in range(34, 42):
            for y in range(10, 36):
                generated_image.putpixel((x, y), (24, 24, 24, 255))
        for x in range(54, 62):
            for y in range(10, 36):
                generated_image.putpixel((x, y), (24, 24, 24, 255))
        for x in range(34, 62):
            for y in range(10, 18):
                if (x - 48) ** 2 + (y - 18) ** 2 >= 190:
                    continue
                generated_image.putpixel((x, y), (24, 24, 24, 255))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "outputs"

            try:
                with patch.object(provider, "_generate_object_image", return_value=generated_image):
                    generated_assets = provider.generate_object_sprite(
                        reference_image_path=reference_image_path,
                        summary={"object_category": "shopping bag", "main_shape": "tall boxy bag"},
                        target_size=64,
                        output_dir=output_dir,
                    )
            finally:
                reference_image_path.unlink(missing_ok=True)

            saved_image = Image.open(generated_assets[0].path).convert("RGBA")
            self.assertEqual(saved_image.size, (96, 96))
            self.assertEqual(saved_image.getpixel((0, 0))[3], 0)
            self.assertEqual(saved_image.getpixel((95, 95))[3], 0)
            self.assertEqual(saved_image.getpixel((32, 44))[3], 255)

    def test_object_generation_prompt_uses_generic_template_with_summary_fields(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")

        prompt = provider._build_object_generation_prompt(
            {
                "object_category": "shopping bag",
                "main_shape": "tall rectangular shopping bag with black handles",
                "material_cues": "paper bag body with attached top handles",
                "palette_notes": "pink body, black handles",
                "silhouette_notes": "upright front-facing bag silhouette",
                "key_identifying_features": "two black handles and a central front symbol",
            }
        )

        self.assertIn("Reference summary:", prompt)
        self.assertIn("Highest priority:", prompt)
        self.assertIn("the output must read immediately as pixel art first", prompt)
        self.assertIn("choose the more sprite-like pixel art interpretation", prompt)
        self.assertIn("object category: shopping bag", prompt)
        self.assertIn("dominant colors: pink body, black handles", prompt)
        self.assertIn("material cues: paper bag body with attached top handles", prompt)
        self.assertIn("key identifying features: two black handles and a central front symbol", prompt)
        self.assertIn("preserve readable negative space, holes, handles, and cutouts", prompt)
        self.assertIn("allow slight dimensional form only when it improves readability at sprite size", prompt)
        self.assertIn("studio green-screen background", prompt)
        self.assertIn("exact vivid chroma-key color #00FF00 (RGB 0,255,0)", prompt)
        self.assertIn("every background pixel outside the object must be that exact #00FF00 color", prompt)
        self.assertIn("will be removed in post-processing", prompt)
        self.assertIn("do not use that green on the object itself, in edge anti-aliasing, in reflections, in shadows, or in color spill", prompt)
        self.assertIn("true pixel art, not a painted cutout or product render", prompt)
        self.assertIn("tiny branding text, repeated printed words, micro labels, and fine typography as optional details", prompt)
        self.assertIn("simplify secondary surface graphics, side-panel copy, dense packaging text", prompt)

    def test_object_generation_prompt_sanitizes_branding_heavy_features(self) -> None:
        provider = GeminiImageProvider(api_key="test-key", model_name="gemini-2.5-flash", image_model_name="gemini-2.5-flash-image")

        prompt = provider._build_object_generation_prompt(
            {
                "object_category": "Branded shopping bag",
                "main_shape": "tall rectangular shopping bag with black handles",
                "material_cues": "paper bag body with attached top handles",
                "palette_notes": "pink body, black handles",
                "silhouette_notes": "upright front-facing bag silhouette",
                "key_identifying_features": "large brand text, repeated printed words on straps, two black handles",
            }
        )

        self.assertIn("object category: shopping bag", prompt)
        self.assertIn("key identifying features: two black handles", prompt)
        self.assertNotIn("repeated printed words on straps", prompt)
        self.assertIn("hard exact chroma-key green screen color", prompt)

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
