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



# 1. PROJECT_JOURNAL.md 기록

이번 스프린트 마지막에 아래 내용을 추가하자.

```markdown
## Sprint 6.5 / Analysis Foundation 완료

### 구현 완료

- Conversation Buffer
- Conversation Session
- 사용자 + 채널별 Conversation 관리
- 5초 inactivity 기반 Session 종료
- Background Cleanup Loop
- ConversationResultDTO
- Message ID 추적
- Conversation 단위 Language Detection
- Language Post Processing
- Message.language 사후 업데이트
- Conversation Buffer 테스트
- 실제 Discord 통합 테스트

### Analysis Foundation

- AnalysisScopeDTO
- AnalysisMessageDTO
- AnalysisDatasetDTO
- AnalysisDatasetMetadataDTO
- AnalysisService
- AnalysisScope 기반 Message 조회
- StatisticsService
- 작성자별 메시지 통계
- 채널별 메시지 통계
- 일별 메시지 활동량
- 시간대별 메시지 활동량
- 언어 분포 통계

### 테스트

- 전체 pytest 26 PASS
- 실제 SQLite 데이터 기반 AnalysisService 실행
- 실제 SQLite 데이터 96개 분석 성공
- 작성자 2명 집계 성공
- 채널 1개 집계 성공
- 일별 활동량 집계 성공
- 시간대별 활동량 집계 성공
- 언어 분포 계산 성공

### 실제 DB 검증 중 발견된 문제

실제 분석 과정에서 `messages.id=10`의 `edited_at` 값이
`0`으로 저장되어 SQLAlchemy DateTime 변환 오류가 발생했다.

원인을 확인한 뒤 기존 DB를 백업하고 해당 잘못된 nullable
datetime 값을 `NULL`로 복구했다.

- DB backup 생성
- `edited_at=0` 데이터 확인
- `edited_at=0 → NULL` 복구
- 복구 후 ORM 조회 정상
- 전체 테스트 26 PASS
- 실제 분석 정상 완료

### 검증 결과

실제 Discord에서 수집된 Raw Message Data를 SQLite에서 조회하여
AnalysisScope → AnalysisDataset → StatisticsResult까지 연결하는
분석 파이프라인이 정상적으로 동작함을 확인했다.

현재 Chronicle은 수집된 원본 데이터를 지정된 범위에 따라 조회하고
기본적인 통계 분석을 수행할 수 있는 상태다.

### 다음 단계

Sprint 7에서는 다국어 Conversation 처리와 분석 결과의 언어 정책을
설계한다.

- Language Distribution
- 대표 언어 / 혼용 언어 정책
- Translation Service
- 다국어 분석 결과 처리
```
# Sprint 6.7 — Analysis Command & Statistics Expansion

## 목표

기존에 구축한 Analysis Foundation을 실제 Discord Slash Command에서 사용할 수 있도록 확장한다.

사용자가 Discord에서 분석 기간을 선택하고, 지정된 범위의 데이터를 분석하여 통계 결과를 확인할 수 있는 `/분석` 명령어를 구축한다.

## 완료

### Analysis Request

- AnalysisRequestDTO 구현
- Guild ID 기반 분석 요청 구성
- 분석 시작 시간 및 종료 시간 관리
- 출력 언어 관리

### Analysis Period

분석 기간을 사용자가 선택할 수 있도록 분석 기간 처리 구조를 구축하였다.

지원 기간:

- 오늘
- 이번 주
- 이번 달
- 올해
- 직접 입력

구현:

- AnalysisPeriodService
- 기간별 시작 및 종료 시간 계산
- 사용자 지정 기간 처리

### Analysis Scope

분석 요청으로부터 실제 분석 대상 범위를 결정하는 AnalysisScopeResolver를 구현하였다.

구조:

AnalysisRequest
→ AnalysisScopeResolver
→ AnalysisScope

AnalysisScope에는 다음 정보가 포함된다.

- Guild ID
- 분석 대상 Channel ID
- 분석 시작 시간
- 분석 종료 시간

### Analysis Dataset

분석 범위에 해당하는 Message Data를 조회하여 분석 전용 Dataset으로 변환하는 구조를 구축하였다.

