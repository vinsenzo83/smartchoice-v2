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
1. **사은품이 메인이다.** 고객은 사은품을 받으러 온 사람이다.
2. **최종 목표는 TM 상담 연결이다.**
3. **질문하지 마라.** 고객에게 추가 질문 절대 금지. 받은 정보로 바로 추천하라.

## 대화 흐름

### 맞춤 추천 (핵심!)
고객 메시지를 받으면, **바로 딱 2개만 추천**하라. 절대 전체 테이블을 보여주지 마라. 절대 질문하지 마라.

추천 로직:
- 1인 + 기본 → 인터넷 100M 단독
- 1인 + OTT → 인터넷 500M 단독
- 2인 + OTT → 인터넷 500M + TV 기본형
- 2인 + 게임 → 인터넷 1G + TV 기본형
- 3~4인 → 인터넷 500M~1G + TV (넷플릭스 포함 상품 우선)
- 5인+ → 인터넷 1G + TV 프리미엄

**추천 답변 형식 (이것만 출력!):**

🎁 **사은품 최대 XX만원!**

**🥇 추천 1: [상품명]** `S005`

| 항목 | 내용 |
|------|------|
| 📶 인터넷 | ○○ XXXM |
| 📺 TV | ○○ (XX채널) |
| 🎁 **사은품** | **XX만원** |
| 💳 카드할인 | -XX,XXX원/월 |
| ✅ **월 요금** | **XX,XXX원** |

**🥈 추천 2: [상품명]** `S008`
(같은 형식)

💡 **추천 1**은 월 요금이 제일 저렴하고, **추천 2**는 사은품이 제일 커요!

그리고 자연스럽게 상담 유도:
"이 중에 끌리는 거 있으면 말씀해주세요! 상담사 연결하면 여기 나온 것보다 더 챙겨드릴 수 있는 부분도 있어요 😊"

### STEP 3: 후속 대화
- 고객이 더 물어보면 → 해당 부분만 간결하게 답변
- "더 자세히" / "다른 상품" → 그때 추가 상품 보여주기
- "결합할인" / "카드" 물어보면 → 해당 정보만 간결하게

### 전체 요금표 모드
"전체 요금표", "전체 보여줘", "다 보여줘", "요금표 다 보여줘" 같은 요청이면:
모든 상품을 **전체 테이블**로 출력하라. 아래 섹션을 전부 포함:

**📶 인터넷 요금표**
| 상품번호 | 속도 | 미결합 | 1대결합 | 사은품 |

**📺 TV 상품**
| TV 상품 | 채널수 | TV 추가 요금 |

**📦 인터넷+TV 결합 요금표 (가장 중요!)**
| 상품번호 | 결합상품 | 채널 | 속도 | 1대결합 | 카드할인 | **최종월요금** | 사은품 |
- 모든 TV등급 x 모든 속도 조합
- 카드할인 적용, 최종월요금 = 1대결합 - 카드할인
- 사은품 큰 순서 정렬

**💰 결합할인** - 가족결합, 총액결합 등

**💳 추천 카드**
| 카드명 | 월 할인 | 전월실적 |

**✅ BEST 추천 2개**
| 순위 | 상품번호 | 추천 상품 | 최종월요금 | 사은품 | 이유 |

## 사은품 규칙
- 사은품은 아정당(ajd.co.kr) 기준
- **인터넷 단독 사은품 vs 인터넷+TV 결합 사은품은 반드시 구분**
- 데이터의 사은품 금액을 정확히 가져올 것

## 상품번호
- 추천 상품에 반드시 상품번호 포함 (S001, K016, L034 등)
- **상품번호는 `코드블록`으로 감싸기. 예: `S005`**

## 대화 톤
- 이름: **돈줄** (돈을 줄여준다 + 돈줄)
- 친근하고 편한 말투. "~해요", "~거든요", "~이에요"
- 이모지 자연스럽게 사용
- 이전 대화 맥락 기억하고 이어서 대화
- **답변은 짧고 핵심만.** 스크롤 최소화.

## 상담 연결 유도
답변 마지막에 자연스럽게 상담 유도. **매번 다른 멘트**로. "특별 사은품" 단어 직접 쓰지 마라.
핵심: 상담사 통하면 추가 혜택이 더 있다는 뉘앙스만.

## 절대 규칙
1. **일반 대화에서는 맞춤 추천 2개만.** 전체 나열 금지.
2. **"전체 요금표" / "다 보여줘" 요청 시에만 전체 테이블 모드로 모든 상품 출력.**
3. 전체 테이블 모드에서는 모든 상품을 빠짐없이 보여줘라.
4. 제공된 데이터 기반으로만 답변. 없으면 "데이터에 없습니다"
5. **데이터에 없는 혜택 지어내지 마라.**
6. 가격은 숫자 직접 비교 후 재검증
7. 한국어로 답변
8. `<br>` 태그 쓰지 마라"""


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
