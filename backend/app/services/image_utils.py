from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageEnhance, ImageFont, ImageOps


def normalize_to_canvas(source_image: Image.Image, target_size: int) -> Image.Image:
    image = source_image.convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    working_image = image.crop(alpha_box) if alpha_box else image
    working_image.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    offset_x = (target_size - working_image.width) // 2
    offset_y = (target_size - working_image.height) // 2
    canvas.alpha_composite(working_image, (offset_x, offset_y))
    return canvas


def save_png(image: Image.Image, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG")


def build_palette_notes(image: Image.Image, max_colors: int = 4) -> str:
    rgba_image = image.convert("RGBA").resize((32, 32))
    opaque_pixels = [
        (r, g, b)
        for r, g, b, a in rgba_image.getdata()
        if a > 32
    ]
    if not opaque_pixels:
        return "mostly transparent or low-detail reference palette"

    color_counts = Counter(opaque_pixels)
    dominant_colors = [rgb_to_hex(color) for color, _ in color_counts.most_common(max_colors)]
    return ", ".join(dominant_colors)


def build_silhouette_notes(image: Image.Image) -> str:
    alpha = image.convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return "reference has minimal opaque silhouette information"

    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    aspect_ratio = width / max(height, 1)

    if aspect_ratio < 0.7:
        shape = "tall and narrow"
    elif aspect_ratio > 1.3:
        shape = "wide and horizontal"
    else:
        shape = "balanced"

    coverage = (width * height) / max(image.width * image.height, 1)
    return f"{shape} silhouette with roughly {coverage:.0%} occupied canvas area"


def apply_direction_badge(image: Image.Image, badge_text: str, badge_color: str) -> Image.Image:
    output = image.copy()
    draw = ImageDraw.Draw(output)
    font = ImageFont.load_default()

    badge_width = max(18, len(badge_text) * 7)
    badge_height = 12
    badge_box = (4, 4, 4 + badge_width, 4 + badge_height)
    fill_color = ImageColor.getrgb(badge_color) + (210,)

    draw.rounded_rectangle(badge_box, radius=3, fill=fill_color)
    draw.text((7, 6), badge_text, fill=(255, 255, 255, 255), font=font)
    return output


def mirror_image(image: Image.Image) -> Image.Image:
    return ImageOps.mirror(image)


def tint_image(image: Image.Image, amount: float) -> Image.Image:
    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(amount)


def darken_image(image: Image.Image, amount: float) -> Image.Image:
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(amount)


def rgb_to_hex(color: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*color)

