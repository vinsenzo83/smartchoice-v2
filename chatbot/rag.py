"""RAG 챗봇 - AJD 3사 데이터 기반 인터넷/TV 상담"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATA_DIR = Path(__file__).parent.parent / "data"

# 데이터 메모리 로드
_cache = {}


def get_data(provider_key=None):
    """데이터 로드 (캐시)"""
    if "all" not in _cache:
        path = DATA_DIR / "all_providers.json"
        with open(path, "r", encoding="utf-8") as f:
            _cache["all"] = json.load(f)
    if provider_key:
        return _cache["all"].get(provider_key, {})
    return _cache["all"]


def build_context(provider_key):
    """통신사 데이터를 Claude에게 넘길 컨텍스트 텍스트로 변환"""
    data = get_data(provider_key)
    if not data:
        return "해당 통신사 데이터가 없습니다."

    provider = data.get("provider", provider_key.upper())
    parts = [f"# {provider} 인터넷/TV 상품 데이터\n"]

    # 1. 인터넷+TV 요금표
    itvs = data.get("internet_tv", [])
    if itvs:
        parts.append("## 인터넷+TV 요금표")
        parts.append("| 상품 | 채널 | 유형 | 100M | 500M | 1G | 사은품(100M) | 사은품(500M) | 사은품(1G) |")
        parts.append("|------|------|------|------|------|-----|-------------|-------------|------------|")
        for item in itvs:
            name = item.get("name", "")
            ch = item.get("channels", "-")
            t = item.get("type", "")
            p100 = f"{item.get('price_100m', '-'):,}원" if item.get("price_100m") else "-"
            p500 = f"{item.get('price_500m', '-'):,}원" if item.get("price_500m") else "-"
            p1g = f"{item.get('price_1g', '-'):,}원" if item.get("price_1g") else "-"
            g100 = item.get("gift_100m", "-")
            g500 = item.get("gift_500m", "-")
            g1g = item.get("gift_1g", "-")
            if t == "미결합":
                parts.append(f"| {name} | {ch} | {t} | {p100} | {p500} | {p1g} | {g100} | {g500} | {g1g} |")
            else:
                parts.append(f"| {name} | {ch} | {t} | {p100} | {p500} | {p1g} | | | |")

    # 2. TV 단독 요금
    tv_solo = data.get("page_content", {}).get("tv_standalone", [])
    if tv_solo:
        parts.append("\n## TV 단독 요금")
        parts.append("| TV 상품 | 월 요금 |")
        parts.append("|---------|--------|")
        for tv in tv_solo:
            parts.append(f"| {tv['name']} | {tv['monthly_price']:,}원 |")

    # 3. 결합 종류
    bundles = data.get("bundle_types", [])
    if bundles:
        parts.append("\n## 결합 종류/조건")
        for b in bundles:
            if isinstance(b, dict):
                items = " | ".join(f"{k}: {v}" for k, v in b.items())
                parts.append(f"- {items}")
            elif isinstance(b, list):
                for bb in b:
                    if isinstance(bb, dict):
                        items = " | ".join(f"{k}: {v}" for k, v in bb.items())
                        parts.append(f"- {items}")

    # 4. 결합할인 상세
    bd = data.get("bundle_discount", [])
    if bd:
        parts.append("\n## 결합할인 상세")
        for row in bd:
            if isinstance(row, dict):
                items = " | ".join(f"{k}: {v}" for k, v in row.items())
                parts.append(f"- {items}")

    # 5. 장기고객 할인
    ltd = data.get("long_term_discount", [])
    if ltd:
        parts.append("\n## 장기고객 할인")
        for row in ltd:
            if isinstance(row, dict):
                items = " | ".join(f"{k}: {v}" for k, v in row.items())
                parts.append(f"- {items}")

    # 6. 카드
    cards = data.get("cards", [])
    if cards:
        parts.append("\n## 인터넷/TV 전용 제휴카드")
        parts.append("| 카드사 | 카드명 | 할인금액 | 실적조건 | 기간 |")
        parts.append("|--------|--------|---------|---------|------|")
        for c in cards:
            parts.append(f"| {c.get('issuer','')} | {c.get('name','')} | {c.get('discount_amount',0):,}원 | {c.get('min_performance','')} | {c.get('period','')} |")

    # 7. 셋톱박스
    stbs = data.get("settop_box", [])
    if stbs:
        parts.append("\n## 셋톱박스")
        for s in stbs:
            items = " | ".join(f"{k}: {v}" for k, v in s.items())
            parts.append(f"- {items}")

    # 8. OTT 지원
    otts = data.get("ott_support", [])
    if otts:
        parts.append("\n## OTT 지원 현황")
        for o in otts:
            items = " | ".join(f"{k}: {v}" for k, v in o.items())
            parts.append(f"- {items}")

    # 9. 와이파이
    wifis = data.get("wifi", [])
    if wifis:
        parts.append("\n## 와이파이 옵션")
        for w in wifis:
            items = " | ".join(f"{k}: {v}" for k, v in w.items())
            parts.append(f"- {items}")

    # 10. 설치비
    inst = data.get("install_fee", {})
    if inst:
        parts.append("\n## 설치비")
        for k, v in inst.items():
            parts.append(f"- {k}: {v}")

    # 11. 유선전화
    phones = data.get("phone_plans", [])
    if phones:
        parts.append("\n## 유선전화 요금제")
        for p in phones:
            items = " | ".join(f"{k}: {v}" for k, v in p.items())
            parts.append(f"- {items}")

    # 12. 할인 안내 텍스트
    guide = data.get("page_content", {}).get("discount_guide", [])
    if guide:
        parts.append("\n## 할인 안내")
        parts.append("\n".join(guide[:30]))

    # 13. 결합할인 상세 (요금제별/회선별)
    bundle_detail_path = DATA_DIR / "bundle_discount_detail.json"
    if bundle_detail_path.exists():
        with open(bundle_detail_path, "r", encoding="utf-8") as f:
            bd = json.load(f)
        prov_bd = bd.get(provider_key, {})
        if prov_bd:
            parts.append("\n## 결합할인 상세 (요금제별/회선별)")
            parts.append(json.dumps(prov_bd, ensure_ascii=False, indent=2))
        # 유의사항
        notes = bd.get("유의사항", {})
        if notes:
            parts.append("\n## 결합 유의사항")
            for k, v in notes.items():
                parts.append(f"- {k}: {v}")

    # 14. 모바일 요금제 (결합할인 계산용) — 상위 10개만
    mobile_file_map = {"skt": "skt_mobile.json", "kt": "kt_mobile.json", "lg": "lguplus_mobile.json"}
    mobile_file = mobile_file_map.get(provider_key)
    if mobile_file:
        mobile_path = DATA_DIR / mobile_file
        if mobile_path.exists():
            with open(mobile_path, "r", encoding="utf-8") as f:
                mobile_plans = json.load(f)
            if mobile_plans:
                parts.append("\n## 주요 모바일 요금제 (결합할인 참고)")
                parts.append("| 요금제명 | 월정액 |")
                parts.append("|----------|--------|")
                for mp in mobile_plans[:10]:
                    name = mp.get("name", "")
                    fee = mp.get("monthly_fee", "")
                    try:
                        fee_str = f"{int(fee):,}원"
                    except (ValueError, TypeError):
                        fee_str = fee
                    parts.append(f"| {name} | {fee_str} |")

    # 15. 상품 카탈로그 (상품번호)
    catalog_path = DATA_DIR / "product_catalog.json"
    if catalog_path.exists():
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        # 해당 통신사 상품만
        prov_name = {"skt": "SKT", "kt": "KT", "lg": "LG U+"}.get(provider_key, "")
        my_items = {k: v for k, v in catalog.items() if v.get("provider") == prov_name}
        if my_items:
            parts.append("\n## 상품번호 카탈로그 (표에 반드시 포함!)")
            parts.append("| 상품번호 | 상품 | 속도 | 1대결합가 |")
            parts.append("|----------|------|------|----------|")
            for pid, info in my_items.items():
                parts.append(f"| {pid} | {info['name']} | {info['speed']} | {info['price']:,}원 |")

    return "\n".join(parts)


SYSTEM_PROMPT = """당신은 "돈줄" - 인터넷/TV 사은품 전문 1차 상담 AI입니다.

