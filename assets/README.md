# 브랜드 · 행사 이미지 자산

여기에 파일을 넣으면 게시 이미지에 자동으로 합성됩니다. 없으면 글자만으로
된 레이아웃으로 대체되므로, 비어 있어도 발송은 정상 동작합니다.

| 경로 | 쓰이는 곳 | 권장 |
| --- | --- | --- |
| `assets/logo.png` | 모든 게시 이미지 좌상단 | 가로 800px 이상, 배경 투명 PNG |
| `assets/shows/<slug>.png` | 해당 전시회 게시글 | 정사각형에 가깝게, 배경 투명 PNG |
| `assets/awards/<slug>.png` | 해당 수상 게시글 | 수상 배지, 배경 투명 PNG |

`<slug>`는 전시회·수상 이름을 소문자로 바꾸고 공백을 `-`로 이은 것입니다.

- `High Point Market` → `assets/shows/high-point-market.png`
- `NY NOW Summer 2026` → `assets/shows/ny-now-summer-2026.png`
- `Retailers' Choice Awards Winner` → `assets/awards/retailers-choice-awards-winner.png`

정확한 파일명은 이 명령으로 확인할 수 있습니다:

```bash
PYTHONPATH=src python -m homedant_linkedin assets
```

## 저작권 주의

전시회 로고와 수상 배지는 **주최측 상표**입니다. 임의로 웹에서 내려받아
쓰지 마시고, 주최측이 출품사·수상사에게 제공하는 공식 홍보 키트의 파일만
넣으세요.

- **High Point Market** — ANDMORE 출품사 포털의 exhibitor marketing kit
  (담당: Angie Carter)
- **Retailers' Choice / NHPA** — 수상 통보 메일에 동봉된 winner badge 키트

키트에는 보통 사용 규정(최소 여백, 변형 금지 등)이 함께 옵니다. 그 규정이
이 문서보다 우선합니다.
