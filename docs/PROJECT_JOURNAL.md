# Sprint 4 (2026-08-07)

## 완료

- Bootstrap 구축
- Logger 구축
- SQLite Repository 구축
- Discord Collector 구축
- DTO / Service / Mapper 구조 완성
- 실시간 Discord 채팅 저장 성공

## 결과

Discord에서 발생한 메시지가 SQLite에 정상 저장되는 것을 확인하였다.

Project Chronicle의 첫 번째 실시간 데이터 수집 파이프라인이 완성되었다.

다음 Sprint에서는 메시지 메타데이터 확장과 Voice Collector 설계를 시작한다.

# Sprint 5 (2026-08-08)

## 목표

Discord 메시지의 메타데이터를 확장하고,
메시지 수정 및 삭제 이력을 추적할 수 있는 시스템을 구축한다.

---

## 완료

### Metadata

- Discord Message ID 저장
- Guild / Channel 이름 저장
- Username / Display Name 저장
- Bot 여부 저장
- Attachment 메타데이터 저장
- Reply Message ID 저장
- Edited At 저장

### Message Edit

- Message Update 기능 구현
- MessageHistory 테이블 구축
- 수정 이력 저장 기능 구현

### Message Delete

- MessageDeleteHistory 테이블 구축
- 삭제 이력 저장 기능 구현
- 삭제 이벤트 처리 구현

---

## 결과

Project Chronicle는 이제 Discord 메시지의
생성(Create),
수정(Update),
삭제(Delete)
전체 생명주기를 기록할 수 있는 구조를 갖추게 되었다.

이후 AI 분석은 현재 상태뿐 아니라
메시지 변화 과정까지 활용할 수 있다.

---

## 다음 Sprint

- Language Detection
- Whisper Voice Collector 설계
- AI 분석 파이프라인 시작

# Sprint 6 (2026-08-08)

## 목표

Discord 메시지의 언어를 자동으로 감지하여 AI 분석 파이프라인의 첫 단계를 구축한다.

---

## 완료

### Language Detection

- langdetect 라이브러리 도입
- Language Detector 구현
- Language Service 구현
- MessageService와 연동
- 메시지 저장 시 언어 자동 감지
- 메시지 수정 시 언어 재감지

---

## 테스트

### 한국어

안녕하세요.

→ ko

### 영어

Hello everyone.

→ no (오인식)

### 일본어

こんにちは。

→ ja

### 중국어

你好。

→ zh-cn

---

## 발견한 문제

langdetect는 짧은 영어 문장을
노르웨이어(no)로 오인식하는 경우가 있었다.

짧은 문장이나 의미가 부족한 텍스트는
언어 감지 정확도가 낮아질 수 있다.

---

## 논의 내용

언어 감지를 메시지 단위가 아닌
Conversation 단위에서 수행하는 방향으로 설계를 변경하기로 결정하였다.

원본 데이터는 변경하지 않고,
AI 분석 전 단계에서 Conversation Buffer를 생성한다.

Buffer 조건

- 같은 작성자
- 같은 채널
- 마지막 메시지 이후 5초 이내

위 조건을 만족하면 하나의 Conversation Session으로 병합한다.

이를 통해

- 언어 감지 정확도 향상
- Topic Detection 정확도 향상
- 감정 분석 품질 향상
- 기사 생성 품질 향상

을 기대할 수 있다.

---

## Project Principle

Raw Data is Immutable.

AI uses Processed Data.

원본 데이터는 절대 수정하지 않는다.

AI는 가공된 데이터를 사용한다.

---

## 다음 Sprint

Conversation Buffer 설계 및 구현


### Technical Debt

Discord.py의 on_message_edit는 캐시에 존재하는 메시지만 수정 이벤트를 받을 수 있다.

Project Chronicle는 데이터 수집 신뢰성을 위해 향후
on_raw_message_edit / on_raw_message_delete 기반으로
Collector를 리팩터링할 예정이다.

## Sprint 6 회고

Language Detection을 구현하는 과정에서
짧은 메시지의 언어 판별 정확도가 낮다는 문제를 확인하였다.

이를 해결하기 위해
언어 감지를 메시지 단위가 아닌
Conversation Session 단위에서 수행하는 방향으로
아키텍처를 개선하기로 결정하였다.

원본 데이터는 그대로 보존하고,
AI는 Conversation Buffer를 통해 생성된
가공 데이터를 사용한다.





# Sprint 6.5 (2026-08-09)

## 목표

짧은 Discord 메시지의 언어 감지 정확도를 향상시키기 위해
메시지를 Conversation 단위로 묶어 처리하는
AI 전처리 시스템을 구축한다.

---

## 완료

### Conversation Buffer

