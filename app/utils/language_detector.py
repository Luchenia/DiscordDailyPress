from ftlangdetect import detect


def detect_language(text: str) -> str:
    """
    텍스트의 언어를 감지한다.

    반환 예시:
    ko, en, ja, zh ...
    """

    if not text.strip():
        return "unknown"

    try:
        result = detect(
            text=text,
            low_memory=True,
        )

        return result["lang"]

    except (ValueError, KeyError):
        return "unknown"