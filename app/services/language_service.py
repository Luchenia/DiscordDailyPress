from app.utils.language_detector import detect_language


class LanguageService:

    def detect(
        self,
        text: str,
    ) -> str:

        return detect_language(text)