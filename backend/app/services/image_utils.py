from collections import Counter
from collections import deque
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


def normalize_sprite_to_canvas(source_image: Image.Image, target_size: int, *, fill_ratio: float = 0.82) -> Image.Image:
    image = source_image.convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    working_image = image.crop(alpha_box) if alpha_box else image

    max_dimension = max(1, int(target_size * fill_ratio))
    working_image.thumbnail((max_dimension, max_dimension), Image.Resampling.NEAREST)

    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    offset_x = (target_size - working_image.width) // 2
    offset_y = (target_size - working_image.height) // 2
    canvas.alpha_composite(working_image, (offset_x, offset_y))
    return canvas


def isolate_main_subject(source_image: Image.Image) -> Image.Image:
    image = source_image.convert("RGBA")
    alpha = image.getchannel("A")
    alpha_box = alpha.getbbox()

    # If the upload already has transparency, trust it and just tighten the crop.
    if alpha_box and _has_transparent_pixels(alpha):
        return image.crop(_expand_bbox(alpha_box, image.size, padding=2))

    background_color = _estimate_background_color(image)
    background_mask = _build_background_mask(image, background_color)
    subject_mask = _invert_binary_mask(background_mask)
    refined_subject_mask = _keep_primary_subject(subject_mask)
    subject_box = refined_subject_mask.getbbox()

    if not subject_box:
        return image

    isolated = image.copy()
    isolated.putalpha(refined_subject_mask)
    return isolated.crop(_expand_bbox(subject_box, image.size, padding=2))


