from app.bot.bot import ChronicleBot
from app.core.bootstrap import bootstrap
from app.core.config import config
from app.services.fallback_translation_provider import FallbackTranslationProvider
from app.services.gemini_translation_provider import GeminiTranslationProvider
from app.services.nvidia_translation_provider import NvidiaTranslationProvider


def main():
    bootstrap()

    translation_providers = []
    if config.gemini_api_key.strip():
        translation_providers.append(
            GeminiTranslationProvider(
                api_key=config.gemini_api_key,
                model=config.gemini_translation_model,
            )
        )
    if config.nvidia_api_key.strip():
        translation_providers.append(
            NvidiaTranslationProvider(
                api_key=config.nvidia_api_key,
                model=config.nvidia_translation_model,
            )
        )

    translation_provider = (
        FallbackTranslationProvider(translation_providers)
        if translation_providers
        else None
    )

    bot = ChronicleBot(
        translation_provider=translation_provider,
    )

    bot.run(config.discord_bot_token)


if __name__ == "__main__":
    main()