## 핵심 목표
1. **사은품이 메인이다.** 고객은 사은품을 받으러 온 사람이다. 모든 답변에서 사은품을 가장 크게, 먼저 보여줘라.
2. **요금/결합/카드는 서비스로 안내한다.** "사은품도 받고, 요금도 이만큼 아낄 수 있어요!" 느낌.
3. **최종 목표는 TM 상담 연결이다.** 답변 마지막에 자연스럽게 "전문 상담사가 더 자세히 안내해드릴 수 있어요" 멘트.

## 사은품 강조 방식
- 사은품 금액을 항상 맨 위에 표시
- **사은품은 반드시 인터넷 단독 / 인터넷+TV 결합을 구분해서 표시할 것**
- 인터넷 단독 사은품과 TV 결합 사은품은 금액이 다르다. 섞어서 표시하면 안 된다.
- 예시:
  "🎁 인터넷 단독: 최대 17만원 / 인터넷+TV 결합: 최대 49만원!"
- 사은품은 아정당(ajd.co.kr) 기준
- **데이터의 사은품 금액을 정확히 확인하고 표시할 것. 인터넷 단독 행의 사은품과 인터넷+TV 행의 사은품을 구분해서 가져와라.**

## 초개인화 추천 모드
사용자 프로필에 생활패턴 정보가 있으면, 그에 맞는 **딱 1~2개 조합만 추천**하라.
모든 상품을 나열하지 말고, 이 고객에게 **가장 적합한 것만** 골라서 추천.

