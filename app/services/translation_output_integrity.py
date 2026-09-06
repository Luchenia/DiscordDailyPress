import re
import unicodedata
from collections import Counter

from app.services.translation_provider import TranslationProviderError


class TranslationIntegrityError(TranslationProviderError):
    def __init__(self, violations: list[str]):
        self.violations = tuple(violations)
        super().__init__(
            "Translation output failed integrity validation: "
            + ", ".join(self.violations),
            retryable=False,
        )


class TranslationOutputIntegrityValidator:
    """Validate exact Discord tokens and code before a translation is persisted."""

    _mention_pattern = re.compile(
        r"<(?:@!?|@&|#)\d+>|@(?:everyone|here)(?![A-Za-z0-9_])"
    )
    _custom_emoji_pattern = re.compile(r"<a?:[A-Za-z0-9_]+:\d+>")
    _url_pattern = re.compile(
        r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+"
    )
    _emoji_base_pattern = (
        r"[\u00A9\u00AE\u203C\u2049\u2122\u2139\u2194-\u2199"
        r"\u21A9\u21AA\u231A\u231B\u2328\u23CF\u23E9-\u23F3"
        r"\u23F8-\u23FA\u24C2\u25AA\u25AB\u25B6\u25C0"
        r"\u25FB-\u25FE\u2600-\u27BF\u2934\u2935\u2B05-\u2B07"
        r"\u2B1B\u2B1C\u2B50\u2B55\u3030\u303D\u3297\u3299"
        r"\U0001F000-\U0001F1E5\U0001F200-\U0001F3FA"
        r"\U0001F400-\U0001FAFF]"
    )
    _emoji_pattern = re.compile(
        r"(?:[\U0001F1E6-\U0001F1FF]{2}|[#*0-9]\ufe0f?\u20e3|"
        + _emoji_base_pattern
        + r"\ufe0f?[\U0001F3FB-\U0001F3FF]?(?:\u200d"
        + _emoji_base_pattern
        + r"\ufe0f?[\U0001F3FB-\U0001F3FF]?)*"
        + r"(?:[\U000E0020-\U000E007E]+\U000E007F)?"
        + r")"
    )
    _fenced_code_pattern = re.compile(r"```.*?```", re.DOTALL)
    _inline_code_pattern = re.compile(r"(?<!`)`[^`\n]+`(?!`)")
    _italic_asterisk_pattern = re.compile(
        r"(?<!\*)\*(?![\s*])[^*\n]*?(?<![\s*])\*(?!\*)"
    )
    _italic_underscore_pattern = re.compile(
        r"(?<![A-Za-z0-9_])_(?![\s_])[^_\n]*?"
        r"(?<![\s_])_(?![A-Za-z0-9_])"
    )
    _markdown_delimiters = ("***", "___", "**", "__", "~~", "||")

    def validate(self, source_text: str, translated_text: str) -> None:
        violations: list[str] = []

        if not isinstance(translated_text, str):
            raise TranslationIntegrityError(["non-string output"])

        if not source_text.strip():
            if translated_text.strip():
                raise TranslationIntegrityError(["empty source changed"])
            return

        if not translated_text.strip():
            raise TranslationIntegrityError(["empty output"])

        self._compare_pattern(
            "Discord mentions",
            self._mention_pattern,
            source_text,
            translated_text,
            violations,
        )
        self._compare_pattern(
            "custom emoji",
            self._custom_emoji_pattern,
            source_text,
            translated_text,
            violations,
        )
        self._compare_urls(source_text, translated_text, violations)
        self._compare_symbols(source_text, translated_text, violations)
        self._compare_code(source_text, translated_text, violations)
        self._compare_markdown(source_text, translated_text, violations)

        if violations:
            raise TranslationIntegrityError(violations)

    @staticmethod
    def _compare_pattern(
        label: str,
        pattern: re.Pattern[str],
        source_text: str,
        translated_text: str,
        violations: list[str],
    ) -> None:
        if Counter(pattern.findall(source_text)) != Counter(
            pattern.findall(translated_text)
        ):
            violations.append(label)

    @classmethod
    def _compare_urls(
        cls,
        source_text: str,
        translated_text: str,
        violations: list[str],
    ) -> None:
        if Counter(cls._extract_urls(source_text)) != Counter(
            cls._extract_urls(translated_text)
        ):
            violations.append("URLs")

    @classmethod
    def _extract_urls(cls, text: str) -> list[str]:
        urls = []
        for match in cls._url_pattern.finditer(text):
            url = match.group().rstrip(".,!?;:")
            while url.endswith(")") and url.count(")") > url.count("("):
                url = url[:-1]
            urls.append(url)
        return urls

    @staticmethod
    def _compare_symbols(
        source_text: str,
        translated_text: str,
        violations: list[str],
    ) -> None:
        def protected_tokens(text: str) -> tuple[Counter[str], Counter[str]]:
            emoji = Counter(
                TranslationOutputIntegrityValidator._emoji_pattern.findall(text)
            )
            without_emoji = TranslationOutputIntegrityValidator._emoji_pattern.sub(
                "", text
            )
            symbols = Counter(
                character
                for character in without_emoji
                if unicodedata.category(character) in {"So", "Sk"}
                or character in {"\u200d", "\ufe0f"}
            )
            return emoji, symbols

        if protected_tokens(source_text) != protected_tokens(translated_text):
            violations.append("Unicode emoji or symbols")

    @classmethod
    def _compare_code(
        cls,
        source_text: str,
        translated_text: str,
        violations: list[str],
    ) -> None:
        source_fenced = cls._fenced_code_pattern.findall(source_text)
        translated_fenced = cls._fenced_code_pattern.findall(translated_text)
        if Counter(source_fenced) != Counter(translated_fenced):
            violations.append("fenced code")

        source_without_fenced = cls._fenced_code_pattern.sub("", source_text)
        translated_without_fenced = cls._fenced_code_pattern.sub("", translated_text)
        source_inline = cls._inline_code_pattern.findall(source_without_fenced)
        translated_inline = cls._inline_code_pattern.findall(translated_without_fenced)
        if Counter(source_inline) != Counter(translated_inline):
            violations.append("inline code")

        if source_text.count("```") != translated_text.count("```"):
            if "fenced code" not in violations:
                violations.append("fenced code")

    @classmethod
    def _compare_markdown(
        cls,
        source_text: str,
        translated_text: str,
        violations: list[str],
    ) -> None:
        source_without_code = cls._remove_code(source_text)
        translated_without_code = cls._remove_code(translated_text)
        source_counts = {
            delimiter: source_without_code.count(delimiter)
            for delimiter in cls._markdown_delimiters
        }
        translated_counts = {
            delimiter: translated_without_code.count(delimiter)
            for delimiter in cls._markdown_delimiters
        }
        source_italics = (
            len(cls._italic_asterisk_pattern.findall(source_without_code)),
            len(cls._italic_underscore_pattern.findall(source_without_code)),
        )
        translated_italics = (
            len(cls._italic_asterisk_pattern.findall(translated_without_code)),
            len(cls._italic_underscore_pattern.findall(translated_without_code)),
        )
        if source_counts != translated_counts or source_italics != translated_italics:
            violations.append("Markdown delimiters")

    @classmethod
    def _remove_code(cls, text: str) -> str:
        without_fenced = cls._fenced_code_pattern.sub("", text)
        return cls._inline_code_pattern.sub("", without_fenced)