def prepare_object_sprite_asset(source_image: Image.Image, target_size: int) -> Image.Image:
    isolated_subject = isolate_main_subject(source_image)
    cleaned_subject = remove_small_alpha_islands(isolated_subject, min_component_size=max(12, target_size // 3))
    simplified_subject = simplify_sprite_colors(cleaned_subject, max_colors=24)
    return normalize_sprite_to_canvas(simplified_subject, target_size, fill_ratio=0.8)


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


def simplify_sprite_colors(image: Image.Image, max_colors: int = 24) -> Image.Image:
    rgba_image = image.convert("RGBA")
    alpha = rgba_image.getchannel("A")
    opaque_rgb = Image.new("RGB", rgba_image.size, (0, 0, 0))
    opaque_rgb.paste(rgba_image.convert("RGB"), mask=alpha)
    quantized = opaque_rgb.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    quantized.putalpha(alpha)
    return quantized


def remove_small_alpha_islands(image: Image.Image, min_component_size: int = 16) -> Image.Image:
    rgba_image = image.convert("RGBA")
    alpha = rgba_image.getchannel("A")
    cleaned_alpha = _filter_small_components(alpha, min_component_size=min_component_size)
    output = rgba_image.copy()
    output.putalpha(cleaned_alpha)

    cleaned_bbox = cleaned_alpha.getbbox()
    if not cleaned_bbox:
        return output
    return output.crop(_expand_bbox(cleaned_bbox, output.size, padding=1))


def _has_transparent_pixels(alpha: Image.Image) -> bool:
    extrema = alpha.getextrema()
    return extrema[0] < 255


def _estimate_background_color(image: Image.Image) -> tuple[int, int, int]:
    width, height = image.size
    border_pixels: list[tuple[int, int, int]] = []

    for x in range(width):
        border_pixels.append(_quantize_rgb(image.getpixel((x, 0))[:3]))
        border_pixels.append(_quantize_rgb(image.getpixel((x, height - 1))[:3]))

    for y in range(1, height - 1):
        border_pixels.append(_quantize_rgb(image.getpixel((0, y))[:3]))
        border_pixels.append(_quantize_rgb(image.getpixel((width - 1, y))[:3]))

    if not border_pixels:
        return (255, 255, 255)

    return Counter(border_pixels).most_common(1)[0][0]


def _build_background_mask(image: Image.Image, background_color: tuple[int, int, int]) -> Image.Image:
    width, height = image.size
    mask = Image.new("L", (width, height), 0)
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    border_points = (
        [(x, 0) for x in range(width)]
        + [(x, height - 1) for x in range(width)]
        + [(0, y) for y in range(1, height - 1)]
        + [(width - 1, y) for y in range(1, height - 1)]
    )

    for point in border_points:
        if point in visited:
            continue

        pixel = image.getpixel(point)
        if not _is_background_like(pixel, background_color):
            continue

        queue.append(point)
        visited.add(point)

        while queue:
            current_x, current_y = queue.popleft()
            mask.putpixel((current_x, current_y), 255)

            for neighbor_x, neighbor_y in _neighbors(current_x, current_y, width, height):
                if (neighbor_x, neighbor_y) in visited:
                    continue

                visited.add((neighbor_x, neighbor_y))
                neighbor_pixel = image.getpixel((neighbor_x, neighbor_y))
                if _is_background_like(neighbor_pixel, background_color):
                    queue.append((neighbor_x, neighbor_y))

    return mask


def _invert_binary_mask(mask: Image.Image) -> Image.Image:
    inverted = Image.new("L", mask.size, 0)
    width, height = mask.size
    for y in range(height):
        for x in range(width):
            inverted.putpixel((x, y), 255 if mask.getpixel((x, y)) == 0 else 0)
    return inverted


def _filter_small_components(mask: Image.Image, min_component_size: int) -> Image.Image:
    width, height = mask.size
    visited: set[tuple[int, int]] = set()
    filtered_mask = Image.new("L", mask.size, 0)

    for y in range(height):
        for x in range(width):
            if mask.getpixel((x, y)) <= 0 or (x, y) in visited:
                continue

            component: list[tuple[int, int]] = []
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited.add((x, y))

            while queue:
                current_x, current_y = queue.popleft()
                component.append((current_x, current_y))

                for neighbor_x, neighbor_y in _neighbors(current_x, current_y, width, height):
                    if (neighbor_x, neighbor_y) in visited:
                        continue
                    if mask.getpixel((neighbor_x, neighbor_y)) <= 0:
                        continue
                    visited.add((neighbor_x, neighbor_y))
                    queue.append((neighbor_x, neighbor_y))

            if len(component) < min_component_size:
                continue

            for component_x, component_y in component:
                filtered_mask.putpixel((component_x, component_y), 255)

    return filtered_mask


def _keep_primary_subject(mask: Image.Image) -> Image.Image:
    width, height = mask.size
    visited: set[tuple[int, int]] = set()
    best_component: list[tuple[int, int]] = []
    best_score = float("-inf")
    center_x = width / 2
    center_y = height / 2

    for y in range(height):
        for x in range(width):
            if mask.getpixel((x, y)) == 0 or (x, y) in visited:
                continue

            component: list[tuple[int, int]] = []
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited.add((x, y))

            while queue:
                current_x, current_y = queue.popleft()
                component.append((current_x, current_y))

                for neighbor_x, neighbor_y in _neighbors(current_x, current_y, width, height):
                    if (neighbor_x, neighbor_y) in visited:
                        continue
                    if mask.getpixel((neighbor_x, neighbor_y)) == 0:
                        continue
                    visited.add((neighbor_x, neighbor_y))
                    queue.append((neighbor_x, neighbor_y))

            component_size = len(component)
            if component_size < 24:
                continue

            average_x = sum(pixel_x for pixel_x, _ in component) / component_size
            average_y = sum(pixel_y for _, pixel_y in component) / component_size
            center_distance = abs(center_x - average_x) + abs(center_y - average_y)
            score = component_size - (center_distance * 1.5)

            if score > best_score:
                best_score = score
                best_component = component

    if not best_component:
        return mask

    refined_mask = Image.new("L", mask.size, 0)
    for x, y in best_component:
        refined_mask.putpixel((x, y), 255)
    return refined_mask


def _neighbors(x: int, y: int, width: int, height: int) -> list[tuple[int, int]]:
    neighbors: list[tuple[int, int]] = []
    if x > 0:
        neighbors.append((x - 1, y))
    if x < width - 1:
        neighbors.append((x + 1, y))
    if y > 0:
        neighbors.append((x, y - 1))
    if y < height - 1:
        neighbors.append((x, y + 1))
    return neighbors


def _is_background_like(pixel: tuple[int, int, int, int], background_color: tuple[int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    if alpha < 20:
        return True

    color_distance = abs(red - background_color[0]) + abs(green - background_color[1]) + abs(blue - background_color[2])
    return color_distance <= 72


def _quantize_rgb(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple((channel // 16) * 16 for channel in color)


def _expand_bbox(bbox: tuple[int, int, int, int], image_size: tuple[int, int], padding: int) -> tuple[int, int, int, int]:
    width, height = image_size
    left = max(0, bbox[0] - padding)
    upper = max(0, bbox[1] - padding)
    right = min(width, bbox[2] + padding)
    lower = min(height, bbox[3] + padding)
    return (left, upper, right, lower)