생활패턴 → 추천 로직:
- 1인가구 + 기본사용 → 인터넷 100M 단독 (TV 없이)
- 1인가구 + 넷플릭스/유튜브 → 인터넷 500M 단독 (OTT는 본인 구독)
- 2인가구 + 넷플릭스 → 인터넷 500M + TV 기본형
- 2인가구 + 게임 → 인터넷 1G + TV 기본형
- 3~4인가구 + 넷플릭스 → 인터넷 500M~1G + TV 넷플릭스 포함 상품
- 3~4인가구 + 게임 → 인터넷 1G + TV 프리미엄
- 5인이상 → 인터넷 1G + TV 프리미엄 + 가족결합 최대 활용

답변 형식:
### 🎁 사은품 안내 (가장 먼저, 가장 크게!)
"🎁 지금 가입하시면 사은품 최대 XX만원!"

| 상품 | 속도 | 사은품 |
|------|------|--------|
사은품 큰 순서로 정렬. 사은품이 포인트다.

### 🎯 맞춤 추천
고객님 상황에 딱 맞는 상품 + 사은품

| 항목 | 내용 |
|------|------|
| 🎁 **사은품** | **XX만원** |
| 📶 인터넷 | ○○ XXM |
| 📺 TV | ○○ (XX채널) |
| 💰 결합할인 | -XX,XXX원 |
| 💳 카드할인 | -XX,XXX원 |
| ✅ **최종 월 요금** | **XX,XXX원** |

### 💡 이렇게나 아낄 수 있어요
"사은품 XX만원 받고, 월 요금도 XX,XXX원밖에 안 돼요!"

### 📞 상담사 연결 유도 (항상 마지막에!)
답변 마지막에 반드시 상담사 연결을 유도하되, **매번 다른 자연스러운 멘트**로 해라. 같은 말 반복 금지.
핵심 메시지: 상담사를 통하면 **여기 안내된 사은품 외에 추가 혜택**이 더 있다는 뉘앙스.

멘트 예시 (참고만 하고 매번 다르게 변형):
- "참, 상담사 통해서 가입하시면 여기 안내드린 것보다 더 챙겨드릴 수 있는 부분이 있어요 👀"
- "혹시 바로 가입 진행하시게 되면, 상담사가 추가로 챙겨드리는 혜택도 있거든요~"
- "사은품 말고도 상담사만 드릴 수 있는 게 따로 있어서, 연결해드리면 좀 더 알차게 받으실 수 있어요!"
- "이 조건이면 상당히 좋은 건데, 상담사 연결하시면 여기서 조금 더 얹어드릴 수 있어요 😊"

절대 "특별 사은품"이라는 단어를 직접 쓰지 마라. 은근하게, 궁금하게 만들어라.
**데이터에 없는 혜택을 지어내지 마라. "월세보증금", "신혼플러스" 등 데이터에 없는 용어 사용 금지. 상담사가 추가 혜택을 드린다는 뉘앙스만 줘라.**

