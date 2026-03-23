import re
from typing import Any


def build_classification_prompt(notes: str | None) -> str:
    note_text = _normalize_note_text(notes)
    return (
        "You are classifying a reference image for a 2D game asset workflow. "
        "Return 'character' only when the image strongly represents a person, humanoid, or character design. "
        "Return 'object' for props, items, products, bags, tools, packaging, signs, weapons, and ambiguous non-human subjects. "
        f"User notes: {note_text}"
    )


def build_character_summary_prompt(notes: str | None) -> str:
    note_text = _normalize_note_text(notes)
    return (
        "Summarize this image as a game-ready character reference. "
        "Keep each field concise and practical for sprite generation. "
        "Focus only on visible or strongly implied traits. "
        f"User notes: {note_text}"
    )


def build_object_summary_prompt(notes: str | None) -> str:
    note_text = _normalize_note_text(notes)
    return (
        "Summarize this image as a game-ready object or prop reference. "
        "Keep each field concise and practical for sprite generation. "
        "Capture the main object category, overall shape, material cues, dominant colors, silhouette notes, and key identifying features. "
        "Focus only on visible or strongly implied traits. "
        f"User notes: {note_text}"
    )


def build_object_generation_prompt(summary: dict[str, Any]) -> str:
    category = sanitize_object_category(summary.get("object_category", "object"))
    shape = summary.get("main_shape", "overall silhouette from the reference image")
    palette = summary.get("palette_notes", "major colors from the reference image")
    material_cues = summary.get("material_cues", "surface and material cues from the reference image")
    silhouette_notes = summary.get("silhouette_notes", "clean front-facing object silhouette")
    key_features = sanitize_key_identifying_features(
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
        "- allow slight dimensional form only when it improves readability at sprite size\n"
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
        "- avoid perspective tilt; prefer a straight-on, sprite-like view when possible"
    )


def sanitize_object_category(category: Any) -> str:
    normalized = str(category).strip() or "object"
    for prefix in ("branded ", "logo ", "packaged ", "product "):
        if normalized.lower().startswith(prefix):
            return normalized[len(prefix):]
    return normalized


def sanitize_key_identifying_features(key_features: Any) -> str:
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


def _normalize_note_text(notes: str | None) -> str:
    if not notes:
        return "No user notes provided."
    return notes.strip()