구조:

AnalysisScope
→ Message Data
→ AnalysisDataset

AnalysisDataset에는 다음 정보가 포함된다.

- Analysis Message
- Message Metadata
- Message Count
- Author Count
- Channel Count
- Language Distribution

원본 Raw Message Data는 변경하지 않고 분석을 위한 별도의 Dataset을 생성한다.

## Statistics Service

AnalysisDataset을 기반으로 통계 정보를 계산하는 StatisticsService를 확장하였다.

### 기본 통계

- 전체 메시지 수
- 전체 작성자 수
- 전체 채널 수
- 작성자별 메시지 수
- 채널별 메시지 수
- 일별 메시지 활동량
- 시간대별 메시지 활동량
- 언어 분포

### 추가 분석 통계

#### 평균 메시지 길이

전체 메시지의 문자 수를 기반으로 평균 메시지 길이를 계산한다.

계산 방식:

전체 메시지 문자 수 ÷ 전체 메시지 수

메시지가 없는 경우 `0.0`으로 처리한다.

#### 가장 활발한 시간대

시간대별 메시지 수를 비교하여 가장 많은 메시지가 발생한 시간을 계산한다.

구조:

hourly_activity
→ 가장 많은 메시지 수를 가진 hour
→ peak_activity_hour

분석 대상 메시지가 없는 경우 `None`으로 처리한다.

#### 가장 활발한 날짜

일별 메시지 활동량을 비교하여 가장 많은 메시지가 발생한 날짜를 계산한다.

구조:

daily_activity
→ 가장 많은 메시지 수를 가진 날짜
→ peak_activity_date

동일한 메시지 수를 가진 날짜가 여러 개 존재하는 경우에도 결정적인 결과가 나오도록 처리하였다.

메시지가 없는 경우:

- peak_activity_date = None
- peak_activity_date_count = 0

## Statistics Result

StatisticsResultDTO에 추가 분석 결과를 반영하였다.

추가 필드:

- average_message_length
- peak_activity_hour
- peak_activity_date
- peak_activity_date_count

이를 통해 단순 집계 결과뿐 아니라 분석 대상의 활동 특성을 확인할 수 있는 기본적인 분석 지표를 제공할 수 있게 되었다.

## Analysis Service Integration

AnalysisService에서 전체 분석 Pipeline을 연결하였다.

구조:

AnalysisRequest
→ AnalysisScopeResolver
→ AnalysisScope
→ AnalysisDataset
→ StatisticsService
→ StatisticsResult

Dataset 생성 과정에서 오류가 발생하는 경우 StatisticsService를 호출하지 않도록 실패 흐름도 테스트하였다.

# Discord Analysis Command

## `/분석`

분석 기능을 실제 Discord Slash Command와 연결하였다.

사용자는 Discord에서 `/분석` 명령어를 실행하여 분석 가능한 데이터를 확인하고 원하는 분석 기간을 선택할 수 있다.

## 분석 기간 선택

Slash Command의 분석 기간 Parameter를 구축하였다.

지원되는 기간:

- 오늘
- 이번 주
- 이번 달
- 올해
- 직접 입력

직접 입력을 선택한 경우 Custom Period Modal을 통해 시작일과 종료일을 입력할 수 있도록 구성하였다.

## Analysis Result Embed

분석 결과를 Discord Embed 형태로 출력하도록 구현하였다.

분석 결과에서 다음 통계 정보를 사용할 수 있다.

- 전체 메시지 수
- 작성자 수
- 채널 수
- 주요 작성자
- 채널별 활동량
- 일별 활동량
- 시간대별 활동량
- 언어 분포
- 평균 메시지 길이
- 가장 활발한 시간대
- 가장 활발한 날짜

## Collection Channel Integration

분석 대상 채널을 별도로 관리하기 위한 Collection Channel 구조를 구축하였다.

완료:

- CollectionChannel Model
- CollectionChannelRepository
- 활성화된 분석 대상 채널 조회
- Channel ID 기반 분석 범위 구성

