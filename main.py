from app.bot.bot import ChronicleBot
from app.core.bootstrap import bootstrap
from app.core.config import config
from app.services.gemini_translation_provider import GeminiTranslationProvider


def main():
    bootstrap()

    translation_provider = None
    if config.gemini_api_key.strip():
        translation_provider = GeminiTranslationProvider(
            api_key=config.gemini_api_key,
            model=config.gemini_translation_model,
        )

    bot = ChronicleBot(
        translation_provider=translation_provider,
    )

    bot.run(config.discord_bot_token)


if __name__ == "__main__":
    main()
