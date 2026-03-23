import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from app.services.providers.mock import MockImageProvider


class MockImageProviderClassificationTests(unittest.TestCase):
    def test_shopping_bag_is_classified_as_object(self) -> None:
        provider = MockImageProvider()

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "pink_shopping_bag.png"
            self._create_transparent_shopping_bag_image(image_path)

            classification = provider.classify_reference(image_path)

        self.assertEqual(classification, "object")

    def test_object_generation_isolates_subject_on_transparent_canvas(self) -> None:
        provider = MockImageProvider()

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "shopping_bag_product.jpg"
            output_dir = Path(temp_dir) / "outputs"
            self._create_bag_on_white_background(image_path)

            generated_assets = provider.generate_object_sprite(
                reference_image_path=image_path,
                summary={},
                target_size=64,
                output_dir=output_dir,
            )

            self.assertEqual(len(generated_assets), 1)

            generated_image = Image.open(generated_assets[0].path).convert("RGBA")
            self.assertEqual(generated_image.size, (64, 64))
            self.assertEqual(generated_image.getpixel((0, 0))[3], 0)
            self.assertEqual(generated_image.getpixel((63, 63))[3], 0)
            self.assertGreater(generated_image.getchannel("A").getbbox()[2], 0)

    def _create_transparent_shopping_bag_image(self, image_path: Path) -> None:
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        draw.rounded_rectangle((14, 18, 50, 54), radius=6, fill=(248, 140, 182, 255))
        draw.arc((20, 8, 44, 28), start=180, end=360, fill=(20, 20, 20, 255), width=4)
        image.save(image_path, format="PNG")

    def _create_bag_on_white_background(self, image_path: Path) -> None:
        image = Image.new("RGB", (120, 120), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        draw.rounded_rectangle((38, 30, 82, 88), radius=8, fill=(248, 140, 182))
        draw.arc((45, 18, 75, 48), start=180, end=360, fill=(20, 20, 20), width=5)
        draw.text((32, 52), "SHOP", fill=(40, 40, 40))
        image.save(image_path, format="JPEG")


if __name__ == "__main__":
    unittest.main()
