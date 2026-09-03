# 링크드인 운영 지침

이 저장소를 보는 **모든 에이전트와 사람이 공유하는 문맥**입니다. 링크드인
작업을 시작하기 전에 이 문서를 먼저 읽으면, 같은 설명을 다시 하지 않아도
됩니다.

계정 하나를 여러 대화가 나눠 다루기 때문에, 여기 적힌 판단 근거와 금지
사항은 개인 취향이 아니라 **실측과 약관에서 나온 것**입니다.

---

## 1. 이 계정에서 무엇이 통하는가

`content/posts/` 의 실적이 답을 이미 갖고 있습니다.

| 게시물 | 노출 | 반응 |
| --- | ---: | ---: |
| National Hardware Show 수상 (NHPA Retailers' Choice) | **698** | 10 |
| RangeMe Award Winner Collection | 42 | 1 |
| 호텔·주거용 오픈 워드로브 | 18 | — |

**제3자 검증이 제품 소개보다 15~35배**입니다. 이 비율이 이 계정의 모든
결정을 지배합니다.

- 사이클마다 **수상·인증·전시 수상 이력을 앞세웁니다**
- 제품 자랑은 그 뒤에 붙입니다
- 리드 발굴도 같은 논리 — 무작정 명단을 긁기보다 **NHPA 회원사처럼 이미
  우리를 인정한 판에서 확장**하는 쪽이 전환이 높습니다

파는 것은 **한국산 무볼트 스틸 선반**이고, 사는 사람은 하드웨어·홈 리테일
바이어, 유통사, 호스피탈리티 스펙서, 멀티패밀리 개발사입니다.

---

## 2. 링크드인을 읽는 법 — OpenCLI

링크드인에는 공개 트렌딩 피드가 없습니다. 글을 읽으려면 로그인 세션이
필요하고, 그 통로가 [OpenCLI](https://github.com/jackwener/opencli) 입니다.

### 구조

```
윈도우 PC ─ 크롬 로그인 세션
              ↕ (Browser Bridge 확장)
           opencli 데몬 (포트 19825)
              ↕
           opencli.cmd linkedin <명령>
```

크롬에 이미 로그인된 세션을 CDP로 빌려 쓰므로 **API 키가 필요 없습니다.**

### ⚠️ 클라우드 세션에서는 안 됩니다

Claude Code 웹/클라우드 컨테이너는 `linkedin.com` 이 네트워크 정책에
막혀 있고(403), 브라우저 세션도 없습니다. **OpenCLI 명령은 사람이 자기
PC에서 실행하고, 결과 JSON을 에이전트에게 전달하는 구조**입니다.

에이전트가 직접 링크드인을 읽는다고 가정하지 마세요.

### 윈도우 환경 주의점

| 증상 | 원인과 해결 |
| --- | --- |
| `opencli.ps1 파일을 로드할 수 없습니다` | PowerShell 실행 정책. **`opencli.cmd`** 로 호출하거나 `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `python3` 가 MS 스토어를 엶 | 스토어 별칭임. **`py -3`** 를 쓸 것 |
| `Activate.ps1` 구문 오류 | `& "$env:USERPROFILE\.agent-reach-venv\Scripts\Activate.ps1"` — 호출 연산자 `&` 와 따옴표 필요 |
| `Extension: not connected` | 크롬이 실행 중인지 확인 → `opencli.cmd daemon restart` |

`daemon restart` 출력에 `disconnect N browser profile(s)` 가 보이면 확장은
이미 붙어 있던 것입니다. 재연결에 몇 초 걸립니다.

---

## 3. 자주 쓰는 명령

링크드인 어댑터에는 24개 명령이 있습니다. 읽기 위주로 씁니다.

```powershell
opencli.cmd linkedin whoami                              # 로그인 계정 확인
opencli.cmd linkedin posts --limit 20 -f json            # 내 게시물 + 지표
opencli.cmd linkedin profile-analytics -f json           # 노출·조회수·검색 노출
opencli.cmd linkedin timeline --limit 100 -f json        # 홈 타임라인
opencli.cmd linkedin company "<회사>" -f json             # 회사 정보
```

### 인자

| 명령 | 인자 | 기본값 |
| --- | --- | --- |
| `posts` | `profile-url`(선택), `limit`(1–100) | URL 생략 시 **본인**, 20 |
| `post-analytics` | 같음 | 30 |
| `profile-analytics` | `profile-url`(선택) | 본인 |
| `timeline` | `limit`(최대 100) | 20 |
| `company` | `company`(필수) — 짧은 이름 / `/company/<name>` / 전체 URL | — |

`profile-url` 이 선택이라 **생략하면 `/in/me/`**, 즉 로그인된 본인입니다.
다른 사람 URL을 넣으면 그 사람 게시물을 읽습니다.

### 반환 필드

`posts` 와 `timeline` 모두 본문과 참여 지표를 함께 줍니다.

```
author, author_url, posted_at, text, raw_text,
reactions, comments, reposts, media_urls, url
```

초안 작성에 필요한 재료가 다 들어 있습니다.

---

## 4. 경쟁사 게시물을 모으는 법

`company` 는 회사 **정보**(업종·규모·본사·팔로워)만 주고, **회사 페이지
게시물을 뽑는 명령은 없습니다.** `posts` 는 개인 프로필(`/in/`) 전용입니다.

우회로는 `timeline` 입니다. 반환 필드에 `author` 와 `author_url` 이 있어
**작성자가 회사든 개인이든 다 잡힙니다.**

```
① 크롬에서 경쟁사·업계 회사 페이지를 팔로우 (사람이 1회)
② opencli.cmd linkedin timeline --limit 100 -f json > timeline.json
③ author 로 필터링해 해당 회사 게시물만 추출
```

링크드인이 의도한 정상 사용 방식이라 계정 위험이 없습니다.

---

## 5. 리드 발굴 경로

**한도를 소모하지 않는 순서**로 좁힙니다.

```powershell
# ① 채용 공고에서 회사 발견 — 그 카테고리를 키우는 중이라는 신호
opencli.cmd indeed search "hardlines buyer" -f json
opencli.cmd indeed search "category manager storage organization" -f json

# ② 회사 규모·업종 확인 (한도 소모 없음)
opencli.cmd linkedin company "<회사>" -f json

# ③ 담당자가 무엇에 관심 있는지
opencli.cmd linkedin posts "https://www.linkedin.com/in/<핸들>/" -f json
```

`google search` 도 저평가돼 있습니다. 전시회 출품사 디렉터리나 바이어
명단은 대부분 웹에 공개돼 있습니다.

### `people-search` 는 아껴 쓸 것

```
limit 최대 10명
각 호출이 링크드인 월간 상업적 이용 한도(CUL)를 소모
```

어댑터 매니페스트에 명시된 경고입니다. 한도를 넘기면 **월말까지 검색이
막힙니다.** 회사명을 이미 알면 `company` 를 쓰세요.

---

## 6. 하지 말 것

`connect`(연결 요청), `safe-send`(메시지 발송), `salesnav-message`(InMail)
같은 `[write]` 명령이 존재합니다. **쓰지 않습니다.**

1. **링크드인 약관이 자동 메시지 발송을 금지**합니다. 읽기와는 비교가 안
   되는 제재 위험입니다
2. 미국 B2B 콜드 이메일은 **CAN-SPAM** 적용 대상입니다
3. 이 계정은 영업 자산입니다. 막히면 NY NOW 부스에서 만난 바이어와의
   연결 통로가 사라집니다
4. **효과가 낮습니다** — 1절의 698 대 42가 그 증거입니다. 대량 콜드
   메시지는 자기 홍보의 극단입니다

### 대신 반자동으로

```
자동: 타깃 발굴 → ICP 점수 → 개인화 초안 작성
수동: 사람이 읽고 다듬어 직접 발송
```

제재 위험이 없고 전환은 더 높습니다. 하루 5~10명이면 사람이 보내도 부담이
없고, NHPA 수상 이력을 상대별로 녹이는 건 자동 발송으로는 못 합니다.

이메일 주소는 링크드인에서 **1촌에게만** 공개됩니다. 이메일 추출 명령은
없습니다.

---

## 7. `trends` — 업계 매체 읽기

링크드인 트렌딩이 없으니, **바이어가 읽는 매체**를 대신 읽습니다.

```bash
PYTHONPATH=src python -m homedant_linkedin trends --days 30
PYTHONPATH=src python -m homedant_linkedin trends --days 7 --json
```

매체 13곳(하드웨어·수납을 앞에), 키워드 8테마 59개. 목록은
`src/homedant_linkedin/data/feeds.json` 에 있고, 매체나 키워드 추가는
**코드가 아니라 이 JSON을 고칩니다.**

답하지 않는 피드는 이름과 함께 표시되고 건너뜁니다. **전부 실패했을 때만**
종료 코드 1입니다 — 그때가 조용한 주가 아니라 네트워크 문제입니다.

읽기 전용 컨테이너에서는 매체 호스트가 차단돼 결과가 비어 있을 수
있습니다. 정상 네트워크에서 돌려야 의미가 있습니다.

---

## 8. 아마존 바이어 메시지 (참고)

링크드인은 아니지만 같은 파이프라인에 얹을 수 있어 적어둡니다.

- **SP-API에는 바이어 메시지를 읽는 엔드포인트가 없습니다.** Messaging
  API v1은 발송 전용입니다
- 아마존은 바이어 메시지 사본을 **셀러의 알림 이메일로 전달**합니다
  (`@marketplace.amazon.com` 릴레이)
- 따라서 **메일함을 읽는 것**이 유일하게 약관에 안전한 읽기 경로입니다.
  셀러센트럴 화면 자동화는 계정 정지 위험이 매출에 직결됩니다
- OpenCLI `amazon` 어댑터는 **구매자 관점 공개 페이지 전용**입니다
  (상품·검색·베스트셀러). 셀러센트럴 명령은 없습니다

발송은 `scripts/send_telegram.py` 를 그대로 재사용하면 됩니다.

---

## 9. 세션 간 문맥 공유

대화끼리 직접 메시지를 주고받는 기능은 현재 열려 있지 않습니다. Cowork
세션은 조회 목록에 잡히지 않고, 클라우드 세션에 보내는 메시지는 단방향입니다.

**이 저장소가 공유 메모리입니다.** 새로 알아낸 것은 이 문서에 적어
커밋하세요. 다음 대화가 그대로 읽습니다.