이를 통해 Chronicle이 모든 Discord 채널을 무조건 분석하는 것이 아니라 지정된 수집 및 분석 대상 채널을 기준으로 데이터를 처리할 수 있는 기반을 구축하였다.

# Multilingual Analysis Command

Discord Interaction Locale을 기반으로 분석 명령어의 사용자 인터페이스를 다국어로 처리할 수 있는 구조를 구축하였다.

다국어 처리 대상:

- Command 이름
- Command 설명
- Parameter 이름
- Parameter 설명
- 분석 기간 선택지
- Custom Period Modal
- 분석 결과
- 오류 메시지

Localization 구조를 별도 모듈로 분리하여 Analysis Command 내부에 언어별 문자열을 직접 하드코딩하지 않도록 구성하였다.

# Testing

Analysis 기능 확장 과정에서 각 계층별 자동화 테스트를 추가하였다.

추가 테스트:

- Analysis Request 테스트
- Analysis Period Service 테스트
- Analysis Scope Resolver 테스트
- Analysis Service Flow 테스트
- Analysis Integration 테스트
- Collection Channel 테스트
- Collection Channel Repository 테스트
- Analysis Command 테스트
- Statistics 확장 테스트

## Statistics Test

StatisticsService에서 다음 항목을 검증하였다.

- 작성자별 메시지 수
- 채널별 메시지 수
- 일별 활동량
- 시간대별 활동량
- 언어 분포
- 평균 메시지 길이
- 가장 활발한 시간대
- 가장 활발한 날짜
- 빈 Dataset 처리
- 동일한 활동량을 가진 날짜 처리

## Analysis Command Test

Discord Analysis Command에 대해 다음 동작을 검증하였다.

- Command Parameter 생성
- 분석 기간 선택
- 기간 Autocomplete
- 다국어 Autocomplete
- Custom Period Modal
- 직접 입력 처리
- 분석 Service 호출
- 분석 결과 Embed 생성
- 분석 대상 채널이 없는 경우 처리
- 분석 오류 처리

# Final Test

최종적으로 전체 프로젝트 테스트를 실행하였다.

결과:

100 passed

기존 기능과 새롭게 추가된 Analysis 기능이 서로 정상적으로 연동되는 것을 확인하였다.

# Discord Integration Test

자동화 테스트뿐만 아니라 실제 Discord 환경에서 `/분석` 명령어를 실행하여 분석 결과가 정상적으로 출력되는 것을 확인하였다.

전체 흐름:

Discord
→ `/분석`
→ AnalysisRequest
→ AnalysisScope
→ AnalysisDataset
→ StatisticsService
→ StatisticsResult
→ Discord Embed

전체 흐름이 실제 환경에서 정상적으로 동작함을 확인하였다.

# 결과

Project Chronicle은 이제 Discord에서 수집한 Raw Message Data를 단순히 저장하는 단계에서 벗어나 다음과 같은 실제 분석 Pipeline을 갖추게 되었다.

Raw Data
→ Analysis Scope
→ Analysis Dataset
→ Statistics
→ Discord Analysis

특히 `/분석` 명령어를 통해 수집된 Discord 데이터를 사용자가 직접 확인할 수 있게 되었다.

이는 향후 Translation, Topic Detection, Summarization, Newspaper Generation으로 이어지는 AI Processing Pipeline을 검증하기 위한 중간 분석 계층으로 활용할 수 있다.

# 설계 원칙

기존 Project Chronicle의 Raw Data 원칙을 그대로 유지한다.

Raw Message Content and Event History are Immutable.

AI 분석 결과 및 파생 메타데이터는 후처리 과정에서 갱신할 수 있다.

Analysis는 Raw Data를 변경하지 않고 분석 대상 범위에 따라 별도의 AnalysisDataset을 생성한다.

따라서 향후 분석 로직이 변경되더라도 기존 Raw Data를 다시 분석할 수 있다.

# 회고

이번 Sprint에서는 기존에 구축한 Analysis Foundation을 실제 Discord Command로 확장하였다.

AnalysisRequest, AnalysisScope, AnalysisDataset, StatisticsService를 연결하고 기간 선택 및 Custom Period 기능을 구현하여 사용자가 Discord에서 직접 분석을 요청할 수 있도록 하였다.

