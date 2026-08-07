from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


def detect_language(text: str) -> str:
    """
    텍스트의 언어를 감지한다.

    반환 예시:
    ko, en, ja, zh-cn ...
    """

    if not text.strip():
        return "unknown"

    try:
        return detect(text)

    except LangDetectException:
        return "unknown"