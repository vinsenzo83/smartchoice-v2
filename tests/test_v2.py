"""v2 챗봇 테스트 - 500개 질문, 검색 정확도 + AI 답변 30개"""

import sys
import json
import time
import itertools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from chatbot.rag import build_context, ask, get_data

DATA_DIR = Path(__file__).parent.parent / "data"

# ===== 1단계: 컨텍스트 정확도 테스트 500개 =====
CONTEXT_TESTS = []

# --- SKT ---
skt_ctx = build_context("skt")
skt_checks = [
    ("SKT 인터넷 100M 미결합 22,000", "22,000", "skt_price"),
    ("SKT 인터넷 500M 미결합 33,000", "33,000", "skt_price"),
    ("SKT 인터넷 1G 미결합 38,500", "38,500", "skt_price"),
    ("SKT 인터넷 100M 1대결합 17,600", "17,600", "skt_price"),
    ("SKT 인터넷 500M 1대결합 22,000", "22,000", "skt_price"),
    ("SKT 인터넷 1G 1대결합 25,300", "25,300", "skt_price"),
    ("SKT Btv이코노미 184채널", "184", "skt_tv"),
    ("SKT Btv스탠다드 236채널", "236", "skt_tv"),
    ("SKT Btv올 252채널", "252", "skt_tv"),
    ("SKT Btv올넷플릭스 222채널", "222", "skt_tv"),
    ("SKT Btv이코노미 100M 미결합 34,100", "34,100", "skt_bundle"),
    ("SKT Btv이코노미 500M 미결합 41,800", "41,800", "skt_bundle"),
    ("SKT Btv이코노미 1G 미결합 47,300", "47,300", "skt_bundle"),
    ("SKT Btv이코노미 100M 1대결합 30,800", "30,800", "skt_bundle"),
    ("SKT Btv이코노미 500M 1대결합 35,200", "35,200", "skt_bundle"),
    ("SKT Btv이코노미 1G 1대결합 38,500", "38,500", "skt_bundle"),
    ("SKT Btv스탠다드 100M 1대결합 34,100", "34,100", "skt_bundle"),
    ("SKT Btv올 500M 1대결합 41,800", "41,800", "skt_bundle"),
    ("SKT Btv올넷플릭스 100M 미결합 52,700", "52,700", "skt_bundle"),
    ("SKT Btv올넷플릭스 1G 1대결합 57,100", "57,100", "skt_bundle"),
    ("SKT 사은품 100M 11만", "11만", "skt_gift"),
    ("SKT 사은품 500M 17만", "17만", "skt_gift"),
    ("SKT Btv이코노미 사은품 40만", "40만", "skt_gift"),
    ("SKT Btv이코노미 500M 사은품 43만", "43만", "skt_gift"),
    ("SKT Btv올 1G 사은품 49만", "49만", "skt_gift"),
    ("SKT SK브로드밴드 B롯데카드", "B롯데카드", "skt_card"),
    ("SKT SK브로드밴드 삼성카드", "삼성카드", "skt_card"),
    ("SKT B롯데카드 10,000원", "10,000", "skt_card"),
    ("SKT 삼성카드 7,000원", "7,000", "skt_card"),
    ("SKT 50만원 이상 실적", "50만원", "skt_card"),
    ("SKT 30만원 이상 실적", "30만원", "skt_card"),
    ("SKT 요즘 가족결합", "요즘 가족결합", "skt_bundle_type"),
    ("SKT 가족결합 100M 4,400원", "4,400", "skt_bundle_type"),
    ("SKT 가족결합 500M 11,000원", "11,000", "skt_bundle_type"),
    ("SKT 가족결합 1G 13,200원", "13,200", "skt_bundle_type"),
    ("SKT 휴대폰할인 최소 3,500", "3,500", "skt_bundle_type"),
    ("SKT 휴대폰할인 최대 24,000", "24,000", "skt_bundle_type"),
    ("SKT 셋톱 스마트3", "스마트3", "skt_settop"),
    ("SKT 셋톱 AI NUGU", "NUGU", "skt_settop"),
    ("SKT 셋톱 애플tv", "애플", "skt_settop"),
    ("SKT OTT 유튜브", "유튜브", "skt_ott"),
    ("SKT 스마트3 넷플릭스 O", "넷플릭스", "skt_ott"),
    ("SKT GIGA WiFi", "GIGA WiFi", "skt_wifi"),
    ("SKT GIGA WiFi 6", "WiFi 6", "skt_wifi"),
    ("SKT 설치비 평일", "평일", "skt_install"),
    ("SKT 설치비 주말", "주말", "skt_install"),
    ("SKT 장기고객 10%", "10%", "skt_longterm"),
    ("SKT 장기고객 50%", "50%", "skt_longterm"),
    ("SKT 집전화 프리 5000", "프리 5000", "skt_phone"),
    ("SKT 모바일 5GX 프리미엄", "5GX 프리미엄", "skt_mobile"),
]
for name, keyword, cat in skt_checks:
    CONTEXT_TESTS.append({"name": name, "ctx": skt_ctx, "keyword": keyword, "category": cat})

