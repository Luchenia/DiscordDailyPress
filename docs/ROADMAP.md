# Project Chronicle Roadmap

Project Chronicle은 Discord에서 발생하는 데이터를 장기적으로 수집하고,
이를 AI가 분석할 수 있는 형태로 가공한 뒤
최종적으로 일간 신문을 생성하는 것을 목표로 한다.

전체적인 데이터 처리 흐름은 다음과 같다.

```text
Discord
  ↓
Data Collection
  ↓
Raw Database
  ↓
Conversation Processing
  ↓
Language / Translation
  ↓
Topic Detection
  ↓
Summarization
  ↓
Newspaper Generation
```

---

# Sprint 1 — Project Foundation ✅

## 목표

Project Chronicle의 전체적인 프로젝트 구조와
기본 실행 환경을 구축한다.

## 완료

- 프로젝트 기본 구조 설계
- Python 실행 환경 구성
- 기본 애플리케이션 구조 구축
- 프로젝트 실행 흐름 구성
- 기본 설정 및 초기화 구조 구축

---

# Sprint 2 — Data Architecture ✅

## 목표

Discord에서 수집되는 데이터를 저장하기 위한
기본 데이터 구조와 Repository 계층을 구축한다.

## 완료

- Database 구조 설계
- SQLite 기반 저장 구조 구축
- Model 계층 구축
- DTO 계층 구축
- Mapper 계층 구축
- Repository 계층 구축
- Service 계층 구축
- 데이터 저장 구조 확립

Project Chronicle의 데이터 처리 구조를 다음과 같이
계층화하였다.

```text
Collector
    ↓
DTO
    ↓
Service
    ↓
Mapper
    ↓
Repository
    ↓
Database
```

---

# Sprint 3 — Application Core / Collector Preparation ✅

## 목표

실제 Discord 데이터를 수집하기 위한
애플리케이션 핵심 구조와 Collector 기반을 준비한다.

## 완료

- Application Bootstrap 구조 구축
- Logger 구축
- Discord Bot 실행 구조 구축
- Discord Collector 기반 구축
- Message 처리 Service 구조 구축
- 데이터 저장 Pipeline 연결 준비

이 Sprint를 통해 Project Chronicle은
실제 Discord 환경에서 동작할 수 있는
애플리케이션 구조를 갖추게 되었다.

---

# Sprint 4 — Discord Message Collection ✅

## 목표

Discord에서 발생하는 메시지를 실시간으로 수집하고
SQLite에 안정적으로 저장한다.

## 완료

- Bootstrap 구축
- Logger 구축
- SQLite Repository 구축
- Discord Collector 구축
- DTO / Service / Mapper 구조 완성
- 실시간 Discord 채팅 저장 성공

## 결과

Discord에서 발생한 메시지가 SQLite에
정상적으로 저장되는 것을 확인하였다.

Project Chronicle의 첫 번째
실시간 데이터 수집 Pipeline이 완성되었다.

---

# Sprint 5 — Message Lifecycle & Metadata ✅

## 목표

Discord 메시지의 메타데이터를 확장하고
메시지의 생성, 수정, 삭제 이력을 추적할 수 있는
시스템을 구축한다.

## 완료

### Metadata

- Discord Message ID 저장
- Guild / Channel 정보 저장
- Username / Display Name 저장
- Bot 여부 저장
- Attachment Metadata 저장
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

## 결과

Project Chronicle은 이제 Discord 메시지의

```text
Create
Update
Delete
```

전체 생명주기를 기록할 수 있는 구조를 갖추게 되었다.

이후 AI 분석에서는 현재 메시지 상태뿐만 아니라
메시지가 변화한 과정까지 활용할 수 있다.

---

# Sprint 6 — Language Detection ✅

## 목표

Discord 메시지의 언어를 자동으로 감지하여
AI 분석 Pipeline의 첫 단계를 구축한다.

