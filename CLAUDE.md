# HOMEDANT USA — LinkedIn AI 에이전트

Homedant USA Inc의 링크드인 게시물을 계획·작성·검수하는 저장소입니다.
파는 것은 **한국산 무볼트 스틸 선반**, 읽는 사람은 하드웨어·홈 리테일
바이어, 유통사, 호스피탈리티 스펙서, 멀티패밀리 개발사입니다. B2B이므로
글은 아마존 구매자가 아니라 이들에게 쓰고, 리스팅 링크 대신 대화를
요청하며 끝냅니다.

## The company OneDrive is read-only. No exceptions.

The Microsoft 365 connector reaches the Speedrack OneDrive, including
`01_사진 ~ 05_본사 관련 자료`. Those are the company's master design files and
photography. There is no second copy.

Having write permission is not permission. In that drive you may only:

- list folders (`sharepoint_folder_search`, `read_resource`)
- open and look at files (`read_resource`)
- search by name or content (`sharepoint_search`)

You may **never** delete, overwrite, move, rename, or create anything there.
That means `sharepoint_update_file`, `sharepoint_upload_file`,
`sharepoint_delete_item`, `sharepoint_move_item`, `sharepoint_rename_item`,
`sharepoint_copy_item` and `sharepoint_create_folder` are off limits for this
drive, whatever the reason and however safe the change looks.

If a change there seems necessary, say so and let Leo do it himself.

## The working copy of the photography

`scripts/sync_photos.ps1` runs on Leo's PC. It reads the master library and
writes downscaled copies to his own OneDrive, under
`해외영업3파트/업무/@업무/자동화/Image` — a different drive from the master
library, and his to write to. Read that folder freely; it is what the picture
for a post is chosen from.

Writing there is still the script's job, not the connector's. The scheduled
job on GitHub Actions cannot reach OneDrive at all, so a photo that actually
ships in a post is copied into `assets/` in this repository. The original in
the master library stays where it is, untouched.

## Confidential material

The repository is public. Pricing, margins, container volumes, competitor
analysis and buyer terms from the Lowe's vendor deck are never committed and
never published. Show organisers' logos and award badges go in only from the
official exhibitor or winner kit.

## 링크드인 작업 전에 읽을 것

**`docs/LINKEDIN_PLAYBOOK.md`** — 이 저장소를 보는 모든 대화가 공유하는
문맥입니다. 링크드인을 읽는 법(OpenCLI), 경쟁사 게시물 수집, 리드 발굴
경로, 하지 말아야 할 것과 그 근거가 들어 있습니다. 링크드인 관련 작업은
여기부터 읽고 시작하세요.

새로 알아낸 것은 그 문서에 적어 커밋하세요. **세션끼리 직접 대화할 수
없으므로, 이 저장소가 유일한 공유 메모리입니다.**

## 이 계정의 핵심 사실

수상 게시물 698 노출 vs 제품 게시물 42·18 — **제3자 검증이 제품 소개보다
15~35배**입니다. 사이클마다 수상·인증을 앞세우고 제품은 뒤에 붙입니다.

## 자료 수정

에이전트는 데이터 파일만 봅니다. 수정 방법은 `docs/UPDATING.md`.

| 파일 | 내용 |
| --- | --- |
| `src/homedant_linkedin/data/brand.json` | 브랜드, 전시회, 수상 |
| `src/homedant_linkedin/data/products.json` | 제품 카탈로그 |
| `src/homedant_linkedin/data/feeds.json` | `trends` 가 읽는 매체와 키워드 |

## 개발

```bash
pip install -e ".[dev]"
PYTHONPATH=src python -m pytest tests/ -q
```

발행 전 검수(`validators.py`)를 우회하지 마세요. 링크드인 글자 수 한도와
근거 없는 표현을 막는 장치입니다.
