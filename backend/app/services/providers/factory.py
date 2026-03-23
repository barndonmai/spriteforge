from app.core.config import get_settings
from app.services.providers.base import ImageProvider
from app.services.providers.gemini import GeminiImageProvider
from app.services.providers.mock import MockImageProvider


def get_image_provider() -> ImageProvider:
    settings = get_settings()

    if settings.provider == "mock":
        return MockImageProvider()
    if settings.provider == "gemini":
        return GeminiImageProvider(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
            image_model_name=settings.gemini_image_model,
        )

    raise ValueError(f"Unsupported SPRITEFORGE_PROVIDER: {settings.provider}")