## 완료

- Language Detection 구현
- Language Service 구현
- MessageService와 Language Service 연동
- 메시지 저장 시 언어 감지
- 메시지 수정 시 언어 재감지
- 언어 감지 예외 처리
- `unknown` 처리

## 초기 구현

초기에는 `langdetect`를 사용하였다.

한국어, 일본어, 중국어 등의 일반적인 문장은
정상적으로 감지할 수 있었지만,
짧은 문장에서는 오인식 문제가 발견되었다.

예:

```text
Hello everyone.
→ no
```

또한 Discord의 특성상 다음과 같이
짧게 분리된 메시지가 자주 발생할 수 있다는 점을 확인하였다.

```text
안
녕
하세요
```

개별 Message 단위의 언어 감지는
충분한 문맥을 확보하기 어렵다는 문제가 있었다.

## 설계 변경

언어 감지를 개별 Message 단위에서
Conversation 단위로 수행하는 방향으로 변경하였다.

```text
Message
  ↓
Conversation
  ↓
Language Detection
```

## Data Principle

```text
Raw Data is Immutable.
AI uses Processed Data.
```

원본 데이터는 변경하지 않고,
AI 분석에 필요한 데이터는 별도의 처리 과정을 통해 생성한다.

---

# Sprint 6.5 — Conversation Processing ✅

## 목표

짧은 Discord 메시지를 Conversation 단위로 묶어
AI 분석에 필요한 문맥을 확보한다.

## 완료

### Conversation Buffer

- ConversationBuffer 구현
- ConversationSession 구현
- 사용자 + 채널별 Conversation 관리
- 마지막 메시지 이후 5초 inactivity 기반 Session 종료
- Background Cleanup Loop 구현
- 만료된 Conversation 자동 Flush

### Conversation Result

- ConversationResultDTO 구현
- Conversation의 Discord Message ID 추적
- Conversation 텍스트 병합
- Conversation 시작 / 종료 시간 기록
- Conversation 단위 Language Detection

### Language Post Processing

Conversation이 종료되면 전체 Conversation을 하나의
텍스트로 합쳐 언어를 다시 감지한다.

예:

```text
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
```

감지된 언어는 Conversation에 포함된
원본 Discord Message ID를 기준으로
각 Message의 `language` 메타데이터에 반영한다.

### Logging

언어 후처리 결과를 다음과 같이 기록한다.

- 성공적으로 업데이트된 메시지 수
- 업데이트 실패 메시지 경고
- 전체 Conversation 처리 결과

예:

```text
Language update completed: 3/3 messages updated to ko
```

### Testing

Conversation Buffer 관련 자동화 테스트 구축.

주요 검증 항목:

- Conversation Session 생성
- 동일 사용자 / 채널 메시지 병합
- 5초 inactivity 기반 Session 종료
- 만료 Session Flush
- Conversation Language Detection
- ConversationResultDTO 생성
- Message ID 보존

실제 Discord 환경에서도
Conversation 생성 및 종료를 검증하였다.

## 결과

Project Chronicle의 데이터 처리 Pipeline이

```text
Message Collection
→ Conversation Buffer
→ Conversation Language Detection
→ Language Post Processing
```

으로 확장되었다.

---

# Sprint 6.6 — FastText Language Detection ✅

## 목표

기존 `langdetect`의 짧은 문장 오인식 문제를 개선하고
Discord Conversation 환경에 보다 적합한
언어 감지 시스템을 구축한다.

## 완료

- `langdetect` 기반 Detector 교체
- `fasttext-langdetect` 도입
- `fastText` 기반 Language Detection 구현
- 기존 LanguageService 인터페이스 유지
- Conversation Pipeline과 연동
- Language Detector 전용 테스트 추가
- 실제 Discord Integration Test 수행

## 변경

기존:

```text
langdetect
```

변경:

```text
fastText
```