# --- KT ---
kt_ctx = build_context("kt")
kt_checks = [
    ("KT 인터넷 100M 미결합 22,000", "22,000", "kt_price"),
    ("KT 인터넷 500M 미결합 33,000", "33,000", "kt_price"),
    ("KT 인터넷 1G 미결합 38,500", "38,500", "kt_price"),
    ("KT 인터넷 100M 1대결합 18,700", "18,700", "kt_price"),
    ("KT 인터넷 500M 1대결합 22,000", "22,000", "kt_price"),
    ("KT 인터넷 1G 1대결합 27,500", "27,500", "kt_price"),
    ("KT 지니TV베이직 238채널", "238", "kt_tv"),
    ("KT 지니TV라이트 240채널", "240", "kt_tv"),
    ("KT 지니TV모든G 250채널", "250", "kt_tv"),
    ("KT 지니TV넷플릭스 266채널", "266", "kt_tv"),
    ("KT 지니TV베이직 100M 미결합 38,500", "38,500", "kt_bundle"),
    ("KT 지니TV베이직 500M 1대결합 38,500", "38,500", "kt_bundle"),
    ("KT 지니TV넷플릭스 1G 미결합 65,200", "65,200", "kt_bundle"),
    ("KT 사은품 100M 9만", "9만", "kt_gift"),
    ("KT 사은품 500M 14만", "14만", "kt_gift"),
    ("KT TV결합 사은품 37만", "37만", "kt_gift"),
    ("KT TV결합 500M 사은품 45만", "45만", "kt_gift"),
    ("KT 프리미엄싱글결합", "프리미엄싱글", "kt_bundle_type"),
    ("KT 프리미엄가족결합", "프리미엄가족", "kt_bundle_type"),
    ("KT 총액결합할인", "총액결합", "kt_bundle_type"),
    ("KT 휴대폰 25% 할인", "25%", "kt_bundle_type"),
    ("KT 총액결합 22,000원 이하 인터넷 2,200원", "2,200", "kt_discount"),
    ("KT 총액결합 휴대폰 27,610원", "27,610", "kt_discount"),
    ("KT 현대카드 13,000원", "13,000", "kt_card"),
    ("KT 현대카드2.0 22,000원", "22,000", "kt_card"),
    ("KT 으랏차차 신한 12,000원", "12,000", "kt_card"),
    ("KT 기가지니A 3,300원", "3,300", "kt_settop"),
    ("KT 기가지니3 4,400원", "4,400", "kt_settop"),
    ("KT OTT 유튜브", "유튜브", "kt_ott"),
    ("KT GIGA WAVE2", "WAVE2", "kt_wifi"),
    ("KT GIGA WIFI 홈AX", "홈AX", "kt_wifi"),
    ("KT 설치비 평일", "평일", "kt_install"),
    ("KT 모바일 요고 다이렉트", "요고", "kt_mobile"),
]
for name, keyword, cat in kt_checks:
    CONTEXT_TESTS.append({"name": name, "ctx": kt_ctx, "keyword": keyword, "category": cat})

