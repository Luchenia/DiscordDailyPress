import httpx

from app.services.translation_provider import TranslationProviderError


SUPPORTED_LANGUAGE_CODES = frozenset({
    "en",
    "cs",
    "da",
    "de",
    "el",
    "es-ES",
    "es-US",
    "fi",
    "fr",
    "hu",
    "it",
    "lt",
    "lv",
    "nl",
    "no",
    "pl",
    "pt-PT",
    "pt-BR",
    "ro",
    "ru",
    "sk",
    "sv",
    "zh-CN",
    "zh-TW",
    "ja",
    "hi",
    "ko",
    "et",
    "sl",
    "bg",
    "uk",
    "hr",
    "ar",
    "vi",
    "tr",
    "id",
    "th",
})
CANONICAL_LANGUAGE_CODES = {
    language.casefold(): language
    for language in SUPPORTED_LANGUAGE_CODES
}


class NvidiaTranslationProvider:
    ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
    DEFAULT_MODEL = "nvidia/riva-translate-4b-instruct-v2"
    DEFAULT_TIMEOUT_SECONDS = 30

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        if not text.strip():
            return ""

        source_code = source_language.strip()
        target_code = target_language.strip()
        if source_code.casefold() == "unknown":
            raise TranslationProviderError(
                "NVIDIA translation requires a known source language",
                retryable=False,
            )

        source_code = self._canonical_language_code(source_code, "source")
        target_code = self._canonical_language_code(target_code, "target")
        if source_code == target_code:
            return text

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": f"{source_code}-{target_code}",
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
            "temperature": 0,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.ENDPOINT,
                    headers=headers,
                    json=payload,
                )
        except httpx.TimeoutException as error:
            raise TranslationProviderError(
                "NVIDIA translation request timed out",
                retryable=True,
            ) from error
        except httpx.TransportError as error:
            raise TranslationProviderError(
                "NVIDIA translation network request failed",
                retryable=True,
            ) from error

        if response.status_code != 200:
            raise TranslationProviderError(
                "NVIDIA translation API request failed",
                retryable=self._is_retryable_status(response.status_code),
                status_code=response.status_code,
            )

        try:
            response_data = response.json()
            translated_content = response_data["choices"][0]["message"]["content"]
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise TranslationProviderError(
                "NVIDIA returned a malformed translation response",
                retryable=False,
            ) from error

        if not isinstance(translated_content, str) or not translated_content.strip():
            raise TranslationProviderError(
                "NVIDIA returned an empty or malformed translation response",
                retryable=False,
            )
        return translated_content.strip()

    @staticmethod
    def _canonical_language_code(language: str, role: str) -> str:
        canonical = CANONICAL_LANGUAGE_CODES.get(language.casefold())
        if canonical is None:
            raise TranslationProviderError(
                f"NVIDIA does not support the requested {role} language",
                retryable=False,
            )
        return canonical

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return (
            status_code in {202, 408, 429}
            or 500 <= status_code < 600
        )