FastText는 외부 AI API를 호출하지 않고
로컬에서 실행되므로
언어 감지 단계에서 별도의 API 비용이 발생하지 않는다.

## Benchmark

일반적인 문장에서는 안정적인 결과를 확인하였다.

```text
안녕하세요. 오늘 업데이트 정말 재미있네요.
→ ko

Hello everyone, I hope you are having a great day.
→ en

こんにちは、今日はとてもいい天気ですね。
→ ja

你好，今天过得怎么样？
→ zh
```

Conversation 단위 테스트에서도:

```text
안
녕
하세요

→ ko
```

```text
Hello
everyone,
how
are
you?

→ en
```

와 같이 정상적인 분할 메시지를
Conversation으로 합친 경우 높은 정확도를 확인하였다.

## 다국어 / 혼용 처리 정책

Conversation의 `language`는
개별 Message에 포함된 모든 단어의 언어를
정밀하게 판별한 값이 아니다.

Conversation 전체의 **대표 언어 / 주 언어**를 의미한다.

예:

```text
오늘 update 진짜 good
→ ko
```

이와 같이 제품명, 게임 용어, 외래어,
인터넷 용어 등의 부분적인 타 언어 사용은
Conversation의 주 언어에 영향을 주지 않는 것으로 처리한다.

Message별 언어 세분화는 현재 구현하지 않는다.

## 확인된 한계

지나치게 잘게 분할된 영어 문장에서는
FastText 역시 오인식할 수 있음을 확인하였다.

예:

```text
Hel
lo
ever
y
one
```

또는:

```text
hel
lo
every
body
```

와 같은 비정상적으로 분할된 문장은
`es`, `jbo` 등의 언어로 오인식될 수 있다.

현재는 이러한 예외를 해결하기 위한
AI fallback을 도입하지 않는다.

Project Chronicle의 목적은 언어 분류 자체의
완벽한 정확성이 아니라,
낮은 비용으로 AI 분석에 충분한 수준의
데이터를 안정적으로 수집하는 것이기 때문이다.

## 테스트

Conversation 관련 테스트:

```text
7 passed
```

Language Detector 테스트 추가 후:

```text
13 passed
```

실제 Discord 환경에서도
한국어 및 영어 Conversation의
Language Post Processing이 정상적으로 동작하는 것을 확인하였다.

## 결과

현재 Language Pipeline은 다음과 같이 확정되었다.

```text
Message Collection
→ Conversation Buffer
→ FastText Conversation Language Detection
→ Language Post Processing
```

---

# Future Data Collection

## Message / User Data

- [x] Message Edit History
- [ ] Nickname History
- [ ] Username History
- [ ] Role History

## Guild / Channel Data

- [ ] Channel Rename History
- [ ] Guild Rename History
- [ ] Thread Support

## Message Interaction Data

- [ ] Mention Collection
- [ ] Reaction Collection
- [x] Attachment Metadata

## Voice Data

- [ ] Voice Session Metadata

---

# AI Processing Roadmap

## Sprint 7 — Translation Service

### 목표

Conversation 데이터를 AI 분석에 사용할 수 있도록
번역 Pipeline을 구축한다.

### 설계

- [ ] Translation Service 설계
- [ ] Translation Data Model 설계
- [ ] 원본 데이터와 번역 데이터 분리
- [ ] 번역 대상 언어 정책 결정
- [ ] Conversation Translation 구현
- [ ] Translation 테스트
- [ ] 실제 Discord Integration Test

### Data Principle

원본 Message Content는 번역 결과로 덮어쓰지 않는다.

```text
Raw Message
    ↓
Immutable
```

번역은 원본과 별개의 파생 데이터로 관리한다.

```text
Original Conversation
        ↓
Translation
        ↓
Translated Data
```

### 보류

- [ ] Message별 다국어 세분화
- [ ] Mixed Language 판정
- [ ] Language Distribution 기반 세부 언어 태깅