또한 작성자, 채널, 날짜, 시간대, 언어 분포와 같은 기본 통계뿐 아니라 다음과 같은 추가 분석 지표를 구현하였다.

- 평균 메시지 길이
- 가장 활발한 시간대
- 가장 활발한 날짜

마지막으로 전체 테스트 100개가 모두 통과하고 실제 Discord 환경에서도 `/분석` 명령어가 정상적으로 동작하는 것을 확인하였다.

이를 통해 Project Chronicle은 다음 단계까지 실제 동작 가능한 데이터 처리 및 분석 기반을 확보하였다.

Message Collection
→ Conversation Processing
→ Language Detection
→ Analysis Foundation
→ Discord Analysis

# 다음 단계

다음 단계에서는 기존 Roadmap에 정의된 Translation Service를 진행한다.

주요 작업:

- 다국어 Conversation 처리
- Language Distribution 활용
- 대표 언어 및 혼용 언어 정책
- Translation Service 설계
- Translation Data Model
- 원본 데이터와 번역 데이터 분리
- Conversation Translation
- Translation 테스트
- 실제 Discord Integration Test

또한 향후 Voice Collector를 별도의 Data Collection 확장 영역으로 설계한다.

# Translation Provider Benchmark (2026-09-06)

Gemini 3.5 Flash-Lite와 NVIDIA Riva Translate 4B v2를 실제 Discord 대화 번역
후보로 비교하였다. 영어/한국어 일반 문장, slang, 은어, 한영 혼용, emoji,
Discord mention, URL, inline code, fenced code와 Markdown을 포함한 8개 case를
사용했으며 provider별 8회, 총 16회 API request를 재시도 없이 실행했다.

Blind human evaluation과 자동 보존 검사를 합친 결과:

| Provider | 평균 정성 점수 | 평균 latency |
| --- | ---: | ---: |
| Gemini 3.5 Flash-Lite | 93.4 | 약 3.812s |
| NVIDIA Riva Translate 4B v2 | 73.9 | 약 0.775s |

NVIDIA는 약 4.9배 빨랐지만, Discord slang과 한국어 은어에서 의미 왜곡이
나타났고 fenced code 및 `API_KEY` 변경 금지 지시를 누락한 case가 있었다.
Gemini는 한 case에서 `패치 노드`라는 오타가 있었으나 전체 의미, 말투,
mention, URL, code, Markdown 보존 품질에서 우세했다.

현재 설계 방향은 Gemini-first이다. NVIDIA는 짧고 단순한 plain-text에 대한
조건부 fast-path 또는 fallback 후보로 유지한다. Provider error뿐 아니라
mention, URL, inline/fenced code 같은 출력 무결성 검증 실패도 failover 조건에
포함해야 한다. Groq는 별도 검증 전까지 provider 순서에 확정적으로 포함하지
않는다.

# Sprint 7 — Translation Pipeline 구현 상태 (2026-09-07)

## 완료

- 원문과 분리된 `message_translations` 파생 데이터 Model / Repository / Alembic migration
- Message ID, 대상 언어, 원문 content hash 기반 번역 식별과 중복 방지
- bounded in-memory Queue와 single asynchronous Worker
- Conversation 종료 및 Message 수정 commit 이후 번역 작업 생성
- 활성 `CollectionChannel`만 번역 대상으로 사용하는 scope 정책
- 삭제된 Message, 같은 대상 언어, stale content hash 번역 제외
- Gemini Translation Provider
- NVIDIA Translation Provider
- Gemini-first Provider fallback
- Discord mention, URL, inline/fenced code, emoji, Markdown 보존 검사
- Bot 시작, queue drain, timeout, 종료 lifecycle 연동
- DB 처리를 `asyncio.to_thread`로 분리하여 Discord event loop blocking 방지
- Conversation flush부터 별도 번역 row 저장까지 자동화 Integration Test

## 현재 계약

- `messages.content`는 번역으로 덮어쓰지 않는다.
- 각 Message의 원문 언어를 Provider의 source language로 사용한다.
- 번역은 `TRANSLATION_TARGET_LANGUAGE`로 설정한 단일 대상 언어를 사용하며
  기본값은 `ko`다.
