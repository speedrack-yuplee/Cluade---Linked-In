# 브랜드 · 행사 이미지 자산

여기에 파일을 넣으면 게시 이미지에 자동으로 합성됩니다. 없으면 글자만으로
된 레이아웃으로 대체되므로, 비어 있어도 발송은 정상 동작합니다.

| 경로 | 쓰이는 곳 | 권장 |
| --- | --- | --- |
| `assets/logo.png` | 모든 게시 이미지 좌상단 | 가로 800px 이상, 배경 투명 PNG |
| `assets/shows/<slug>.png` | 해당 전시회 게시글 | 정사각형에 가깝게, 배경 투명 PNG |
| `assets/awards/<slug>.png` | 해당 수상 게시글 | 수상 배지, 배경 투명 PNG |
| `assets/products/<ASIN>.jpg` | 해당 제품이 들어가는 모든 게시글 | 정사각형에 가깝게, 1000px 이상 |

`<slug>`는 전시회·수상 이름을 소문자로 바꾸고 공백을 `-`로 이은 것입니다.

- `High Point Market` → `assets/shows/high-point-market.png`
- `NY NOW Summer 2026` → `assets/shows/ny-now-summer-2026.png`
- `Retailers' Choice Awards Winner` → `assets/awards/retailers-choice-awards-winner.png`

정확한 파일명은 이 명령으로 확인할 수 있습니다:

```bash
PYTHONPATH=src python -m homedant_linkedin assets
```

## 완성된 A+ 이미지 (`assets/creatives/`)

Amazon A+ 콘텐츠처럼 **이미 완성된 브랜드 이미지**는 여기에 필러 이름 폴더로
넣습니다. 넣으면 그 이미지가 게시 이미지로 **그대로** 나갑니다 — 제가 만드는
템플릿보다 낫기 때문입니다.

```
assets/creatives/project/*.jpg        프로젝트 솔루션
assets/creatives/retail/*.jpg         리테일 적합성
assets/creatives/manufacturing/*.jpg  Made in Korea
assets/creatives/seasonal/*.jpg       Q4 시즌
assets/creatives/supply/*.jpg         공급 · 물류
```

한 폴더에 여러 장 넣으면 주 단위로 돌아가며 쓰입니다. 정사각형 1200px
이상을 권합니다.

**전시회·수상 게시글은 예외입니다.** "D-7", "Space M-1007" 같은 숫자가
매번 달라져야 해서 완성 이미지로 대체할 수 없고, 항상 새로 그립니다.

현재 상태는 이 명령으로 확인합니다:

```bash
PYTHONPATH=src python -m homedant_linkedin assets
```

## 제품 사진

제품 사진은 자사 자산이므로 권리 문제가 없습니다. `assets/products/` 에
ASIN 이름으로 넣으면 Amazon 리스팅 컷 대신 그 파일이 쓰입니다.

```
assets/products/B0GWGZF1F3.jpg
assets/products/B0D8VQS2BK.png
```

`.jpg` `.jpeg` `.png` `.webp` 를 지원합니다. 파일이 없으면 리스팅 이미지를
자동으로 받아 씁니다.

**연출 사진을 권합니다.** 흰 배경 제품컷보다, 실제 공간에 놓인 사진
(콘도 침실의 오픈 워드로브, 공구를 올린 창고 선반 등)이 피드에서 훨씬 잘
읽힙니다. 기존 게시글에 쓰셨던 이미지들이 여기 적합합니다.

## 저작권 주의

전시회 로고와 수상 배지는 **주최측 상표**입니다. 임의로 웹에서 내려받아
쓰지 마시고, 주최측이 출품사·수상사에게 제공하는 공식 홍보 키트의 파일만
넣으세요.

- **High Point Market** — 공식 브랜드 키트 적용 완료
  (`assets/shows/high-point-market.png`)

  브랜드 가이드북(HPMKT Brand Guidelines) 규정에 따라 고른 파일입니다:

  | 규정 | 적용 |
  | --- | --- |
  | 가로형(horizontal) 또는 세로형 락업 우선 사용 | 가로형 락업 |
  | 흰색·밝은 배경에는 **black + grey 이중색이 기본** | Black Grey |
  | 가로형 최소 높이 50px | 렌더링 시 100px |
  | 로고 주변에 아이콘 하나 너비만큼 여백 | 상하 50px+, 좌우 110px |
  | ® 기호 제거 금지 | Registered 버전 사용 |
  | 왜곡·효과·복잡한 배경 금지 | 비율 유지, 흰 패널 위 배치 |

  **가이드북 PDF는 저장소에 넣지 않았습니다** — HPMKT 저작물이고 이 저장소는
  공개입니다. 로고 파일 자체는 출품사 홍보용으로 제공된 것이라 파이프라인에
  필요한 한 장만 넣었습니다.
- **Retailers' Choice / NHPA** — 수상 통보 메일에 동봉된 winner badge 키트

키트에는 보통 사용 규정(최소 여백, 변형 금지 등)이 함께 옵니다. 그 규정이
이 문서보다 우선합니다.
