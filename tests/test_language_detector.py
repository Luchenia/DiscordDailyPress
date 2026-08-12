from app.utils.language_detector import detect_language


def test_hello_everyone_is_english():
    assert detect_language("Hello everyone.") == "en"

def test_korean_is_detected():
    assert detect_language("안녕하세요.") == "ko"


def test_english_is_detected():
    assert detect_language("Hello everyone.") == "en"


def test_japanese_is_detected():
    assert detect_language("こんにちは。") == "ja"

def test_chinese_is_detected():
    assert detect_language("你好，今天过得怎么样？") == "zh"

def test_empty_text_is_unknown():
    assert detect_language("") == "unknown"