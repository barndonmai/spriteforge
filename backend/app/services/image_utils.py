from collections import Counter
from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


def normalize_to_canvas(source_image: Image.Image, target_size: int) -> Image.Image:
    image = source_image.convert("RGBA")
    working_image = trim_transparent_bounds(image)
    working_image.thumbnail((target_size, target_size), Image.Resampling.NEAREST)

    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    offset_x = (target_size - working_image.width) // 2
    offset_y = (target_size - working_image.height) // 2
    canvas.alpha_composite(working_image, (offset_x, offset_y))
    return canvas


def normalize_sprite_to_canvas(source_image: Image.Image, target_size: int, *, fill_ratio: float = 0.82) -> Image.Image:
    image = source_image.convert("RGBA")
    working_image = trim_transparent_bounds(image)

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
        cleared_background = make_border_background_transparent(image)
        cleared_box = cleared_background.getchannel("A").getbbox()
        if not cleared_box:
            return image
        return cleared_background.crop(_expand_bbox(cleared_box, cleared_background.size, padding=2))

    isolated = image.copy()
    isolated.putalpha(refined_subject_mask)
    isolated = make_border_background_transparent(isolated)
    return isolated.crop(_expand_bbox(subject_box, image.size, padding=2))


def prepare_object_sprite_asset(source_image: Image.Image, target_size: int) -> Image.Image:
    return normalize_sprite_to_canvas(source_image.convert("RGBA"), target_size, fill_ratio=0.9)