- ConversationBuffer 구현
- ConversationSession 구현
- 작성자 + 채널 단위로 Session 분리
- 마지막 메시지 이후 5초 inactivity 기반 Session 종료
- 백그라운드 Cleanup Loop 구현
- 만료된 Conversation 자동 Flush

### Conversation Result

- ConversationResultDTO 구현
- Conversation의 원본 Discord Message ID 추적
- Conversation 텍스트 병합
- Conversation 시작 / 종료 시간 기록
- Conversation 단위 언어 감지

### Language Post Processing

실시간 메시지 저장 시 언어 감지가 어려운
짧은 메시지는 우선 `unknown`으로 저장한다.

Conversation이 종료되면 전체 Conversation을
하나의 텍스트로 합쳐 언어를 다시 감지한다.

감지된 언어는 Conversation에 포함된
원본 Discord Message ID를 기준으로
각 Message의 `language` 메타데이터에 반영한다.

이를 통해 다음과 같은 처리가 가능해졌다.

~~~text
안       → unknown
녕       → unknown
하세요   → unknown

        ↓

Conversation
"안 녕 하세요"

        ↓

language = ko

        ↓

안       → ko
녕       → ko
하세요   → ko
~~~

### Language Update Logging

언어 후처리 결과를 다음과 같이 기록하도록 개선하였다.

- 성공적으로 업데이트된 메시지 수 기록
- 업데이트 실패 메시지 경고 로그 기록
- 전체 Conversation 처리 결과 기록

예:

~~~text
Language update completed: 3/3 messages updated to ko
~~~

---

## 테스트

### Automated Test

Conversation Buffer 관련 테스트를 추가하고
총 7개의 테스트가 통과하였다.

~~~text
7 passed
~~~

검증 항목:

- Conversation Session 생성
- 동일 작성자 / 채널 메시지 병합
- 5초 inactivity 기반 Session 종료
- 만료 Session Flush
- Conversation 언어 감지
- ConversationResultDTO 생성
- Message ID 보존

### Discord Integration Test

실제 Discord 환경에서 다음 시나리오를 검증하였다.

#### 한국어

~~~text
안
녕
하세요
~~~

→ 하나의 Conversation으로 병합

→ `language = ko`

→ `3/3 messages updated to ko`

#### 영어

~~~text
Hel
lo
every
one
~~~

→ 하나의 Conversation으로 병합

→ `language = en`

→ `4/4 messages updated to en`

또한 메시지 사이의 간격이 5초를 초과하는 경우
Conversation이 정상적으로 분리되는 것을 확인하였다.

실제 테스트에서 약 5.046초의 간격이 발생한 메시지가
별도의 Conversation으로 처리되었으며,
이는 현재 정의한 5초 inactivity 조건이 정상적으로
동작하고 있음을 확인한 결과이다.

---

## 설계 결정

언어 감지를 개별 Message 단위에서
Conversation 단위로 변경하였다.

이 구조는 짧게 분할된 메시지뿐 아니라
향후 여러 언어가 혼용되는 Conversation을
처리할 수 있는 기반을 제공한다.

향후에는 Conversation 내 언어 분포를 분석하여
다국어 혼용 상황을 처리할 예정이다.

---

## Data Principle

기존의

> Raw Data is Immutable.

원칙을 다음과 같이 구체화한다.

> Raw Message Content and Event History are Immutable.  
> AI 분석 결과 및 파생 메타데이터는 후처리로 갱신할 수 있다.

즉, 메시지의 원본 내용과 생성 / 수정 / 삭제 이력은
변경하지 않으며,

`language`와 같은 AI 분석용 메타데이터는
Conversation 분석 결과에 따라 갱신할 수 있다.

---

## 회고

이번 Sprint에서는 단순한 Message 단위 언어 감지의
한계를 확인하고 Conversation 단위의 전처리 구조를
구축하였다.

특히 안, 녕, 하세요와 같이 짧게 분리된 메시지를
하나의 Conversation으로 묶은 후 언어를 감지하고,
그 결과를 각 원본 Message의 `language` 메타데이터에
반영하는 전체 파이프라인을 실제 Discord 환경에서
검증하였다.

이를 통해 Project Chronicle의 AI 분석 파이프라인은

~~~text
Message Collection
→ Conversation Buffer
→ Conversation Language Detection
→ Metadata Post Processing
~~~

으로 확장되었다.

다음 Sprint부터는 수집된 Conversation 데이터를
실제로 분석하여 신문에 활용할 수 있는 정보를
추출하는 단계로 넘어간다.



# Sprint 6.6 (2026-08-13)

## 목표

기존 `langdetect` 기반 언어 감지 시스템을
Discord Conversation 환경에 보다 적합한
`fastText` 기반 언어 감지 시스템으로 교체한다.

특히 `langdetect`에서 발생했던 짧은 영어 문장의
오인식 문제를 개선하고,
기존 Conversation Buffer 및 Language Post Processing
파이프라인과의 호환성을 유지한다.

