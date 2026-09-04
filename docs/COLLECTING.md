# 성과 데이터 자동 수집

LinkedIn 수치는 **이엽님 PC에서만** 모을 수 있습니다. opencli가 이 컴퓨터의
크롬 세션을 쓰기 때문입니다. 클라우드 세션은 linkedin.com 에 접근할 수
없고, 이 스크립트가 푸시한 것을 읽습니다.

## 한 번 해두면 되는 준비

저장소를 PC에 클론합니다.

```powershell
cd $env:USERPROFILE\Documents
git clone https://github.com/speedrack-yuplee/Cluade---Linked-In.git
```

## 수동 실행

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Documents\Cluade---Linked-In\scripts\collect_linkedin.ps1"
```

끝나면 `claude/linkedin-metrics` 브랜치에 푸시됩니다.

### 화면에 안 뜨게 하기

기본값이 `-Window background` 입니다. 크롬 탭은 열리지만 **앞으로 나오지
않습니다.** 다른 창에서 일하는 동안 돌려도 됩니다.

opencli 버전이 이 값을 안 받으면 경고를 한 줄 찍고 예전처럼 화면에 띄워서
다시 시도합니다. 그럴 때는 opencli 를 업데이트하거나, 아래 자동 실행으로
자리에 없는 시간에 돌리세요.

```powershell
# 확인용 — 이 명령이 --window 값으로 무엇을 받는지 보여줍니다
opencli.cmd linkedin posts --help
```

**완전히 안 보이게 하려면 자동 실행이 답입니다.** 아래 스케줄러 등록은
`-WindowStyle Hidden` 으로 돌기 때문에 PowerShell 창도 뜨지 않습니다.

## 자동 실행 (주 1회)

작업 스케줄러에 등록합니다. PowerShell을 **관리자 권한으로** 열고:

```powershell
$script = "$env:USERPROFILE\Documents\Cluade---Linked-In\scripts\collect_linkedin.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 7am
Register-ScheduledTask -TaskName "LinkedIn metrics" -Action $action -Trigger $trigger
```

월요일 오전 7시에 돕니다. 출근 전이라 화면을 뺏길 일이 없고, 게시 요일
(월·수·금)보다 앞이라 그 주 콘텐츠를 정하기 전에 지난주 성과가 들어옵니다.

PC가 꺼져 있어 걸렀다면 켠 다음 따라잡게 하려면:

```powershell
Set-ScheduledTask -TaskName "LinkedIn metrics" `
    -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)
```

**크롬이 로그인된 상태여야 합니다.** 로그아웃되면 스크립트가 실패합니다.
확인:

```powershell
opencli.cmd linkedin whoami
```

## 저장되는 형식

스크립트는 opencli 원본을 그대로 쓰지 않습니다. `content/reference/README.md`
가 정한 형식으로 바꿔서 저장합니다.

| README 항목 | 어디서 오나 |
| --- | --- |
| `posted_at` `impressions` `reactions` `comments` `reposts` `url` | opencli 그대로 |
| `hook` | 본문 첫 줄 |
| `hashtags` | 본문에서 `#단어` 추출 |
| `tagged` | opencli 의 `mentions` |
| `has_image` | `media` 유무 |
| `pillar` `topic` | 비워둠 — 본문 보고 나중에 분류 |

`raw_text` 는 버립니다. 본문(`body`)과 같은 내용인데, opencli 가 줄바꿈과
따옴표를 이스케이프하지 않아 **JSON 을 깨뜨립니다.** 파싱 전에 줄 단위로
걷어냅니다.

## 누구를 볼지 정하기

`src/homedant_linkedin/data/watchlist.json` 에 있습니다. 세 종류입니다.

| 항목 | 수집 방식 |
| --- | --- |
| `people` | `profile_url` 이 있으면 그 사람 게시글 10개를 직접 수집 |
| `companies` | **직접 수집 불가.** LinkedIn에서 팔로우하시면 `timeline` 에 섞여 들어옵니다 |
| `search_terms` | 사람을 새로 찾을 때 쓸 검색어 메모. 자동 실행되지 않습니다 |

`profile_url` 이 비어 있으면 **건너뛰고 이름만 알려줍니다.** 핸들을 추측해서
엉뚱한 사람을 긁는 것보다 낫습니다. 채우시려면 그 사람 프로필에 들어가
주소창의 `https://www.linkedin.com/in/핸들/` 을 그대로 붙여넣으면 됩니다.

**회사는 팔로우가 곧 수집입니다.** opencli는 회사 페이지 게시글을 읽지
못합니다(`posts requires a /in/<handle>/ profile URL`). 팔로우해 두시면 그
회사 글이 피드에 뜨고, `timeline` 이 그걸 가져옵니다.

## 노출 수는 남의 글에서 안 보입니다

LinkedIn은 노출을 작성자에게만 보여줍니다. 남의 게시글은 **반응·댓글**로만
비교됩니다. 절대 도달은 알 수 없습니다.

## 푸시된 뒤

`metrics.yml` 워크플로우가 자동으로 돌면서 텔레그램으로 두 가지를 보냅니다.

1. **내 게시글 순위** — 노출순 상위 5개, 주제별 평균 노출
2. **다른 계정 동향** — 반응이 붙은 글, 자주 나온 주제, 자주 쓰인 단어

2번이 콘텐츠 소재가 됩니다. 예를 들어 "관세·소싱"이 계속 상위로 올라오면,
그 주 공급·물류 게시글을 그 각도로 쓰면 됩니다.

## 안 될 때

| 증상 | 원인 |
| --- | --- |
| `opencli did not return JSON` | 크롬 로그아웃, 또는 확장 미연결 (`opencli.cmd doctor`) |
| 수치가 전부 0 | 어댑터가 셀렉터를 못 찾음. `opencli adapter eject linkedin` 후 수정 |
| 한글이 `?쇰볗` 처럼 깨짐 | `[Console]::OutputEncoding` 이 설정 안 됨. 스크립트를 최신본으로 pull |
| `no change since the last run` | 정상입니다. 지난번과 같은 데이터라 커밋하지 않았습니다 |
