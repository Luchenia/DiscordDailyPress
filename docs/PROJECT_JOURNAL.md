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