---

## 변경 사항

### Language Detection Engine

기존:

- `langdetect`

변경:

- `fastText`
- `fasttext-langdetect 1.1.1`

`LanguageService`와 `ConversationBuffer`의
기존 인터페이스는 유지하고,
실제 언어 감지 구현체만 교체하였다.

이를 통해 상위 계층의 코드 변경을 최소화하면서
언어 감지 엔진을 교체할 수 있도록 하였다.

### FastText Configuration

메모리 사용량을 고려하여
`low_memory=True` 옵션을 사용한다.

언어 감지는 별도의 외부 API를 호출하지 않고
로컬에서 처리한다.

따라서 Conversation이 종료될 때 수행되는
언어 감지 과정에서 추가적인 API 비용이 발생하지 않는다.

---

## 기존 langdetect 문제

Sprint 6에서 `langdetect`를 사용하여
짧은 영어 문장의 언어 감지를 테스트한 결과,
다음과 같은 오인식이 발생하였다.

```text
Hello everyone.

langdetect → no
```

실제 의미와 관계없는 `no(노르웨이어)`로
판정되는 문제가 확인되었다.

이에 따라 Discord에서 수집되는 짧은 Conversation의
언어 판별 정확도를 개선하기 위해
fastText를 대체 언어 감지 엔진으로 검토하였다.

---

## FastText Benchmark

### 일반 문장

```text
한국어
안녕하세요. 오늘 업데이트 정말 재미있네요.
→ ko 1.0000

영어
Hello everyone, I hope you are having a great day.
→ en 0.9951

일본어
こんにちは、今日はとてもいい天気ですね。
→ ja 1.0000

중국어
你好，今天过得怎么样？
→ zh 0.9064
```

일반적인 문장에서는 안정적인 결과를 확인하였다.

---

## Conversation Benchmark

Conversation Buffer에서 실제로 생성되는
형태를 기준으로 언어 감지를 추가 테스트하였다.

### 한국어 분할

```text
안
녕
하세요

→ "안 녕 하세요"

fastText
ko 1.0000
```

### 영어 문장 분할

```text
Hello
everyone,
how
are
you?

→ "Hello everyone, how are you?"

fastText
en 0.9962
```

Conversation 단위로 메시지를 병합한 경우
짧게 분할된 메시지에서도 높은 정확도를 확인하였다.

### 짧은 Discord Conversation

```text
안녕
ㅋㅋ
오늘
뭐해

→ ko 0.9999
```

```text
hi
lol
what
are
you
doing

→ en 0.9650
```

짧은 인터넷 표현이 포함된 Conversation에서도
주 언어를 안정적으로 판별할 수 있었다.

---

## 다국어 및 혼용 Conversation 검토

한국어와 영어가 일부 혼용된 Conversation도 테스트하였다.

```text
오늘 update 진짜 good
→ ko 0.8943
```

```text
이거 really good 하네
→ ko 0.9396
```

이러한 결과를 바탕으로
일상적인 Discord Conversation에서 사용되는
외래어, 제품명, 게임 용어, 인터넷 용어 등의
부분적인 타 언어 사용은
Conversation의 주 언어 판별을 방해하는 수준이
아닌 것으로 판단하였다.

따라서 현재 단계에서는
Message별 언어를 별도로 세분화하지 않는다.

---

## 설계 결정

Project Chronicle에서 `language` 메타데이터는
개별 Message의 모든 단어가 어떤 언어인지
정밀하게 판별한 결과가 아니다.

대신 해당 Message가 속한
Conversation의 **주 언어(대표 언어)**를 의미한다.

예:

```text
Conversation

안
녕
하세요

        ↓

language = ko

        ↓

Message 1 → ko
Message 2 → ko
Message 3 → ko
```

Conversation 내부에 일부 영어 단어,
제품명, 게임 용어 또는 외래어가 포함되더라도
전체적인 대화 흐름이 한국어라면
Conversation의 주 언어를 `ko`로 유지한다.

이러한 일부 혼용은 실제 Discord 환경에서
자연스럽게 발생할 수 있으며,
신문 생성 및 AI 분석 목적에서는
허용 가능한 수준의 오차로 판단하였다.

---

## 다국어 Conversation 처리

하나의 Conversation 전체가
서로 다른 언어로 구성되는 극단적인 경우도
추가적으로 검토하였다.

FastText를 Conversation 전체에 적용하는 경우
일부 다국어 Conversation에서
한 언어로 편향된 결과가 발생할 수 있음을 확인하였다.

그러나 실제 Project Chronicle의 사용 환경에서는
하나의 Conversation 안에서 주 언어 자체가
지속적으로 변경되는 경우가 많지 않을 것으로 판단하였다.