- 두 API key가 모두 있으면 Gemini 다음 NVIDIA 순서로 각각 한 번 시도한다.
- Provider 오류뿐 아니라 출력 무결성 실패도 다음 Provider로 넘어가는 조건이다.
- 원문 수정 중 생성된 오래된 결과와 삭제된 Message의 결과는 저장하지 않는다.

## 남은 작업

- 새 Ubuntu host에서 실제 Discord와 외부 Provider를 사용한 운영 통합 검증
- 번역 결과를 Analysis / Topic Detection 입력으로 선택하는 정책과 조회 경로
- process restart 후 Queue 복구와 자동 retry가 실제 운영에 필요한지 검토
- 대표 언어 / mixed language 세부 정책

외부 Discord/API 검증은 외부 상태 변경 또는 API 비용을 발생시킬 수 있으므로
사용자 approval 이후 별도로 수행한다.

## Ubuntu 중앙 개발환경 검증

- 중앙 개발 host: `chronicle-dev`
- Project path: `/home/amadeus/projects/DiscordDailyPress`
- Project Python: 3.11
- `uv` 기반 `.venv`와 `requirements-dev.txt` 설치 절차 문서화
- Translation 관련 회귀 테스트: 117 passed
- 전체 자동화 테스트: 234 passed, 3 deprecation warnings
- 실제 SQLite DB와 외부 Discord / Translation API를 사용하지 않고 검증

# Sprint 7.1 — Translation Analysis Consumption (2026-09-08)

## 목표

저장된 번역 중 현재 Message content와 정확히 일치하는 파생 데이터만
AnalysisDataset 준비 단계에서 안전하게 선택한다.

## 구현

- `MessageTranslationRepository.get_current_batch` 단일 조회 경계 추가
- `AnalysisTextResolver`와 `MissingTranslationPolicy` 도입
- 기본 `RawSourceFallbackPolicy` 구현
- `AnalysisRequestDTO.output_language`를 Dataset 준비 경로에 연결
- `AnalysisMessageDTO`에 다음 provenance 필드 추가
  - `analysis_content`
  - `analysis_language`
  - `analysis_content_source`
  - `source_content_hash`
  - `translation_id`

기존 `content`와 `language`는 원문과 원문 언어로 유지한다. 따라서 현재
StatisticsService의 메시지 길이와 언어 분포 의미는 바뀌지 않으며, 후속 AI
분석은 `analysis_content`와 `analysis_language`를 명시적으로 사용할 수 있다.

## 안전 계약

- 현재 Message content hash와 일치하지 않는 stale translation은 선택하지 않는다.
- stale row는 삭제하거나 갱신하지 않고 그대로 보존한다.
- 같은 언어 Message는 번역 조회 없이 원문을 사용한다.
- 번역이 없거나 빈 번역이면 기본 policy가 원문으로 fallback한다.
- 역사 DB의 nullable / blank source language는 저장값을 수정하지 않고 분석
  경계에서 기존 `unknown` 계약으로 정규화한다.
- fallback 결과는 source kind와 실제 언어가 명시되어 downstream이 판단할 수 있다.
- soft-deleted Message는 기존 Analysis query에서 제외하며 resolver 직접 입력도 거부한다.
- Dataset 준비 과정은 DB read만 수행하고 외부 Provider/API를 호출하지 않는다.
- 실제 Chronicle DB와 `messages.content`를 수정하지 않는다.

## 검증

- translation-consumption focused tests: 6 passed
- related Analysis regression tests: 60 passed
- full test suite: 240 passed, 3 existing deprecation warnings
- current / stale / missing / same-language / edited-new-hash / batch / deleted 시나리오 검증
- mock provider와 in-memory SQLite만 사용하여 외부 API 호출 없음

## 다음 단계

Sprint 8 Topic Detection이 `AnalysisMessageDTO.analysis_content`를 입력으로
사용하도록 provider-independent service / DTO 계약을 먼저 설계한다.

# Sprint 8 — Topic Detection Foundation (2026-09-08)

## 구현