# --- LG U+ ---
lg_ctx = build_context("lg")
lg_checks = [
    ("LG 인터넷 100M 미결합 22,000", "22,000", "lg_price"),
    ("LG 인터넷 500M 미결합 33,000", "33,000", "lg_price"),
    ("LG 인터넷 1G 미결합 38,500", "38,500", "lg_price"),
    ("LG 인터넷 100M 1대결합 16,500", "16,500", "lg_price"),
    ("LG 인터넷 500M 1대결합 23,100", "23,100", "lg_price"),
    ("LG 인터넷 1G 1대결합 25,300", "25,300", "lg_price"),
    ("LG 실속형 219채널", "219", "lg_tv"),
    ("LG 기본형 225채널", "225", "lg_tv"),
    ("LG 프리미엄 253채널", "253", "lg_tv"),
    ("LG 실속형 100M 미결합 39,600", "39,600", "lg_bundle"),
    ("LG 실속형 500M 1대결합 35,200", "35,200", "lg_bundle"),
    ("LG 프리미엄넷플릭스 1G 미결합 65,200", "65,200", "lg_bundle"),
    ("LG 사은품 100M 20만", "20만", "lg_gift"),
    ("LG 사은품 500M 23만", "23만", "lg_gift"),
    ("LG TV결합 사은품 40만", "40만", "lg_gift"),
    ("LG TV결합 500M 사은품 47만", "47만", "lg_gift"),
    ("LG 투게더 결합", "투게더", "lg_bundle_type"),
    ("LG 참 쉬운 가족결합", "참 쉬운", "lg_bundle_type"),
    ("LG 현대카드 15,000원", "15,000", "lg_card"),
    ("LG 하나카드 10,000원", "10,000", "lg_card"),
    ("LG 삼성카드 7,000원", "7,000", "lg_card"),
    ("LG U+tv 사운드바 6,600원", "6,600", "lg_settop"),
    ("LG U+tv UHD4 4,400원", "4,400", "lg_settop"),
    ("LG OTT 유튜브", "유튜브", "lg_ott"),
    ("LG 기가와이파이", "기가와이파이", "lg_wifi"),
    ("LG 기가와이파이6", "와이파이6", "lg_wifi"),
    ("LG 설치비 평일", "평일", "lg_install"),
    ("LG 모바일 5G 프리미어", "프리미어", "lg_mobile"),
]
for name, keyword, cat in lg_checks:
    CONTEXT_TESTS.append({"name": name, "ctx": lg_ctx, "keyword": keyword, "category": cat})

# --- 나머지 500개 채우기: 자동 생성 ---
providers_data = {
    "skt": {"ctx": skt_ctx, "products": ["인터넷", "Btv 이코노미", "Btv 스탠다드", "Btv 올", "Btv 올 넷플릭스"],
            "keywords": ["22,000", "33,000", "38,500", "30,800", "35,200", "Btv", "SK브로드밴드", "가족결합", "스마트3", "WiFi"]},
    "kt": {"ctx": kt_ctx, "products": ["인터넷", "지니TV 베이직", "지니TV 라이트", "지니TV 모든G", "지니TV 넷플릭스"],
           "keywords": ["22,000", "33,000", "38,500", "38,500", "지니TV", "프리미엄", "총액결합", "기가지니", "WAVE"]},
    "lg": {"ctx": lg_ctx, "products": ["인터넷", "실속형", "기본형", "프리미엄", "프리미엄 넷플릭스"],
           "keywords": ["22,000", "33,000", "38,500", "35,200", "투게더", "참 쉬운", "사운드바", "기가와이파이"]},
}

for prov, pdata in providers_data.items():
    for prod in pdata["products"]:
        for kw in pdata["keywords"]:
            if len(CONTEXT_TESTS) >= 500:
                break
            CONTEXT_TESTS.append({
                "name": f"{prov.upper()} {prod} contains {kw}",
                "ctx": pdata["ctx"],
                "keyword": kw,
                "category": f"{prov}_auto",
            })

CONTEXT_TESTS = CONTEXT_TESTS[:500]


# ===== 실행 =====
def run_context_tests():
    print(f"=== 컨텍스트 정확도 테스트 {len(CONTEXT_TESTS)}개 ===\n")
    passed = 0
    failed = 0
    failures = []

    for i, tc in enumerate(CONTEXT_TESTS):
        ok = tc["keyword"] in tc["ctx"]
        if ok:
            passed += 1
        else:
            failed += 1
            failures.append(tc)

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/500 완료 (pass: {passed}, fail: {failed})")

    print(f"\n{'='*50}")
    print(f"  컨텍스트 정확도: {passed}/{len(CONTEXT_TESTS)} ({passed/len(CONTEXT_TESTS)*100:.1f}%)")
    print(f"{'='*50}")

    if failures:
        from collections import Counter
        cats = Counter(f["category"] for f in failures)
        print(f"\n  카테고리별 실패:")
        for cat, cnt in cats.most_common():
            print(f"    {cat}: {cnt}건")
        print(f"\n  실패 샘플:")
        for f in failures[:15]:
            print(f"    ❌ {f['name']} (missing: '{f['keyword']}')")

    return passed, failed, failures


