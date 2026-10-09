# 자료 업데이트 방법

에이전트는 두 개의 데이터 파일만 봅니다. 여기만 고치면 게시글, 이미지,
캘린더가 전부 따라 바뀝니다.

## 새 전시회

`src/homedant_linkedin/data/brand.json` 의 `trade_shows` 에 추가합니다.

```json
{
  "name": "NY NOW Winter 2027",
  "booth": "372",
  "booth_label": "Booth",
  "venue": "Javits Center, New York, NY",
  "start": "2027-02-07",
  "end": "2027-02-11",
  "hashtags": ["HOMEDANT", "NYNOW", "StorageSolutions", "KoreanMade", "B2B"]
}
```

넣는 즉시 D-30 / D-14 / D-7 / D-2 카운트다운과 전시 기간 게시글이
캘린더에 자동으로 자리를 잡습니다. `booth` 가 아직 없으면 `null` 로 두세요 —
부스 번호 없이 발행 가능한 문장으로 나갑니다.

**끝난 전시회는 지우지 마세요.** 종료일이 지나면 알아서 로테이션에서
빠지고, 기록으로 남습니다.

## 새 수상 · 언론 보도

`recognitions` 에 추가합니다. `posted_on` 은 **비워 두세요** — 비어 있으면
"수상했습니다" 발표문으로 나가고, 한 번 올린 뒤 그 날짜를 채워 넣으면
그 다음부터는 같은 글을 반복하지 않고 다른 각도로 다시 씁니다.

```json
{
  "name": "...",
  "award": "...",
  "org": "...",
  "event": "...",
  "venue": "...",
  "city": "...",
  "date": "2027-03-15",
  "posted_on": null,
  "thanks": ["..."],
  "hashtags": ["HOMEDANT", "...", "B2B"]
}
```

## 신규 제품

`src/homedant_linkedin/data/products.json` 에 추가합니다.

| 항목 | 필수 | 설명 |
| --- | --- | --- |
| `asin`, `sku`, `title`, `category`, `marketplace`, `url` | 필수 | Amazon 리스팅 정보 |
| `short_name` | 권장 | 문장에 들어갈 이름. 없으면 리스팅 제목을 잘라서 씁니다 |
| `audience` | 권장 | 누구를 위한 제품인지 (B2B 바이어 기준) |
| `highlights` | 권장 | 셀링포인트 3개. 이미지 불릿으로도 쓰입니다 |
| `retail_fit` | 선택 | 진열·팔레트·규격 관련 한 줄 |
| `segments` | 필수 | `["retail"]` / `["project"]` / 둘 다 |
| `image_url` | 권장 | 리스팅 대표 이미지. 게시 이미지에 들어갑니다 |

`segments` 가 필러를 결정합니다. 호텔·다세대 프로젝트용이면 `project`,
리테일 바이어용이면 `retail` 입니다.

## 완성 이미지 (A+ 콘텐츠 등)

`assets/creatives/<필러>/` 에 넣으면 그 이미지가 게시 이미지로 그대로
나갑니다. 필러 폴더는 `project` `retail` `manufacturing` `seasonal` `supply`
입니다. 자세한 내용은 [`assets/README.md`](../assets/README.md)를 보세요.

**용량이 큰 zip을 대화창에 올릴 수 없을 때:**

1. **Google Drive에 올리기** — 이미 연결돼 있어 제가 바로 읽습니다. 용량 제한
   걱정이 없고 가장 편합니다.
2. **GitHub 웹에서 직접 업로드** — `assets/creatives/<필러>/` 로 이동해
   Add file → Upload files
3. **이미지를 미리 줄여서 보내기** — 게시 이미지는 1200px 정사각형입니다.
   원본 2500px를 1200px로 줄이면 한 장에 2.5MB → 200KB 수준이 됩니다.

## 제품별 하중

하중은 모델마다 다르고 LiftBeam 장착 여부에 따라 달라집니다. 브랜드 공통
문구에는 상한만 쓰고, 개별 수치는 제품에 적습니다.

```json
"load_per_tier": "264 lb",
"load_total": "1,322 lb across five tiers"
```

기록된 제품만 게시글에 수치가 들어갑니다. 없으면 그 문장을 생략합니다.

## 브랜드 사실

`proof_points`, `capability`, `positioning`, `offer` 를 고치면 모든 게시글에
반영됩니다. **공개 저장소이므로 단가, 마진, 생산능력 같은 대외비는 넣지 마세요.**

## 고친 뒤

```bash
PYTHONPATH=src pytest
PYTHONPATH=src python -m homedant_linkedin calendar --until 2026-12-31
python scripts/build_calendar_page.py --until 2026-12-31 --out calendar.html
```

커밋해서 푸시하면 GitHub Actions 가 캘린더 페이지를 다시 만들고, 다음
발송분부터 새 내용이 적용됩니다.