위 기능들은 실제 운영 데이터에서 필요성이 확인될 경우
추후 별도 Sprint로 추가한다.

---

# Sprint 8 — Topic Detection

## 목표

Conversation에서 어떤 주제의 대화가 이루어졌는지
자동으로 분류한다.

## 계획

- [ ] Topic Detection 설계
- [ ] Topic 분류 기준 정의
- [ ] Conversation → Topic Pipeline 구현
- [ ] Topic 저장 구조 설계
- [ ] Topic Detection 테스트
- [ ] 실제 Discord Integration Test

---

# Sprint 9 — Summarization

## 목표

Conversation 및 Topic 단위의 대화를 요약하여
신문 생성에 사용할 수 있는 정보로 변환한다.

## 계획

- [ ] Conversation Summarization 설계
- [ ] Topic 기반 요약
- [ ] 핵심 사건 / 발언 추출
- [ ] 요약 결과 저장 구조 설계
- [ ] Summarization 테스트

---

# Sprint 10 — Newspaper Generator

## 목표

수집된 Discord 데이터를 기반으로
최종적으로 일간 신문을 자동 생성한다.

## 계획

```text
Conversation
    ↓
Language / Translation
    ↓
Topic Detection
    ↓
Summarization
    ↓
Newspaper Generator
```

- [ ] Newspaper Generator 설계
- [ ] 기사 구조 설계
- [ ] 기사 제목 생성
- [ ] 기사 본문 생성
- [ ] 주요 사건 분류
- [ ] 일간 신문 구성
- [ ] Newspaper Output 구현
- [ ] 전체 Pipeline Integration Test

---

# Future AI Features

Sprint 8~10 이후 실제 운영 데이터를 기반으로
필요성을 판단하여 추가한다.

- [ ] AI Sentiment Analysis
- [ ] AI Topic Classification 고도화
- [ ] AI Article Generation 고도화

---

# Project Architecture

현재 Project Chronicle의 핵심 Pipeline:

```text
Discord
  ↓
Message Collector
  ↓
Raw Database
  ↓
Message Lifecycle
(Create / Update / Delete)
  ↓
Conversation Buffer
  ↓
Conversation Session
  ↓
FastText Language Detection
  ↓
Language Post Processing
  ↓
Translation
  ↓
Topic Detection
  ↓
Summarization
  ↓
Newspaper Generator
```

---

# Core Data Principle

Project Chronicle은 다음 원칙을 유지한다.

```text
Raw Message Content and Event History are Immutable.

AI 분석 결과 및 파생 메타데이터는
후처리 과정에서 갱신할 수 있다.
```

즉,

- 원본 메시지 내용은 변경하지 않는다.
- 수정 이력은 변경하지 않는다.
- 삭제 이력은 변경하지 않는다.
- Language와 같은 파생 메타데이터는 후처리할 수 있다.
- Translation 결과는 원본과 분리한다.
- AI 분석 결과는 Raw Data와 분리한다.

이를 통해 AI Pipeline이 변경되더라도
원본 Discord 데이터를 다시 분석할 수 있도록 한다.


## Sprint 6.5 ✅

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

## Analysis Foundation ✅

- AnalysisScopeDTO
- AnalysisMessageDTO
- AnalysisDatasetDTO
- AnalysisDatasetMetadataDTO
- AnalysisService
- AnalysisScope 기반 데이터 조회
- StatisticsService
- 작성자별 통계
- 채널별 통계
- 일별 활동량 통계
- 시간대별 활동량 통계
- 언어 분포 통계
- 실제 SQLite 데이터 분석 검증

## Sprint 7

- 다국어 Conversation 처리
- Language Distribution
- 대표 언어 / 혼용 언어 정책
- Translation Service

## Sprint 8

- Topic Detection

## Sprint 9

- Summarization

## Sprint 10

- Newspaper Generator