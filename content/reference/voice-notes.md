# 자연스러움 점검 — 2026-09-08

이엽님 요청: "사람이 쓴 것 같은지 모르겠으면 다른 계정 게시글이나 자료를 보고
가져와라." LinkedIn 자체는 차단돼 있어(조직 정책), 검색으로 확인 가능한
범위에서 봤다.

## 확인한 것

**1. 첫 줄 길이 — 이미 맞게 하고 있었다.**
LinkedIn은 데스크톱에서 약 210자를 넘으면 "…더 보기"로 접는다. 이 시스템은
이미 `MAX_HOOK_CHARS = 210` 을 검증기에서 강제하고 있다 — 고칠 게 없었다.

**2. 잘 되는 훅 유형 — 이미 상당수 쓰고 있었다.**
검색 결과, 반응이 좋은 훅 유형은 반박형("다들 X라고 하지만, 아니다"),
숫자·통계 나열형, 스토리형 순이었다. 지금 문구를 보니:

> "A boltless frame sounds like a shortcut. It is the harder engineering choice."

이게 이미 반박형이다. 제조 필러의 다른 훅들도 대부분 이 구조다. 처음부터
새로 쓸 필요는 없었다.

**3. 실제로 비어 있던 자리 하나 — 고쳤다.**
숫자·통계형 훅이 2.5배 반응을 낸다는 결과가 있었는데, 정작 "figure" 판형
(이미지에 "264 lb" 처럼 숫자를 크게 넣는 판형)에서는 **본문 첫 줄이 그
숫자와 무관한 문장**으로 시작하고 있었다. 이미지는 숫자를 주장하고, 글은
다른 얘기를 하는 셈이었다.

**고침:** figure 판형이 걸리는 게시글은 본문 첫 줄이 이미지와 같은 숫자로
시작하도록 연결했다 (`composer.py` `_lead_with_the_figure`). 예:

- "264 lb — per tier, on the five-tier HOMEDANT House shelving."
- "10 min — to stand a unit up, by hand, with no tools."
- "0 bolts — HANDiLOCK locks the frame together by hand."

미국 소매 시즌(모먼트)에 맞춘 훅이 이미 있는 날은 그게 더 구체적이라 그대로
둔다 — 숫자 훅이 덮어쓰지 않는다.

## 결론

"자연스러움"을 통째로 다시 쓸 문제는 아니었다. 검증할 수 있는 범위에서는
이미 업계 통용 패턴을 따르고 있었고, 실제 어긋난 지점 — 이미지와 글이 같은
주장을 안 하던 것 — 하나만 고쳤다. 진짜 검증은 실제 게시글의 노출·반응
데이터로 하는 게 맞고, 그게 `report_performance.py` 가 하는 일이다.

## 출처

- [LinkedIn Hooks That Stop the Scroll: 25 Proven Opening Lines for 2026](https://connectsafely.ai/articles/linkedin-hooks-engagement-guide-2026)
- [LinkedIn Post Headlines: 15 Proven Hooks That Stop the Scroll (2026)](https://connectsafely.ai/articles/linkedin-post-headline-writing-guide-2026)
- [LinkedIn Marketing Strategy 2026: Complete B2B Guide](https://lagrowthmachine.com/linkedin-marketing-strategy-2026/)
