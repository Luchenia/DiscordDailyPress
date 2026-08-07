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