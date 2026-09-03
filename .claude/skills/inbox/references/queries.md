# 검색 질의

`outlook_email_search` 로 후보를 좁힐 때 쓴다. 전체를 훑는 것보다 이 질의를
순서대로 돌리는 편이 빠르고 정확하다. 결과가 겹치므로 발신자와 제목으로
중복을 제거한다.

기본 기간은 최근 30일. 결과가 20건 미만이면 90일로 넓히고, 200건을 넘으면
7일씩 나눠 돌린다.

## 1순위 — 거래 단계 언어 (거의 전부 A·B급)

```
quotation OR quote OR RFQ OR "request for quote"
MOQ OR "minimum order" OR "price list" OR "wholesale price"
"purchase order" OR PO OR "vendor setup" OR "new vendor"
"line review" OR "case pack" OR planogram OR "sell-through"
container OR "40HQ" OR FOB OR DDP OR EXW OR "landed cost"
```

## 2순위 — 우리 제품과 사업

```
shelving OR shelf OR "storage rack" OR pegboard OR boltless
HOMEDANT OR HANDiLOCK OR LiftBeam
"private label" OR OEM OR ODM
```

## 3순위 — 전시회 후속 (`brand.json` 의 전시회명을 그대로 쓴다)

```
"High Point Market" OR HPMKT OR "M-1007"
"NY NOW" OR "National Hardware Show" OR NeoCon OR "DESIGN TOKYO"
"met you at" OR "following up from the show" OR "booth"
```

## 4순위 — 방치하면 손해가 나는 실무 건

```
chargeback OR "damaged on arrival" OR shortage OR claim
"Seller Central" OR "listing suppressed" OR "policy violation" OR "case ID"
"action required" OR deadline OR "by end of"
```

## 5순위 — 채널별 발신자

```
from:*@*.com 중 리테일·유통 도메인 (walmart, homedepot, lowes, acehardware,
truevalue, wayfair, overstock 등 알려진 채널명)
RangeMe OR "buyer inquiry" OR "supplier inquiry"
```

## 걸러낼 때 쓰는 반대 질의

아래에 걸리는 건은 C급 후보로 먼저 빼면 남는 양이 크게 준다.

```
unsubscribe OR newsletter OR webinar OR "no-reply" OR noreply
"boost your sales" OR "rank higher" OR "we noticed your listing"
"sourcing agent" OR "we can find suppliers" OR "freight forwarder"
"free sample" (조건 언급 없이 단독으로 나오는 경우)
```

`unsubscribe` 가 본문에 있다고 무조건 C급은 아니다. 리테일러의 정식
벤더 포털 안내에도 들어 있다. 발신 도메인을 함께 본다.