생활패턴 정보가 없으면 기존 방식(전체 테이블)으로 답변.

## 대화 톤
- 너의 이름은 **돈줄** (돈을 줄여준다 + 돈줄). 항상 "돈줄"로 표기.
- 사은품을 강조하면서도 부담스럽지 않게. "이 상품 가입하시면 사은품 XX만원 드려요~" 느낌
- 고객이 망설이면 "지금이 제일 좋은 조건이에요" "이번 달 사은품이 특히 많아요" 같은 넛지
- 모든 답변 끝에 자연스럽게 상담 연결 유도: "더 궁금하신 거 있으면 전문 상담사 바로 연결해드릴게요!"
- 친근하고 편한 말투. "~해요", "~거든요", "~이에요" 스타일
- 이모지 자연스럽게 사용
- 인사하면 "돈줌이에요~" 하고 자기소개 + 뭘 도와줄 수 있는지 간단히 설명
- "뭐 할 수 있어?" 같은 질문엔 할 수 있는 것 목록 안내
- 이전 대화 맥락을 반드시 기억하고 이어서 대화할 것
- 고객이 한 말을 다시 요약해주면서 공감 표현

## 돈줌이 할 수 있는 것
1. 인터넷/TV 요금 비교 (SKT, KT, LG U+)
2. 생활패턴 맞춤 추천 (가족수, 사용용도 기반)
3. 결합할인 계산 (가족결합, 총액결합 등)
4. 제휴카드 할인 비교
5. 사은품/설치비/셋톱박스/와이파이 안내
6. 최종 실질 요금 계산 (기본요금 - 결합할인 - 카드할인)
7. 전문 상담사 연결 (바로 상담 / 연락받기)

## 절대 규칙
1. **사용자에게 추가 질문을 하지 마라.** 정보가 부족하면 모든 경우의 수를 표에 다 보여줘라.
2. **아래 6개 섹션을 반드시 전부 출력하라. 하나라도 빠지면 안 된다.**
3. 인터넷만 물어봐도 TV, 결합, 카드, 결합할인까지 전부 보여줘라.

### 📶 1. 인터넷 요금표
| 속도 | 미결합 | 1대결합 | 사은품 |
인터넷 단독 요금. 모든 속도(100M/500M/1G) 포함.

### 📺 2. TV 상품 안내 (반드시 출력!)
| TV 상품 | 채널수 | TV 추가 요금 |
TV 단독 요금 데이터가 있으면 표시. 없으면 인터넷+TV 결합가에서 인터넷 단독가를 빼서 TV 추가 비용 계산.
**이 표를 절대 생략하지 마라.**

### 📦 3. 인터넷+TV 결합 요금표 (반드시 출력! 가장 중요!)
| 결합상품 | 채널 | 속도 | 미결합 | 1대결합 | 카드할인 | **최종월요금** | 사은품 |
모든 TV등급 x 모든 속도 조합. 사은품 큰 순서로 정렬.
**이 표를 절대 생략하지 마라. 인터넷만 물어봐도 TV 결합 표까지 무조건 보여줘라.**
**모든 표의 첫 번째 컬럼에 상품번호(S001, K016, L034 등)를 반드시 표시할 것.**
**BEST 추천의 상품번호는 `코드블록`으로 감싸서 표시. 예: `S005`**
- 모든 TV등급 x 모든 속도 조합을 행으로
- 카드할인은 추천카드 1개 기준 (컬럼 헤더에 카드명 표기)
- **최종월요금 = 1대결합 - 카드할인** (굵게)
- 사은품은 아정당(ajd.co.kr) 기준
- 최종월요금 낮은 순 정렬

### 💰 4. 결합할인 안내
결합할인은 위 3번 표의 1대결합과 **별도 추가 할인**이다. 반드시 아래처럼 속도별로 한 줄씩 보여줘라.

**가족결합 (인터넷 할인)**
| 속도 | 인터넷 할인금액 |
|------|---------------|
| 100M | X,XXX원 |
| 500M | XX,XXX원 |
| 1G | XX,XXX원 |

**가족결합 (휴대폰 할인)**
| 요금제 구간 | 할인금액 |
데이터에 있으면 표시. 최소~최대만 있으면 그대로 표시.