또한 향후 Topic Detection,
Summarization,
Article Generation 등의 AI 분석 단계에서는
원본 Conversation 텍스트 전체를 사용하므로,
다국어 Conversation의 세부적인 언어 처리는
필요한 경우 AI 분석 단계에서 처리할 수 있다.

따라서 현재 단계에서는
Message별 언어 세분화,
Mixed Language 판정,
Message별 AI 언어 감지 등의 기능을
추가하지 않는다.

---

## 발견한 한계

FastText 역시 지나치게 잘게 분할된
영어 Conversation에서는 정확도가 크게 낮아지는
문제를 확인하였다.

예:

```text
Hel
lo
ever
y
one

→ "Hel lo ever y one"

fastText → es
```

또한:

```text
hel
lo
every
body

→ "hel lo every body"

fastText → jbo
```

와 같이 실제 영어 문장을 인위적으로
과도하게 분할한 경우 다른 언어로 오인식할 수 있었다.

이는 개별 단어 자체가 충분한 문맥을 가지고 있지 않고,
영어 문장 역시 정상적인 단어 형태로 구성되지 않기 때문에
발생하는 한계로 판단하였다.

이러한 형태는 실제 Discord에서 발생할 가능성이 있으나
현재 예상되는 사용 빈도와 Project Chronicle의 목적을
고려하여 별도의 AI fallback을 도입하지 않는다.

향후 실제 운영 데이터에서 해당 오인식이
유의미한 빈도로 발생할 경우 개선 대상으로 검토한다.

---

## 테스트

### Automated Test

기존 Conversation Buffer 테스트:

```text
7 passed
```

FastText 전환 이후에도
기존 Conversation 관련 테스트가
모두 정상적으로 통과하였다.

추가로 Language Detector 전용 테스트를 구축하였다.

검증 항목:

- 영어 감지
- 한국어 감지
- 일본어 감지
- 중국어 감지
- `Hello everyone.` 회귀 테스트
- 빈 문자열 `unknown` 처리

최종 결과:

```text
13 passed
```

이를 통해 기존 Conversation Pipeline과
FastText 기반 Language Detector가
정상적으로 연동되는 것을 확인하였다.

---

## Discord Integration Test

실제 Discord 환경에서 FastText 기반
Conversation Language Detection을 검증하였다.

### 한국어

```text
안
녕
하세요
```

→

```text
language = ko
7/7 messages updated to ko
```

### 영어

```text
Hello
everyone
```

→

```text
language = en
2/2 messages updated to en
```

정상적인 한국어 및 영어 Conversation에서는
주 언어가 정상적으로 감지되고,
Conversation에 포함된 모든 Message의
`language` 메타데이터가 정상적으로 갱신되는 것을 확인하였다.

또한 의도적으로 영어 문장을 지나치게 분할한 경우
`es`, `jbo` 등의 오인식이 발생하는 것을 실제 Discord에서
확인하였다.

---

## Data Principle

기존 원칙을 유지한다.

```text
Raw Message Content and Event History are Immutable.
AI 분석 결과 및 파생 메타데이터는 후처리로 갱신할 수 있다.
```

`language`는 원본 데이터가 아닌
Conversation 분석으로 생성된 파생 메타데이터이므로
Conversation 종료 후 갱신할 수 있다.

---

## 회고

이번 Sprint에서는 기존 `langdetect` 기반
언어 감지 시스템을 fastText 기반으로 교체하였다.

`Hello everyone.`이 `no`로 오인식되는
기존 문제를 해결하였으며,
일반적인 한국어 및 영어 Conversation과
짧게 분할된 Conversation에서
안정적인 언어 감지 결과를 확인하였다.

특히 Conversation Buffer와 Language Post Processing의
기존 구조를 변경하지 않고
언어 감지 구현체만 교체할 수 있었으며,
총 13개의 자동화 테스트가 모두 통과하였다.

실제 Discord 환경에서도
Conversation 종료 → 언어 감지 →
Message language 후처리의 전체 파이프라인이
정상적으로 동작함을 확인하였다.

반면 영어 문장을 지나치게 잘게 분할하는
비정상적인 입력에서는 오인식이 발생할 수 있음을 확인하였다.

현재는 이러한 예외를 해결하기 위해
AI fallback이나 Message별 언어 분석을 추가하지 않는다.

Project Chronicle의 목표는
언어 분류 자체의 완벽한 정확성이 아니라
낮은 비용으로 AI 분석에 충분한 수준의
데이터를 안정적으로 수집하는 것이므로,
현재 수준의 오차는 허용 가능한 것으로 판단하였다.

이를 통해 Project Chronicle의 언어 처리 파이프라인은

Message Collection
→ Conversation Buffer
→ FastText Conversation Language Detection
→ Metadata Post Processing

구조로 확정되었다.

다음 단계에서는 이 언어 데이터를 기반으로
Translation Service 설계를 시작한다.