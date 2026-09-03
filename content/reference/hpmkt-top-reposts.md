# High Point Market 검색 — 퍼감 상위 게시글

수집일 2026-09-03. `opencli browser` 로 LinkedIn 콘텐츠 검색 화면을
직접 읽었습니다.

검색어 세 개를 각각 끝까지 스크롤한 뒤 합치고 중복을 제거했습니다.

| 검색어 | 결과 |
| --- | --- |
| `#HPMKT` | 3 |
| `High Point Market` | 3 |
| `#HighPointMarket` | 3 |
| 중복 제거 후 | 7 |

## 퍼감 상위 5

| # | 작성자 | 퍼감 | 반응 | 댓글 | 본문 첫 두 줄 | 게시물 URL |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [Lars Vestergaard](https://www.linkedin.com/in/larsvestergaard/) | 2 | 30 | 7 | Lene Simon & I are Extrem(ly) excited to announce that we've partnered up with FFL Brands, also known as Furniture For Life, as their sales representa… | null |
| 2 | [Craftmaster Furniture](https://www.linkedin.com/company/craftmaster-furniture/posts/) | 2 | 20 | 1 | We’re excited to be open and ready to share our newest introductions with you. Be sure to stop by and see us—ample parking is available, and we offer… | null |
| 3 | [Intiaro](https://www.linkedin.com/company/intiaro/posts/) | 2 | 9 | 1 | High Point Market is all about one big question: What’s new? New collections. New fabrics. New finishes. | null |
| 4 | [Deco Marché](https://www.linkedin.com/company/decomarche/posts/) | null | 32 | 3 | Your next best seller might already be waiting for you. 👀 Two Markets. Thousands of products to discover. Plenty of opportunities to find the pieces t… | null |
| 5 | [High Point Market Authority](https://www.linkedin.com/company/high-point-market-authority/posts/) | null | 10 | 1 | For retailers, High Point Market offers something no catalog or website can replicate: the opportunity to experience complete collections in person an… | null |

## 읽어야 할 주의사항

**퍼감 `null` 은 0이 아닙니다.** LinkedIn 은 퍼감이 없을 때 그 자리에
아무것도 그리지 않습니다. 카운터가 화면에 없었다는 뜻이고, 실제로 0인지
표시만 안 된 것인지 이 화면만으로는 구분할 수 없습니다. 그래서 0으로
채우지 않았습니다. 실제 숫자가 찍힌 글은 7개 중 3개뿐이고 셋 다 퍼감 2라,
상위 3위는 반응 수로 순서를 매겼습니다.

**게시물 URL 이 대부분 `null` 인 이유.** 검색 결과 화면은 LinkedIn 이
새로 만든 UI 라서 클래스명이 전부 해시되어 있고, 카드 DOM 어디에도
게시물 URN 이나 퍼머링크가 없습니다. 활동 페이지 카드에 있는
`data-urn` 이 검색 카드에는 없습니다. 게시물 관리 메뉴(`…`)의
"링크 복사"도 열어봤지만 메뉴가 DOM 에 노출되지 않았습니다.
작성자 링크는 카드에 있어서 작성자 이름에 걸어 두었습니다.
7건 중 URN 을 아는 것은 Leo Lee 님 본인 글 하나뿐인데(활동 페이지에서
따로 수집), 그 글은 상위 5위 안에 들지 않아 표에는 채울 URL 이 없습니다.

**결과가 9건뿐인 것도 화면 그대로입니다.** 세 검색 모두 3건에서 끝나고
바로 푸터가 나옵니다. 스크롤을 더 내려도 추가 로딩이 없습니다.

## 전체 7건

| 작성자 | 퍼감 | 반응 | 댓글 | 걸린 검색어 |
| --- | --- | --- | --- | --- |
| Lars Vestergaard | 2 | 30 | 7 | `High Point Market` |
| Craftmaster Furniture | 2 | 20 | 1 | `#HPMKT` |
| Intiaro | 2 | 9 | 1 | `#HPMKT` |
| Deco Marché | null | 32 | 3 | `#HighPointMarket` |
| High Point Market Authority | null | 10 | 1 | `High Point Market` |
| Melissa Van Hise | null | 2 | null | `High Point Market`, `#HighPointMarket` |
| Leo Lee | null | null | null | `#HPMKT`, `#HighPointMarket` |
