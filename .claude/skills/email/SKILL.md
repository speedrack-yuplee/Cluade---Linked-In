---
name: email
description: Translate an inbound English business email into Korean and draft the English reply for Homedant USA. Use whenever the user pastes an English email, forwards a buyer/distributor/logistics/trade-show message, asks what an email means or says "이 메일 해석해줘 / 답장 써줘", or writes a Korean reply that needs to go out in business English.
---

# 영문 메일 해석 · 답장 작성

Homedant USA Inc(작성자 Leo Lee, Global B2B Sales)로 들어오는 영문 메일을
해석하고, 보낼 수 있는 상태의 영문 답장을 만든다. 목적은 사용자가 매번
LLM 창을 새로 열어 회사 설명을 다시 붙여넣는 일을 없애는 것이다.

## 시작할 때 읽을 것

메일을 받으면 답을 쓰기 전에 다음을 읽는다.

| 파일 | 무엇을 얻나 |
| --- | --- |
| `src/homedant_linkedin/data/brand.json` | 회사명, 포지셔닝, proof points, 수상 이력, 참가 전시회 |
| `src/homedant_linkedin/data/products.json` | 제품별 ASIN/SKU/치수/하중/세그먼트 |
| `content/emails/facts.md` | 가격·MOQ·리드타임·결제조건 등 영업 조건 (사용자가 채워 넣는 파일) |
| `references/glossary.md` | 무역·리테일 용어 한영 대조, HANDiLOCK 등 고유어 표기 규칙 |
| `references/playbooks.md` | 메일 유형별 판단 기준과 답장 뼈대 |
| `references/style.md` | 문체 규칙과 서명 |
| `content/emails/` | 지난 메일 기록 — 같은 상대와의 이전 대화가 있으면 반드시 확인 |

`content/emails/facts.md` 가 없거나 항목이 비어 있으면, 그 항목은 답장에
지어내지 말고 **[확인 필요]** 로 표시한다.

## 출력 형식

사용자가 영문 메일을 붙여넣으면 아래 순서 그대로 답한다. 절대 순서를
바꾸거나 항목을 생략하지 않는다.

### 1. 한 줄 요약
누가, 무엇을, 언제까지 원하는지 한 문장.

### 2. 전문 번역
메일 전체를 한국어로 옮긴다. 문단·리스트·표를 원문 구조 그대로 유지하고,
가격·수량·날짜·품번은 숫자를 그대로 둔다. 직역이 어색한 관용 표현은
한국어 상용 표현으로 바꾸되, 조건이나 의무를 나타내는 문장(shall, subject to,
net 30, FOB 등)은 의미를 흐리지 말고 정확히 옮긴다.

### 3. 읽는 법
번역만으로는 안 보이는 것을 짚는다.

- 상대가 누구인가: 실제 바이어 / 유통사 / 중개인 / 마케팅 영업 / 스팸
- 진짜 요구사항과 숨은 전제 (예: "send your best price" = 이미 경쟁 견적을 받고 있다)
- 톤과 급한 정도, 답장 기한
- 위험 신호 — 선불 요구, 낯선 계좌 변경 안내, 도메인이 회사명과 다른 발신자,
  샘플만 무료로 받아가려는 패턴은 반드시 경고한다

### 4. 확인 필요
답장을 쓰기 위해 사용자만 아는 정보를 항목으로 묻는다. 없으면 "없음".
질문은 3개를 넘기지 않는다. 답을 기다리느라 초안을 미루지 말고,
가정을 표시한 초안을 함께 낸다.

### 5. 영문 답장 초안
`references/playbooks.md` 의 해당 유형 뼈대와 `references/style.md` 문체를
따른다. 그대로 복사해 보낼 수 있어야 한다. 제목 줄(Subject)을 포함한다.
확정되지 않은 값은 `[[MOQ 확인]]` 처럼 대괄호 두 개로 감싸 눈에 띄게 둔다.

### 6. 답장 한국어 대역
초안을 그대로 한국어로 옮긴다. 사용자가 보내기 전에 무슨 말을 하는지
확인할 수 있어야 하므로, 의역하지 말고 초안과 1:1로 대응시킨다.

### 7. 다음 단계
답장 이후 할 일이 있으면 짧게. (카탈로그 첨부, 샘플 발송, 캘린더 초대,
전시회 미팅 확정 등) 없으면 생략한다.

## 반대 방향 — 한국어로 쓴 내용을 영문 메일로

사용자가 한국어로 "이렇게 답해줘" 라고 쓰면, 3·4번을 건너뛰고
**영문 초안 + 한국어 대역**만 낸다. 사용자의 한국어를 직역하지 말고,
북미 B2B 메일에서 통하는 문장으로 다시 쓴다.

## 지켜야 할 선

- **없는 사실을 만들지 않는다.** 가격, MOQ, 리드타임, 재고 수량, 인증서,
  결제 조건은 `facts.md` 나 사용자 확인 없이는 절대 쓰지 않는다.
- 하중·치수·소재는 `products.json` 값을 그대로 쓴다. 반올림하거나 "약"을
  붙여 부풀리지 않는다.
- HANDiLOCK, LiftBeam 같은 자체 용어는 처음 나올 때 한 번 설명한다
  (`glossary.md` 참고). 상대는 이 단어를 모른다.
- 상대가 요구하지 않은 할인, 독점권, 납기 약속을 먼저 제시하지 않는다.
- 스팸이나 무의미한 영업 메일로 판단되면 답장 초안 대신 그 판단과 근거만 낸다.

## 기록

주고받은 메일 중 남길 가치가 있는 것은 `content/emails/` 에
`YYYY-MM-DD-상대-주제.md` 로 저장한다. 형식은 `content/emails/_TEMPLATE.md`.
사용자가 요청할 때만 저장하고, 저장 여부를 매번 묻지는 않는다.
같은 상대에게서 다시 메일이 오면 이 기록을 먼저 읽고 문맥을 이어 간다.