**총액결합할인** (KT/LG 등 해당 시)
| 월 합산 요금 | 인터넷 할인 | 휴대폰 할인 |
구간별로 한 줄씩.

**장기고객 할인** (해당 시)
| 가입기간 | 할인율 |
년수별로 한 줄씩.

각 결합할인 아래에 "3번 결합요금에서 추가로 X원 더 할인 가능" 식으로 구체적 예시를 넣어라.
예: "인터넷 500M + Btv이코노미 1대결합 35,200원에서 가족결합 11,000원 추가 할인 → **24,200원**"

**절대 `<br>` 태그를 쓰지 마라. 줄바꿈은 표의 새 행으로 처리할 것.**

### 💳 5. 추천 카드
| 카드명 | 월 최대할인 | 전월실적 | 할인기간 |
**반드시 월 최대 할인금액이 큰 순서대로. 인터넷/TV 전용 카드만 사용.**

### ✅ BEST 추천 (반드시 2개!)
특정 통신사 지정 시 해당 통신사에서 **가성비 BEST 2개**, 미지정이면 **전체에서 BEST 2개** 추천.
상품번호를 반드시 포함하여 고객이 바로 상담 신청할 수 있게.

| 순위 | 상품번호 | 추천 상품 | 최종월요금 | 사은품 | 추천 이유 |
|------|---------|----------|-----------|--------|----------|
| 🥇 1위 | S005 | ○○ 500M + ○○TV + ○○카드 | XX,XXX원 | XX만원 | 한 줄 이유 |
| 🥈 2위 | S008 | ○○ 500M + ○○TV + ○○카드 | XX,XXX원 | XX만원 | 한 줄 이유 |

- 1위: 최종월요금 가장 저렴한 조합
- 2위: 사은품 가장 큰 조합 또는 채널 많은 프리미엄 조합
- 각 통신사 카드할인 반드시 적용 (SKT: B롯데카드 10,000원, KT: 현대카드, LG U+: 현대카드)
- OTT는 고객이 언급한 경우만 포함
- "위 상품번호로 바로 상담 신청하실 수 있어요!" 멘트 추가

## 정확성 규칙
- 제공된 데이터 기반으로만 답변. 없으면 "데이터에 없습니다"
- **가격 순위는 숫자를 직접 비교. 작성 후 재검증**
- 약정별/결합별 요금 차이 명시
- **데이터에 정확한 금액이 없고 "최소~최대" 범위만 있으면 범위로 표시. 임의로 특정 금액을 단정짓지 마라.**
- 예: 휴대폰 할인이 "최소 3,500 ~ 최대 24,000원"이면 그대로 표시. "10만원 요금제는 24,000원 할인" 같은 추측 금지.
- 정확한 금액은 "상담 시 요금제에 따라 확인 가능"으로 안내
- 한국어로 답변"""


def ask(question, provider_key=None, chat_history=None):
    """질문에 대해 답변 생성 - 데이터는 system에, 대화는 messages에"""
    import anthropic

    # 컨텍스트 구성
    if provider_key:
        context = build_context(provider_key)
    else:
        context_parts = []
        for pk in ["skt", "kt", "lg"]:
            context_parts.append(build_context(pk))
        context = "\n\n---\n\n".join(context_parts)

    # 시스템 프롬프트에 데이터 포함
    full_system = f"""{SYSTEM_PROMPT}

## 통신사 상품 데이터
{context}"""

    # 대화 히스토리 (깔끔하게)
    messages = []
    if chat_history:
        for msg in chat_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    # 현재 질문
    messages.append({"role": "user", "content": question})

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=full_system,
        messages=messages,
    )
    return response.content[0].text


def detect_provider(text):
    """텍스트에서 통신사 감지"""
    q = text.lower()
    if any(kw in q for kw in ["sk", "skt", "skb", "브로드"]):
        return "skt"
    if any(kw in q for kw in ["kt", "케이티"]):
        return "kt"
    if any(kw in q for kw in ["lg", "유플", "엘지"]):
        return "lg"
    return None


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("데이터 로드 완료!\n")
    while True:
        q = input("질문: ").strip()
        if not q or q in ("quit", "exit", "q"):
            break
        prov = detect_provider(q)
        answer = ask(q, provider_key=prov)
        print(f"\n{answer}\n")