- `TopicDetectionProvider` 비동기 protocol을 추가했다.
- `TopicDetectionService`가 준비된 `AnalysisDatasetDTO`를 받아 provider용 입력과
  Chronicle topic 결과를 만드는 경계를 추가했다.
- provider 입력에는 raw `content`를 노출하지 않고 `analysis_content`, 분석/원문
  언어, message identity, content source/hash, translation ID를 전달한다.
- provider 결과는 topic ID, optional label, message membership, explicit
  unassigned/noise ID로 구성한다.

## 안전 계약

- 입력 DTO는 immutable이며 translation/raw provenance 조합을 검증한다.
- provider 결과는 모든 dataset message를 topic 또는 unassigned에 정확히 한 번
  포함해야 한다.
- dataset 밖의 ID, 중복 topic ID, 중복 membership, 누락 ID는 계약 오류로
  거부한다.
- soft-deleted Message는 기존 AnalysisDataset에서 제외되고 provider가 dataset
  밖의 삭제 ID를 반환해도 다시 포함되지 않는다.
- 저장소와 production DB를 변경하지 않으며 외부 API를 호출하지 않는다.

## 남은 결정

Topic 수, hierarchy, clustering threshold, provider 선택, persistence schema는
운영 정책이 정해진 뒤 provider 및 repository 구현 단계에서 결정한다.

## 검증

- Topic Detection focused tests: 6 passed
- Analysis/translation 관련 회귀 테스트: 21 passed
- 제한된 sandbox에서 종료 가능한 전체 회귀 범위: 229 passed, 기존 warning 3개
- 외부 provider/API 및 production DB mutation 없음

# Sprint 9 — Topic Summarization Foundation (2026-09-08)

## 구현

- `TopicSummarizationProvider` 비동기 protocol을 추가했다.
- `TopicSummarizationService`가 검증된 `TopicDetectionResultDTO`를 받아 topic별
  provider 입력과 evidence-linked summary 결과를 만드는 경계를 추가했다.
- provider 입력은 topic ID, optional label, 명시적 output language, prepared
  `TopicDetectionMessageDTO`만 포함한다.
- topic message는 `created_at`, message ID 순으로 정렬하여 provider 입력을
  deterministic하게 유지한다.
- 결과는 analysis scope, detector/summarizer ID, output language, topic identity,
  source hash, translation provenance와 unassigned/noise message를 보존한다.

## 안전 계약

- raw `messages.content` field는 summarization provider 계약에 노출하지 않는다.
- 모든 detected topic은 정확히 하나의 summary를 가져야 한다.
- 중복, unknown, 누락 topic summary를 거부한다.
- blank summary와 empty/duplicate evidence를 거부한다.
- evidence message ID는 해당 topic membership에 속해야 한다.
- unassigned/noise message는 summary topic으로 변환하지 않고 결과 provenance에
  명시적으로 유지한다.
- 저장소, schema, production DB, bot runtime과 외부 API를 변경하지 않는다.

## 검증

- Topic Summarization focused tests: 16 passed
- Topic Detection / Analysis Translation 관련 회귀 테스트: 21 passed
- 제한된 sandbox에서 종료 가능한 전체 회귀 범위: 245 passed, 기존 warning 3개
- DB-thread test 실행이 가능한 환경의 전체 회귀 범위: 262 passed, 기존 warning 3개
- production Chronicle DB size, mtime, SHA-256 불변 확인

## 남은 결정

Production topic detector/summarizer provider, 입력 크기 제한, topic 정책,
persistence, bot wiring과 newspaper composition은 후속 단계에서 결정한다.

# Boundary-Safe Analysis Run Orchestration Foundation (2026-09-08)

## 구현

- `AnalysisRunRequestDTO`, `AnalysisRunLimitsDTO`, `AnalysisRunResultDTO`를 추가했다.
- `AnalysisRunService`가 prepared `AnalysisDatasetDTO`를 Topic Detection과 Topic
  Summarization service에 순차 전달하는 provider-independent 경계를 추가했다.
- `AnalysisService.prepare_dataset`을 application read boundary로 추가하고
  orchestration에서는 `asyncio.to_thread`로 호출한다.
