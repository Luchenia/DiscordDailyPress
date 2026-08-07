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