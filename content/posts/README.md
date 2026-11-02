# 기존 LinkedIn 게시글 보관함

여기에 이미 LinkedIn에 올린 게시글을 넣어 주세요. 에이전트가 이 글들을
읽고 실제 문체(호흡, 문장 길이, 이모지 사용, 마무리 방식)에 맞춰 새 초안을
씁니다. 글이 없으면 에이전트는 기본 템플릿 문체로만 씁니다.

## 넣는 방법 (GitHub 웹에서, git 명령 없이)

1. 이 폴더 페이지에서 **Add file → Create new file** 클릭
2. 파일 이름을 `content/posts/2026-08-14-garage-shelf.md` 처럼 `날짜-주제.md` 형식으로 입력
3. 아래 형식대로 붙여넣기
4. 아래쪽 **Commit changes** 클릭

여러 개를 한 번에 올릴 때는 **Add file → Upload files** 로 `.md` 파일들을
드래그해서 넣으면 됩니다.

## 파일 형식

파일 맨 위에 `---` 로 감싼 정보 블록을 두고, 그 아래에 게시글 본문을
**LinkedIn에 올린 그대로** (줄바꿈, 이모지, 해시태그 포함) 붙여 넣습니다.

```markdown
---
date: 2026-08-14
url: https://www.linkedin.com/posts/...
language: ko
topic: 창고 선반 신제품 출시
asin: B0GWGZF1F3
reactions: 42
comments: 5
---

여기에 게시글 본문을 그대로 붙여넣습니다.

줄바꿈도 원문 그대로 두세요. 문단 사이 간격이 문체의 일부입니다.

#HomeOrganization #HOMEDANT
```

### 정보 블록 항목

| 항목 | 필수 | 설명 |
| --- | --- | --- |
| `date` | 필수 | 게시일 `YYYY-MM-DD` |
| `url` | 선택 | 원본 게시글 링크 |
| `language` | 선택 | `ko` 또는 `en` (기본 `en`) |
| `topic` | 선택 | 한 줄 주제 |
| `asin` | 선택 | 해당 제품 ASIN. 있으면 카탈로그와 연결됩니다 |
| `reactions` / `comments` | 선택 | 반응 수. 어떤 글이 잘 먹혔는지 판단하는 데 씁니다 |

정보 블록 없이 본문만 붙여넣어도 읽을 수는 있습니다. 날짜와 반응 수가
있으면 더 정확해집니다.

## 한 번에 많이 올리고 싶다면

LinkedIn에서 본인 게시글 전체를 파일로 받을 수 있습니다.

LinkedIn → **Settings & Privacy → Data privacy → Get a copy of your data**
에서 게시글(Shares)을 포함해 요청하면, 잠시 뒤 메일로 받는 zip 안에
`Shares.csv` 가 들어 있습니다. 그 CSV를 이 폴더에 그대로 올려 주셔도 됩니다.
제가 개별 `.md` 파일로 나눠 드립니다.

## 주의

이 저장소는 **공개(public)** 입니다. 올린 글은 누구나 볼 수 있습니다.
어차피 LinkedIn에 공개한 글이라면 문제없지만, 미공개 초안이나 내부 자료는
넣지 마세요.
