---
name: inbox
description: Triage an English inbox for real export-sales leads — sort Outlook or pasted mail into act-now / check / ignore, filtering out spam, cold vendor pitches and brokers. Use when the user asks to go through their mailbox, find leads worth replying to, says "메일함 좀 훑어줘 / 거래 될 만한 것만 골라줘", or pastes a batch of subject lines and senders.
---

# 메일함 선별 — 거래 가능성 있는 것만

Homedant USA로 들어오는 영문 메일 중 **해외 매출로 이어질 수 있는 것만**
골라낸다. 전부 번역하지 않는다. 대부분은 읽을 가치가 없고, 전부 읽으면
진짜가 묻힌다.

## 어디서 메일을 읽나

| 방법 | 조건 |
| --- | --- |
| Microsoft 365 커넥터 (`outlook_email_search`) | claude.ai에서 연결되어 있어야 함 |
| 사용자가 붙여 넣은 목록 | 발신자 · 제목 · 날짜만 있어도 1차 선별 가능 |
| Outlook에서 내보낸 CSV | 파일 경로를 받아 읽는다 |

커넥터가 없으면 지어내지 말고, 연결이 필요하다고 알린 뒤 붙여넣기
방식으로 진행한다. **메일함을 읽을 수 없는데 읽은 척하지 않는다.**

## 순서

### 1. 범위를 먼저 정한다
기간(기본: 최근 30일)과 대상을 확인한다. 수천 통을 한 번에 처리하려
하지 말고, 기간을 나눠 돌린다.

### 2. 검색으로 후보를 좁힌다
전체를 훑지 말고 `references/queries.md` 의 질의를 순서대로 돌린다.
거래 언어(RFQ, MOQ, purchase order, line review, container)와 전시회명이
가장 잘 걸린다.

### 3. 등급을 매긴다
`references/scoring.md` 기준으로 A · B · C 세 등급. 애매하면 B로 두고
C로 버리지 않는다. **놓친 바이어의 비용이 헛읽은 메일의 비용보다 크다.**

### 4. 표로 낸다

```
## A급 — 지금 답장 (3건)
| 날짜 | 발신 | 회사 | 무슨 건인가 | 왜 A급인가 |

## B급 — 확인 필요 (5건)
| 날짜 | 발신 | 회사 | 무슨 건인가 | 무엇이 불확실한가 |

## C급 — 무시 (41건)
유형별 건수만. 목록을 나열하지 않는다.
예) 물류 대행 영업 18, SEO·마케팅 영업 12, 소싱 에이전트 7, 사기 의심 2 …
```

C급은 **건수와 유형만** 낸다. 하나씩 설명하면 그게 다시 소음이 된다.
단, 사기 의심 건은 발신 주소와 이유를 반드시 밝힌다.

### 5. 넘긴다
A급 중 사용자가 고른 건은 `email` 스킬로 넘어가 전문 번역과 영문 답장
초안을 만든다. 선별 단계에서는 번역하지 않는다 — 등급과 한 줄 요약까지다.

## 지켜야 할 선

- **읽기만 한다.** 메일을 삭제·이동·스팸 처리하거나 답장을 대신 보내지 않는다.
  초안까지가 끝이고 보내는 것은 사용자다.
- C급 판정에 확신이 없으면 B로 올린다.
- 회사명·발신 주소·요청 내용을 추측으로 채우지 않는다. 메일에 없으면 빈칸.
- 메일 본문을 이 저장소에 저장하지 않는다. 공개 저장소이고, 상대의
  연락처와 거래 조건이 들어 있다. 남길 가치가 있는 건만 사용자가 요청할 때
  `content/emails/` 에 요약 형태로 남긴다.
