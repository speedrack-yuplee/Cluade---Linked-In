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

크롬 창이 뜨고 스크롤이 일어납니다. **끝날 때까지 건드리지 마세요.**
끝나면 `claude/linkedin-metrics` 브랜치에 푸시됩니다.

## 자동 실행 (주 1회)

작업 스케줄러에 등록합니다. PowerShell을 **관리자 권한으로** 열고:

```powershell
$script = "$env:USERPROFILE\Documents\Cluade---Linked-In\scripts\collect_linkedin.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am
Register-ScheduledTask -TaskName "LinkedIn metrics" -Action $action -Trigger $trigger
```

월요일 오전 8시에 돕니다. 게시 요일(월·수·금)보다 앞이라, 그 주 콘텐츠를
정하기 전에 지난주 성과가 들어옵니다.

**크롬이 로그인된 상태여야 합니다.** 로그아웃되면 스크립트가 실패합니다.
확인:

```powershell
opencli.cmd linkedin whoami
```

## 푸시된 뒤

`metrics.yml` 워크플로우가 자동으로 돌면서 순위 요약을 텔레그램으로
보냅니다. 아무것도 안 하셔도 됩니다.

## 안 될 때

| 증상 | 원인 |
| --- | --- |
| `opencli did not return JSON` | 크롬 로그아웃, 또는 확장 미연결 (`opencli.cmd doctor`) |
| 수치가 전부 0 | 어댑터가 셀렉터를 못 찾음. `opencli adapter eject linkedin` 후 수정 |
| `no change since the last run` | 정상입니다. 지난번과 같은 데이터라 커밋하지 않았습니다 |
