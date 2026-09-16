# 성과 데이터 보관함

LinkedIn 게시글의 **실제 노출·반응 수치**를 여기에 모읍니다. 지금 콘텐츠
캘린더의 필러 순서는 화면 캡처 3장에 근거하고 있습니다. 표본이 얇습니다.

## 넣는 형식

`content/reference/posts.json` — 배열, 게시글 하나가 객체 하나.

```json
[
  {
    "posted_at": "2026-04-15",
    "pillar": "recognition",
    "topic": "Retailers' Choice Awards winner at the National Hardware Show",
    "url": "https://www.linkedin.com/posts/...",
    "impressions": 698,
    "reactions": 10,
    "comments": 8,
    "reposts": 0,
    "hook": "We are proud to share that HOMEDANT has been selected as a ...",
    "hashtags": ["HOMEDANT", "RetailersChoice", "NHPA"],
    "tagged": ["North American Hardware and Paint Association (NHPA)"],
    "has_image": true
  }
]
```

| 항목 | 필수 | 비고 |
| --- | --- | --- |
| `posted_at` | 필수 | `YYYY-MM-DD` |
| `impressions` | 필수 | 이게 없으면 데이터의 의미가 없습니다 |
| `reactions`, `comments`, `reposts` | 권장 | |
| `hook` | 권장 | 첫 문장. 훅 패턴 분석에 씁니다 |
| `hashtags`, `tagged` | 권장 | 도달의 상당 부분이 여기서 나옵니다 |
| `pillar` | 선택 | 비워두면 제가 본문 보고 분류합니다 |

`0` 과 `null` 은 다릅니다. **읽지 못한 값은 `null`** 로 두세요. `0` 으로
채우면 "노출이 없었다"로 읽혀 분석이 틀어집니다.

## 수집 방법

`opencli linkedin posts` 가 노출·반응을 전부 `0` 으로 반환하는 문제가
있습니다(2026-09 기준). 어댑터가 그 영역을 못 읽습니다.

- 어댑터를 고치려면 `opencli adapter eject linkedin` 후 셀렉터 수정
- 고치기 전까지는 LinkedIn 화면에서 직접 옮겨 적는 편이 빠릅니다

수집은 **이엽님 PC의 로컬 Claude 세션**에서만 가능합니다. 클라우드 세션은
linkedin.com 에 접근할 수 없습니다.

## 쌓이면 할 수 있는 것

- 필러별 평균 노출 → 지금 배분(제3자 인증 우선)이 맞는지 검증
- 훅 유형별 성과 → 질문형 / 선언형 / 뉴스형 중 무엇이 먹히는지
- 해시태그·기관 태그의 도달 기여도
- 이미지 유무의 차이