def save_png(image: Image.Image, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(destination, format="PNG")


def remove_chroma_green_background(source_image: Image.Image) -> Image.Image:
    image = source_image.convert("RGBA")
    background_key = _estimate_green_screen_key(image)
    if background_key is None:
        return image

    output = image.copy()
    pixels = output.load()
    width, height = output.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue

            similarity = _green_screen_similarity((red, green, blue), background_key)
            if similarity >= 0.92:
                pixels[x, y] = (red, green, blue, 0)
                continue

            if similarity >= 0.72:
                fade = max(0.0, min(1.0, (0.92 - similarity) / 0.20))
                pixels[x, y] = (red, green, blue, int(alpha * fade))

    output = despill_green_edges(output, background_key)
    output = remove_residual_green_fragments(output, background_key)
    return remove_connected_green_regions(output, background_key)


def despill_green_edges(source_image: Image.Image, key_color: tuple[int, int, int]) -> Image.Image:
    image = source_image.convert("RGBA")
    output = image.copy()
    pixels = output.load()
    width, height = output.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue

            similarity = _green_screen_similarity((red, green, blue), key_color)
            if similarity < 0.35:
                continue
            touches_transparent = _touches_transparent_pixel(output, x, y)
            if alpha == 255 and not touches_transparent:
                continue

            capped_green = min(green, max(red, blue) + 8)
            if alpha < 255 or touches_transparent:
                adjusted_green = capped_green
            else:
                strength = min(1.0, max(0.0, (similarity - 0.35) / 0.45))
                adjusted_green = int(green + ((capped_green - green) * strength))
            pixels[x, y] = (red, adjusted_green, blue, alpha)

    return output


def remove_residual_green_fragments(source_image: Image.Image, key_color: tuple[int, int, int]) -> Image.Image:
    image = source_image.convert("RGBA")
    output = image.copy()
    pixels = output.load()
    width, height = output.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue

            similarity = _green_screen_similarity((red, green, blue), key_color)
            if similarity < 0.28:
                continue

            touches_transparent = _touches_transparent_pixel(output, x, y)
            touches_edge = _touches_image_edge(x, y, width, height)
            if touches_edge and similarity >= 0.22:
                pixels[x, y] = (red, green, blue, 0)
                continue

            if touches_transparent and similarity >= 0.34:
                pixels[x, y] = (red, green, blue, 0)
                continue

            if alpha < 224 and similarity >= 0.28:
                pixels[x, y] = (red, green, blue, 0)

    return output


def remove_connected_green_regions(source_image: Image.Image, key_color: tuple[int, int, int]) -> Image.Image:
    image = source_image.convert("RGBA")
    width, height = image.size
    visited: set[tuple[int, int]] = set()
    output = image.copy()
    output_pixels = output.load()

    for y in range(height):
        for x in range(width):
            if (x, y) in visited:
                continue

            red, green, blue, alpha = image.getpixel((x, y))
            if alpha == 0:
                continue

            similarity = _green_screen_similarity((red, green, blue), key_color)
            if similarity < 0.18:
                continue

            component: list[tuple[int, int]] = []
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited.add((x, y))
            touches_transparent = False
            touches_edge = False
            max_similarity = similarity

            while queue:
                current_x, current_y = queue.popleft()
                component.append((current_x, current_y))
                current_red, current_green, current_blue, current_alpha = image.getpixel((current_x, current_y))
                max_similarity = max(
                    max_similarity,
                    _green_screen_similarity((current_red, current_green, current_blue), key_color),
                )

                if _touches_image_edge(current_x, current_y, width, height):
                    touches_edge = True

                for neighbor_x, neighbor_y in _neighbors(current_x, current_y, width, height):
                    neighbor_red, neighbor_green, neighbor_blue, neighbor_alpha = image.getpixel((neighbor_x, neighbor_y))
                    if neighbor_alpha == 0:
                        touches_transparent = True
                        continue

                    if (neighbor_x, neighbor_y) in visited:
                        continue

                    neighbor_similarity = _green_screen_similarity((neighbor_red, neighbor_green, neighbor_blue), key_color)
                    if neighbor_similarity < 0.18:
                        continue

                    visited.add((neighbor_x, neighbor_y))
                    queue.append((neighbor_x, neighbor_y))

            if not ((touches_transparent or touches_edge) and max_similarity >= 0.28):
                continue

            for component_x, component_y in component:
                red, green, blue, _ = output_pixels[component_x, component_y]
                output_pixels[component_x, component_y] = (red, green, blue, 0)

    return output


def trim_transparent_bounds(source_image: Image.Image) -> Image.Image:
    image = source_image.convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    if not alpha_box:
        return image
    return image.crop(alpha_box)


def has_real_transparency(source_image: Image.Image) -> bool:
    alpha = source_image.convert("RGBA").getchannel("A")
    minimum_alpha, _ = alpha.getextrema()
    return minimum_alpha < 255


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


def simplify_sprite_colors(image: Image.Image, max_colors: int = 24, blur_radius: float = 0.0) -> Image.Image:
    rgba_image = image.convert("RGBA")
    alpha = rgba_image.getchannel("A")
    opaque_rgb = Image.new("RGB", rgba_image.size, (0, 0, 0))
    opaque_rgb.paste(rgba_image.convert("RGB"), mask=alpha)
    if blur_radius > 0:
        opaque_rgb = opaque_rgb.filter(ImageFilter.GaussianBlur(radius=blur_radius))
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


def make_border_background_transparent(source_image: Image.Image) -> Image.Image:
    image = source_image.convert("RGBA")
    background_color = _estimate_background_color(image)
    background_mask = _build_background_mask(image, background_color)
    if not background_mask.getbbox():
        return image

    output = image.copy()
    alpha = output.getchannel("A")
    width, height = output.size

    for y in range(height):
        for x in range(width):
            if background_mask.getpixel((x, y)) > 0:
                alpha.putpixel((x, y), 0)

    output.putalpha(alpha)
    return output


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


def _estimate_green_screen_key(image: Image.Image) -> tuple[int, int, int] | None:
    width, height = image.size
    border_pixels: list[tuple[int, int, int]] = []

    for x in range(width):
        border_pixels.append(image.getpixel((x, 0))[:3])
        border_pixels.append(image.getpixel((x, height - 1))[:3])

    for y in range(1, height - 1):
        border_pixels.append(image.getpixel((0, y))[:3])
        border_pixels.append(image.getpixel((width - 1, y))[:3])

    green_pixels = [pixel for pixel in border_pixels if _is_green_dominant(pixel)]
    if len(green_pixels) < max(8, len(border_pixels) // 12):
        return None

    count = len(green_pixels)
    red = sum(pixel[0] for pixel in green_pixels) // count
    green = sum(pixel[1] for pixel in green_pixels) // count
    blue = sum(pixel[2] for pixel in green_pixels) // count
    return (red, green, blue)


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


def _build_green_screen_mask(image: Image.Image, key_color: tuple[int, int, int]) -> Image.Image:
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
        if not _is_green_screen_like(pixel, key_color):
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
                if _is_green_screen_like(neighbor_pixel, key_color):
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


def _is_green_dominant(color: tuple[int, int, int]) -> bool:
    red, green, blue = color
    return green >= 110 and green - max(red, blue) >= 18


def _is_green_screen_like(pixel: tuple[int, int, int, int], key_color: tuple[int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    if alpha < 20:
        return True

    return _green_screen_similarity((red, green, blue), key_color) >= 0.72


def _green_screen_similarity(color: tuple[int, int, int], key_color: tuple[int, int, int]) -> float:
    red, green, blue = color
    if not _is_green_dominant((red, green, blue)):
        return 0.0

    color_distance = abs(red - key_color[0]) + abs(green - key_color[1]) + abs(blue - key_color[2])
    return max(0.0, 1.0 - (color_distance / 120.0))


def _touches_transparent_pixel(image: Image.Image, x: int, y: int) -> bool:
    width, height = image.size
    for neighbor_x, neighbor_y in _neighbors(x, y, width, height):
        if image.getpixel((neighbor_x, neighbor_y))[3] == 0:
            return True
    return False


def _touches_image_edge(x: int, y: int, width: int, height: int) -> bool:
    return x <= 1 or y <= 1 or x >= width - 2 or y >= height - 2


def _quantize_rgb(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple((channel // 16) * 16 for channel in color)


def _expand_bbox(bbox: tuple[int, int, int, int], image_size: tuple[int, int], padding: int) -> tuple[int, int, int, int]:
    width, height = image_size
    left = max(0, bbox[0] - padding)
    upper = max(0, bbox[1] - padding)
    right = min(width, bbox[2] + padding)
    lower = min(height, bbox[3] + padding)
    return (left, upper, right, lower)
