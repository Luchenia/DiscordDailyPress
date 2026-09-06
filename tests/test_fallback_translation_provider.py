import asyncio

import pytest

from app.services.fallback_translation_provider import FallbackTranslationProvider
from app.services.translation_output_integrity import (
    TranslationIntegrityError,
    TranslationOutputIntegrityValidator,
)
from app.services.translation_provider import TranslationProviderError


class FakeProvider:
    def __init__(self, result="translated", error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def translate(self, text, source_language, target_language):
        self.calls.append((text, source_language, target_language))
        if self.error is not None:
            raise self.error
        return self.result


def translate(provider, text="hello", source="en", target="ko"):
    return asyncio.run(provider.translate(text, source, target))


def test_requires_at_least_one_provider():
    with pytest.raises(ValueError):
        FallbackTranslationProvider([])


def test_primary_valid_result_does_not_call_fallback():
    primary = FakeProvider("번역")
    fallback = FakeProvider("다른 번역")
    provider = FallbackTranslationProvider([primary, fallback])

    assert translate(provider) == "번역"
    assert primary.calls == [("hello", "en", "ko")]
    assert fallback.calls == []


def test_provider_error_calls_each_fallback_once_in_order():
    first_error = TranslationProviderError("first failed", retryable=True)
    primary = FakeProvider(error=first_error)
    fallback = FakeProvider("번역")
    provider = FallbackTranslationProvider([primary, fallback])

    assert translate(provider) == "번역"
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1


@pytest.mark.parametrize(
    ("source", "invalid", "valid"),
    [
        (
            "Ping <@123> and <@&456> in <#789>.",
            "<@123>에게 알려 주세요.",
            "<@123>와 <@&456>에게 <#789>에서 알려 주세요.",
        ),
        (
            "See https://example.com/a?q=1 🚀",
            "https://example.com/other를 확인하세요.",
            "https://example.com/a?q=1에서 확인하세요 🚀",
        ),
        (
            "Run `git status --short` first.",
            "먼저 git status를 실행하세요.",
            "먼저 `git status --short`를 실행하세요.",
        ),
        (
            "**Fix:**\n```python\nprint(\"ready\")\n```\nKeep `API_KEY`.",
            "**수정:** 설정을 변경하세요.",
            "**수정:**\n```python\nprint(\"ready\")\n```\n`API_KEY`를 유지하세요.",
        ),
        (
            "Ship it <:party:123> 😭",
            "배포하세요 <:other:123>",
            "배포하세요 <:party:123> 😭",
        ),
        (
            "Tell @everyone and @here about the *quick fix*.",
            "모두에게 빠른 수정 사항을 알려 주세요.",
            "@everyone과 @here에게 *빠른 수정*을 알려 주세요.",
        ),
    ],
)
def test_integrity_failure_uses_fallback(source, invalid, valid):
    primary = FakeProvider(invalid)
    fallback = FakeProvider(valid)
    provider = FallbackTranslationProvider([primary, fallback])

    assert translate(provider, source) == valid
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1


@pytest.mark.parametrize("result", [None, "", "  \n"])
def test_invalid_result_uses_fallback(result):
    primary = FakeProvider(result)
    fallback = FakeProvider("번역")

    assert translate(FallbackTranslationProvider([primary, fallback])) == "번역"


def test_empty_source_returns_first_provider_empty_result():
    primary = FakeProvider("")
    fallback = FakeProvider("must not run")
    provider = FallbackTranslationProvider([primary, fallback])

    assert translate(provider, "  \n") == ""
    assert fallback.calls == []


def test_all_failures_raise_aggregate_retryability_without_another_attempt():
    primary = FakeProvider(
        error=TranslationProviderError("temporary", retryable=True)
    )
    fallback = FakeProvider("mention missing")
    provider = FallbackTranslationProvider([primary, fallback])

    with pytest.raises(TranslationProviderError) as raised:
        translate(provider, "ping <@123>")

    assert str(raised.value) == "All configured translation providers failed"
    assert raised.value.retryable is True
    assert raised.value.status_code is None
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1
    assert isinstance(raised.value.__cause__, TranslationIntegrityError)


def test_unexpected_exception_is_not_hidden_or_fallen_back():
    error = RuntimeError("programming error")
    primary = FakeProvider(error=error)
    fallback = FakeProvider("must not run")
    provider = FallbackTranslationProvider([primary, fallback])

    with pytest.raises(RuntimeError) as raised:
        translate(provider)

    assert raised.value is error
    assert fallback.calls == []


def test_validator_rejects_added_protected_content():
    validator = TranslationOutputIntegrityValidator()

    with pytest.raises(TranslationIntegrityError) as raised:
        validator.validate("hello", "번역 <@123> https://example.com `code` 🚀")

    assert set(raised.value.violations) == {
        "Discord mentions",
        "URLs",
        "Unicode emoji or symbols",
        "inline code",
    }


@pytest.mark.parametrize(
    ("source", "translated"),
    [
        ("Notify @everyone and @here.", "@everyone에게 알리세요."),
        ("Notify the team.", "@here에 알리세요."),
    ],
)
def test_validator_rejects_removed_or_added_mass_mentions(source, translated):
    validator = TranslationOutputIntegrityValidator()

    with pytest.raises(TranslationIntegrityError) as raised:
        validator.validate(source, translated)

    assert "Discord mentions" in raised.value.violations


def test_validator_allows_reordered_preserved_emoji():
    validator = TranslationOutputIntegrityValidator()

    validator.validate(
        "Start 👩‍💻 🚀 then finish 👨‍🔧 ✅",
        "완료 👨‍🔧 ✅ 후 시작 👩‍💻 🚀",
    )


@pytest.mark.parametrize(
    ("source", "translated"),
    [
        ("👩‍💻 👨‍🔧", "👩‍🔧 👨‍💻"),
        ("👍🏻 👎🏿", "👍🏿 👎🏻"),
    ],
)
def test_validator_rejects_recombined_emoji_sequences(source, translated):
    validator = TranslationOutputIntegrityValidator()

    with pytest.raises(TranslationIntegrityError) as raised:
        validator.validate(source, translated)

    assert "Unicode emoji or symbols" in raised.value.violations


@pytest.mark.parametrize(
    ("source", "translated"),
    [
        ("©️ ™", "© ™️"),
        (
            "Flag: \U0001F3F4\U000E0067\U000E0062\U000E0065"
            "\U000E006E\U000E0067\U000E007F",
            "Flag: 🏴",
        ),
    ],
)
def test_validator_rejects_changed_emoji_variants(source, translated):
    validator = TranslationOutputIntegrityValidator()

    with pytest.raises(TranslationIntegrityError) as raised:
        validator.validate(source, translated)

    assert "Unicode emoji or symbols" in raised.value.violations


@pytest.mark.parametrize(
    ("source", "translated"),
    [
        ("Use *quick fix* now.", "빠른 수정을 사용하세요."),
        ("Use the quick fix now.", "지금 *빠른 수정*을 사용하세요."),
        ("Be _very_ careful.", "아주 조심하세요."),
    ],
)
def test_validator_rejects_added_or_removed_italic_markdown(source, translated):
    validator = TranslationOutputIntegrityValidator()

    with pytest.raises(TranslationIntegrityError) as raised:
        validator.validate(source, translated)

    assert "Markdown delimiters" in raised.value.violations


def test_validator_allows_translated_italic_markdown():
    validator = TranslationOutputIntegrityValidator()

    validator.validate(
        "Use *quick fix* and be _careful_ now.",
        "지금 *빠른 수정*을 사용하고 _조심_하세요.",
    )


@pytest.mark.parametrize(
    ("source", "translated"),
    [
        ("This is ***important***.", "이건 **중요합니다**."),
        ("This is **important**.", "이건 ***중요합니다***."),
        ("This is ___important___.", "이건 __중요합니다__."),
        ("This is __important__.", "이건 ___중요합니다___."),
    ],
)
def test_validator_rejects_changed_bold_italic_markdown(source, translated):
    validator = TranslationOutputIntegrityValidator()

    with pytest.raises(TranslationIntegrityError) as raised:
        validator.validate(source, translated)

    assert "Markdown delimiters" in raised.value.violations