- analysis scope repository query를 `created_at`, Discord message ID 순으로
  정렬한다.
- 모든 run은 caller가 positive `max_messages`, `max_total_characters`를 명시해야
  하며, prepared `analysis_content` 기준 초과 시 provider 호출 전에 거부한다.

## 안전 계약

- orchestration result는 raw `AnalysisDatasetDTO`를 downstream에 노출하지 않는다.
- scope, output language, detector/summarizer ID, dataset metadata, applied limits,
  source hash, translation provenance, evidence와 unassigned/noise를 보존한다.
- contract error는 그대로 전파하며 임의 topic 또는 summary를 만들지 않는다.
- production limit, token, billing, batching 정책을 선택하지 않는다.
- provider SDK, 외부 API, bot runtime, persistence, schema와 migration을 변경하지
  않는다.

## 검증

- Analysis Run orchestration focused tests: 9 passed
- orchestration + repository ordering focused scope: 15 passed
- Topic Detection / Topic Summarization / Analysis Translation 회귀: 37 passed
- 전체 자동화 테스트: 272 passed, 기존 warning 3개
- fake detector/summarizer만 사용하며 외부 API 호출 없음
- production Chronicle DB size, mtime, SHA-256 불변 확인

## 남은 결정

Production provider/model, 실제 input limit 값, batching, topic policy, persistence,
runtime wiring과 newspaper composition은 후속 단계에서 결정한다.

# Deterministic Newspaper Composer Foundation (2026-09-09)

## 구현

- immutable `NewspaperEditionMetadataDTO`, `NewspaperSectionDTO`,
  `NewspaperMessageProvenanceDTO`, `NewspaperResultDTO`를 추가했다.
- `NewspaperComposerService`가 검증된 `AnalysisRunResultDTO`를 순수 in-memory
  newspaper artifact와 Markdown으로 변환한다.
- section은 각 topic의 최초 prepared message `created_at`, message ID, topic ID
  순으로 정렬한다. message 수를 중요도 점수로 사용하거나 AI ranking 단계를
  추가하지 않는다.
- topic 내부와 unassigned/noise provenance는 `created_at`, message ID 순으로
  정렬한다.
- analysis scope 시작 시각을 KST로 변환한 날짜를 edition date로 사용하고,
  scope 양 끝을 KST로 표시한다. end boundary는 exclusive임을 명시하며 정확한
  UTC boundary도 DTO에 유지한다.

## artifact 계약

- Markdown은 고정 title, edition metadata, ordered topic sections, 마지막
  unassigned/noise section 순서다.
- 각 topic section은 제공된 label, 검증된 summary, topic message count,
  evidence ID/count, content-free source provenance만 표시한다.
- source provenance는 message/channel ID, UTC created time, source hash,
  source/analysis language, raw/translation 구분과 translation ID를 보존한다.
- label이 없으면 번호가 있는 구조적 `Topic N` heading만 사용한다.
- zero-topic run은 topic을 만들지 않고 factual empty state와 명시적
  unassigned/noise count/provenance를 표시한다.

## 안전 계약

- composer에는 provider, 외부 API, database, filesystem, 현재 clock dependency가
  없다.
- `analysis_content`와 raw `messages.content`를 DTO 또는 Markdown에 복사하지
  않는다.
- 동적 문자열의 HTML과 Markdown 구문을 escape하여 edition structure를 변경할
  수 없게 한다.
- scope-derived date와 안정된 ordering만 사용하므로 동일 입력은 byte-identical
  Markdown을 만든다.
- persistence, schema, migration, bot/runtime, file output을 변경하지 않는다.

## 검증

- Newspaper Composer focused tests: 8 passed
- Analysis Run / Topic Detection / Topic Summarization / Analysis Service 회귀:
  37 passed
- 전체 자동화 테스트: 280 passed, 기존 warning 3개
- production Chronicle DB size, mtime, SHA-256 불변 확인

## 남은 결정

Production detector/summarizer와 input limits, runtime orchestration entry point,
Discord 전달 형식/길이 분할, artifact persistence/retention은 후속 단계에서
결정한다.
