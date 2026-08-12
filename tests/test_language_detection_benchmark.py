from langdetect import detect as langdetect_detect
from langdetect.lang_detect_exception import LangDetectException

from ftlangdetect import detect as fasttext_detect


TEST_CASES = [
    # 일반적인 문장
    ("한국어 일반 문장", "안녕하세요. 오늘 업데이트 정말 재미있네요."),
    ("영어 일반 문장", "Hello everyone, I hope you are having a great day."),
    ("일본어 일반 문장", "こんにちは、今日はとてもいい天気ですね。"),
    ("중국어 일반 문장", "你好，今天过得怎么样？"),

    # 분할 채팅
    ("한국어 분할", "안"),
    ("한국어 분할", "녕"),
    ("한국어 분할", "하세요"),

    ("영어 분할", "Hel"),
    ("영어 분할", "lo"),
    ("영어 분할", "every"),
    ("영어 분할", "one"),

    # 짧은 Discord 표현
    ("짧은 한국어", "ㅋㅋ"),
    ("짧은 한국어", "ㅎㅎ"),
    ("짧은 한국어", "ㅇㅇ"),
    ("짧은 한국어", "ㄴㄴ"),
    ("짧은 한국어", "안녕"),
    ("짧은 한국어", "네"),
    ("짧은 한국어", "응"),

    ("짧은 영어", "ok"),
    ("짧은 영어", "yes"),
    ("짧은 영어", "no"),
    ("짧은 영어", "hi"),
    ("짧은 영어", "lol"),

    # 혼합 언어
    ("한국어 + 영어", "안녕하세요 hello"),
    ("한국어 + 영어", "오늘 update 좋네"),
    ("영어 + 한국어", "Hello 오늘 어때?"),
    ("영어 + 한국어", "이거 really good"),

    # 기존 langdetect 문제 재현
    ("기존 오인식 테스트", "Hello everyone."),
]

# Conversation Buffer 시뮬레이션
CONVERSATION_TEST_CASES = [
    # --------------------------------------------------
    # 한국어 분할 메시지
    # --------------------------------------------------

    (
        "한국어 분할 Conversation",
        [
            "안",
            "녕",
            "하세요",
        ],
    ),

    (
        "한국어 문장 분할 Conversation",
        [
            "오늘",
            "날씨가",
            "정말",
            "좋네요",
        ],
    ),

    # --------------------------------------------------
    # 영어 분할 메시지
    # --------------------------------------------------

    (
        "영어 분할 Conversation",
        [
            "Hel",
            "lo",
            "every",
            "one",
        ],
    ),

    (
        "영어 문장 분할 Conversation",
        [
            "Hello",
            "everyone,",
            "how",
            "are",
            "you?",
        ],
    ),

    # --------------------------------------------------
    # 짧은 Discord 메시지
    # --------------------------------------------------

    (
        "한국어 짧은 Conversation",
        [
            "안녕",
            "ㅋㅋ",
            "오늘",
            "뭐해",
        ],
    ),

    (
        "영어 짧은 Conversation",
        [
            "hi",
            "lol",
            "what",
            "are",
            "you",
            "doing",
        ],
    ),

    # --------------------------------------------------
    # 한국어 + 영어 혼용
    # --------------------------------------------------

    (
        "한국어 영어 혼용",
        [
            "오늘",
            "update",
            "진짜",
            "good",
        ],
    ),

    (
        "영어 한국어 혼용",
        [
            "Hello",
            "오늘",
            "어때?",
        ],
    ),

    (
        "한국어 영어 자연스러운 혼용",
        [
            "이거",
            "really",
            "good",
            "하네",
        ],
    ),

    (
        "영어 한국어 자연스러운 혼용",
        [
            "This",
            "게임",
            "진짜",
            "재밌다",
        ],
    ),

    # --------------------------------------------------
    # 언어가 명확하게 분리된 혼용
    # --------------------------------------------------

    (
        "한국어 문장 + 영어 문장",
        [
            "오늘 날씨가 정말 좋다.",
            "I want to go outside.",
        ],
    ),

    (
        "영어 문장 + 한국어 문장",
        [
            "I really like this game.",
            "이 게임 정말 재미있어.",
        ],
    ),
]

def run_conversation_benchmark():
    print()
    print("=" * 100)
    print("Conversation Language Detection Benchmark")
    print("=" * 100)

    for name, messages in CONVERSATION_TEST_CASES:

        conversation_text = " ".join(messages)

        result = run_fasttext(
            conversation_text
        )

        print()
        print(f"[{name}]")

        print("Messages:")
        for index, message in enumerate(messages, start=1):
            print(
                f"  {index}. {message}"
            )

        print(
            f"Conversation: {conversation_text}"
        )

        print("fastText:")

        for item in result:
            print(
                f"  {item['lang']:>5} "
                f"{item['score']:.4f}"
            )


def run_langdetect(text: str) -> str:
    try:
        return langdetect_detect(text)
    except LangDetectException:
        return "unknown"


def run_fasttext(text: str):
    try:
        return fasttext_detect(
            text=text,
            low_memory=True,
            k=3,
        )
    except ValueError:
        return [
            {
                "lang": "unknown",
                "score": 0.0,
            }
        ]


def main():
    print("=" * 100)
    print("Language Detection Benchmark")
    print("=" * 100)

    for name, text in TEST_CASES:
        langdetect_result = run_langdetect(text)
        fasttext_result = run_fasttext(text)

        print()
        print(f"[{name}]")
        print(f"Text: {text}")

        print(f"langdetect : {langdetect_result}")

        print("fastText   :")

        for result in fasttext_result:
            print(
                f"  {result['lang']:>5} "
                f"{result['score']:.4f}"
            )




if __name__ == "__main__":
    main()
    run_conversation_benchmark()