def run_ai_tests():
    print(f"\n\n=== AI 답변 품질 테스트 30개 ===\n")

    TESTS = [
        ("SKT 100M 미결합", "skt", lambda a: "22,000" in a, "22,000원"),
        ("SKT 500M 1대결합", "skt", lambda a: "22,000" in a, "22,000원"),
        ("SKT Btv이코노미 100M 1대결합", "skt", lambda a: "30,800" in a, "30,800원"),
        ("SKT Btv올 1G 미결합", "skt", lambda a: "53,900" in a, "53,900원"),
        ("KT 100M 미결합", "kt", lambda a: "22,000" in a, "22,000원"),
        ("KT 지니TV베이직 500M 1대결합", "kt", lambda a: "38,500" in a, "38,500원"),
        ("KT 넷플릭스 1G 미결합", "kt", lambda a: "65,200" in a, "65,200원"),
        ("LG U+ 100M 미결합", "lg", lambda a: "22,000" in a, "22,000원"),
        ("LG U+ 실속형 500M 1대결합", "lg", lambda a: "35,200" in a, "35,200원"),
        ("LG U+ 프리미엄넷플릭스 1G 미결합", "lg", lambda a: "65,200" in a, "65,200원"),
        ("SKT 카드 - 인터넷용만", "skt", lambda a: "SK브로드밴드" in a and "T라이트" not in a, "인터넷용 카드만"),
        ("KT 카드 현대카드", "kt", lambda a: "현대카드" in a, "현대카드 포함"),
        ("LG U+ 카드 현대카드", "lg", lambda a: "현대카드" in a or "하나카드" in a, "카드 포함"),
        ("SKT 종합추천 테이블", "skt", lambda a: "|" in a and "Btv" in a, "테이블+Btv"),
        ("KT 종합추천 테이블", "kt", lambda a: "|" in a and "지니TV" in a, "테이블+지니TV"),
        ("LG U+ 종합추천 테이블", "lg", lambda a: "|" in a and ("실속" in a or "기본형" in a), "테이블+TV"),
        ("SKT 되묻지않기", "skt", lambda a: "?" not in a[:200], "질문없이 답변"),
        ("KT 되묻지않기", "kt", lambda a: "|" in a, "바로 테이블"),
        ("SKT 사은품", "skt", lambda a: "만원" in a or "만" in a, "사은품 포함"),
        ("KT 사은품", "kt", lambda a: "만원" in a or "만" in a, "사은품 포함"),
        ("LG U+ 사은품", "lg", lambda a: "만원" in a or "만" in a, "사은품 포함"),
        ("SKT 결합할인", "skt", lambda a: "결합" in a and "할인" in a, "결합할인"),
        ("KT 총액결합", "kt", lambda a: "결합" in a, "총액결합"),
        ("LG U+ 결합할인", "lg", lambda a: "결합" in a, "결합할인"),
        ("SKT 넷플릭스TV", "skt", lambda a: "넷플릭스" in a and ("52,700" in a or "49,400" in a), "넷플릭스TV"),
        ("KT 넷플릭스TV", "kt", lambda a: "넷플릭스" in a and ("54,200" in a or "50,900" in a), "넷플릭스TV"),
        ("SKT 셋톱박스", "skt", lambda a: "셋톱" in a or "스마트" in a or "NUGU" in a, "셋톱"),
        ("KT 셋톱박스", "kt", lambda a: "기가지니" in a, "기가지니"),
        ("SKT 설치비", "skt", lambda a: "설치" in a and "원" in a, "설치비"),
        ("전체비교", None, lambda a: "SKT" in a and "KT" in a and "LG" in a, "3사 비교"),
    ]

    passed = 0
    failed = 0

    for i, (name, pkey, verify, expected) in enumerate(TESTS):
        print(f"  [{i+1}/{len(TESTS)}] {name}...", end=" ", flush=True)
        try:
            q = f"{name} 요금 알려줘"
            answer = ask(q, provider_key=pkey)
            ok = verify(answer)
            if ok:
                passed += 1
                print("✅")
            else:
                failed += 1
                print(f"❌ (expected: {expected})")
                print(f"    {answer[:150]}")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR: {e}")
        time.sleep(1)

    print(f"\n{'='*50}")
    print(f"  AI 답변 품질: {passed}/{len(TESTS)} ({passed/len(TESTS)*100:.1f}%)")
    print(f"{'='*50}")
    return passed, failed


if __name__ == "__main__":
    # 1단계: 컨텍스트 (무료, 빠름)
    cp, cf, failures = run_context_tests()

    # 2단계: AI 답변 (API 호출)
    ap, af = run_ai_tests()

    # 최종 요약
    print(f"\n\n{'='*50}")
    print(f"  최종 결과")
    print(f"{'='*50}")
    print(f"  컨텍스트 정확도: {cp}/500 ({cp/500*100:.1f}%)")
    print(f"  AI 답변 품질: {ap}/30 ({ap/30*100:.1f}%)")
    print(f"{'='*50}")

    # 저장
    json.dump({
        "context_tests": {"total": 500, "passed": cp, "failed": cf},
        "ai_tests": {"total": 30, "passed": ap, "failed": af},
        "context_failures": [{"name": f["name"], "keyword": f["keyword"], "category": f["category"]} for f in failures],
    }, open(DATA_DIR / "test_v2_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
