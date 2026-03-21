"""AJD 3사 인터넷/TV/결합 크롤러 - 깔끔한 정제 데이터"""

import json
import re
import sys
import requests
from bs4 import BeautifulSoup
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

URLS = {
    "skt": "https://www.ajd.co.kr/internet/list/sys:product:internet:skt",
    "kt": "https://www.ajd.co.kr/internet/list/sys:product:internet:kt",
    "lg": "https://www.ajd.co.kr/internet/list/sys:product:internet:lg",
}

PROVIDER_NAMES = {"skt": "SKT", "kt": "KT", "lg": "LG U+"}


def crawl():
    print("[AJD 크롤러] 시작...")
    all_data = {}

    for key, url in URLS.items():
        print(f"\n  [{PROVIDER_NAMES[key]}] {url}")
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "lxml")
        tables = soup.select("table")

        provider_data = parse_all_tables(tables, key)

        # 테이블 외 페이지 콘텐츠도 파싱
        provider_data["page_content"] = parse_page_content(soup)

        all_data[key] = provider_data

        # 통신사별 개별 저장
        save_json(f"{key}.json", provider_data)
        print(f"  → {key}.json 저장 완료")

    # 전체 통합 저장
    save_json("all_providers.json", all_data)
    print(f"\n[AJD 크롤러] 완료 → data/all_providers.json")
    return all_data


def parse_all_tables(tables, provider_key):
    """모든 테이블을 유형별로 정제"""
    data = {
        "provider": PROVIDER_NAMES[provider_key],
        "internet_tv": [],       # 인터넷+TV 요금표
        "bundle_types": [],      # 결합 종류/조건
        "bundle_discount": [],   # 결합할인 상세 (총액결합 등)
        "cards": [],             # 제휴카드
        "settop_box": [],        # 셋톱박스
        "ott_support": [],       # OTT 지원
        "wifi": [],              # 와이파이 옵션
        "install_fee": {},       # 설치비
        "phone_plans": [],       # 유선전화
        "long_term_discount": [],# 장기고객 할인
    }

    for i, table in enumerate(tables):
        rows = table.select("tr")
        if not rows:
            continue
        first_text = rows[0].get_text(strip=True)

        # 전체 테이블 텍스트로도 판별
        all_text = table.get_text(strip=True)

        if "인터넷 상품" in first_text or ("모바일결합" in first_text and "100M" in first_text):
            data["internet_tv"] = parse_internet_tv(table)
        elif "결합 종류" in first_text:
            data["bundle_types"] = parse_generic_table(table)
        elif "결합 조건" in all_text and ("할인" in all_text or "결합" in first_text):
            # SKT 요즘 가족결합 등
            data["bundle_types"].append(parse_generic_table(table)) if isinstance(data["bundle_types"], list) else None
            if not data["bundle_types"]:
                data["bundle_types"] = parse_generic_table(table)
            else:
                data["bundle_types"].extend(parse_generic_table(table))
        elif "월 요금 합산" in first_text or "월요금합산" in first_text:
            data["bundle_discount"] = parse_generic_table(table)
        elif "월 요금" in first_text and ("회선" in first_text or "회선" in all_text):
            data["bundle_discount"] = parse_generic_table(table)
        elif "카드사" in first_text or "카드명" in first_text:
            data["cards"] = parse_cards(table)
        elif "셋톱박스" in first_text or "임대료" in first_text:
            data["settop_box"] = parse_generic_table(table)
        elif "유튜브" in first_text or "넷플릭스" in first_text:
            data["ott_support"] = parse_generic_table(table)
        elif ("특징" in first_text and ("100M" in first_text or "100메가" in first_text)):
            data["wifi"] = parse_generic_table(table)
        elif "인터넷 단독" in first_text or ("평일" in all_text and "주말" in all_text and "설치" not in first_text):
            data["install_fee"] = parse_install_fee(table)
        elif "요금제" in first_text and "월 요금" in first_text and "무료" in first_text:
            data["phone_plans"] = parse_generic_table(table)
        elif "년 미만" in first_text or "가입년수" in first_text or "가입년수" in all_text:
            data["long_term_discount"] = parse_generic_table(table)

    return data


def parse_internet_tv(table):
    """인터넷+TV 요금표를 정제된 구조로 파싱"""
    rows = table.select("tr")
    products = []
    current_product = ""

    for row in rows[2:]:  # 헤더 2줄 스킵
        cells = row.select("th, td")
        texts = [c.get_text(strip=True) for c in cells]
        if not texts:
            continue

        # rowspan 있는 셀 = 상품명
        rowspan_cells = row.select("[rowspan]")
        if rowspan_cells:
            current_product = rowspan_cells[0].get_text(strip=True)

        # 채널수 추출
        channels = ""
        ch_match = re.search(r"(\d+)\s*채널", current_product)
        if ch_match:
            channels = ch_match.group(1)

        # 상품명 정리 (채널수 제거)
        clean_name = re.sub(r"\d+채널", "", current_product).strip()

        # 미결합/1대결합 구분
        if "미결합" in " ".join(texts):
            # 미결합 행: 요금 + 사은품 교차
            prices = re.findall(r"([\d,]+)원", " ".join(texts))
            gifts = re.findall(r"(\d+만)원", " ".join(texts))

            product = {
                "name": clean_name,
                "channels": channels,
                "type": "미결합",
            }
            if len(prices) >= 3:
                product["price_100m"] = int(prices[0].replace(",", ""))
                product["price_500m"] = int(prices[1].replace(",", ""))
                product["price_1g"] = int(prices[2].replace(",", ""))
            if len(gifts) >= 1:
                product["gift_100m"] = gifts[0]
            if len(gifts) >= 2:
                product["gift_500m"] = gifts[1]
            if len(gifts) >= 3:
                product["gift_1g"] = gifts[2]

            products.append(product)

        elif "결합" in " ".join(texts):
            # 1대결합 행: 요금만
            prices = re.findall(r"([\d,]+)(?:원)?", " ".join(texts))
            # 숫자만 필터 (4자리 이상)
            prices = [p.replace(",", "") for p in prices if len(p.replace(",", "")) >= 4]

            product = {
                "name": clean_name,
                "channels": channels,
                "type": "1대결합",
            }
            if len(prices) >= 3:
                product["price_100m"] = int(prices[0])
                product["price_500m"] = int(prices[1])
                product["price_1g"] = int(prices[2])
            elif len(prices) >= 1:
                product["price_100m"] = int(prices[0])
                if len(prices) >= 2:
                    product["price_500m"] = int(prices[1])

            products.append(product)

    return products


def parse_cards(table):
    """카드 테이블 파싱"""
    rows = table.select("tr")
    cards = []
    current_issuer = ""

    for row in rows[1:]:  # 헤더 스킵
        cells = row.select("th, td")
        texts = [c.get_text(strip=True) for c in cells]
        if not texts or len(texts) < 2:
            continue

        # rowspan으로 카드사 이어짐
        if len(texts) >= 3:
            current_issuer = texts[0]
            card_name = texts[1]
            benefit = texts[2] if len(texts) > 2 else ""
        elif len(texts) == 2:
            card_name = texts[0]
            benefit = texts[1]
        else:
            continue

        # 할인금액 추출
        amount_match = re.search(r"([\d,]+)원\s*할인", benefit)
        amount = int(amount_match.group(1).replace(",", "")) if amount_match else 0

        # 실적 추출
        perf_match = re.search(r"([\d,]+)만?원\s*이상\s*실적", benefit)
        performance = perf_match.group(0) if perf_match else ""

        # 기간 추출
        period_match = re.search(r"\((\d+~?\d*개월)\)", benefit)
        period = period_match.group(1) if period_match else ""

        cards.append({
            "issuer": current_issuer,
            "name": card_name,
            "benefit": benefit,
            "discount_amount": amount,
            "min_performance": performance,
            "period": period,
        })

    return cards


def parse_install_fee(table):
    """설치비 테이블"""
    rows = table.select("tr")
    result = {}
    headers = []

    for row in rows:
        cells = row.select("th, td")
        texts = [c.get_text(strip=True) for c in cells]
        if not texts:
            continue
        if "구분" in texts[0] or "인터넷" in texts[0]:
            headers = texts
        else:
            label = texts[0]
            for j, val in enumerate(texts[1:], 1):
                key = headers[j] if j < len(headers) else f"col_{j}"
                result[f"{label}_{key}"] = val

    return result


def parse_generic_table(table):
    """범용 테이블 → 딕셔너리 리스트"""
    rows = table.select("tr")
    headers = []
    result = []

    for row in rows:
        cells = row.select("th, td")
        texts = [c.get_text(strip=True) for c in cells]
        if not texts:
            continue

        ths = row.select("th")
        tds = row.select("td")

        if ths and not tds:
            headers = texts
            continue

        if headers:
            row_dict = {}
            for j, val in enumerate(texts):
                key = headers[j] if j < len(headers) else f"col_{j}"
                row_dict[key] = val
            result.append(row_dict)
        else:
            result.append({"cells": texts})

    return result


def parse_page_content(soup):
    """테이블 외 페이지 전체 콘텐츠 파싱 - TV단독요금, 할인안내, 설치안내 등"""
    # 원본 보존 후 테이블 제거
    import copy
    soup_copy = copy.copy(soup)
    for table in soup_copy.select("table"):
        table.decompose()

    text = soup_copy.get_text(separator="\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 3]

    content = {
        "tv_standalone": [],
        "discount_guide": [],
        "install_guide": [],
        "full_text": [],
    }

    # TV 단독 요금 추출
    i = 0
    while i < len(lines):
        line = lines[i]
        # "경제적인 요금의 채널" + 다음 줄 "월 XX,XXX원" 패턴
        if ("채널" in line or "콘텐츠" in line or "디즈니" in line) and i + 1 < len(lines):
            next_line = lines[i + 1]
            price_match = re.search(r"월\s*([\d,]+)원", next_line)
            if price_match:
                content["tv_standalone"].append({
                    "name": line,
                    "monthly_price": int(price_match.group(1).replace(",", "")),
                })
                i += 2
                continue
        i += 1

    # 할인 안내 (STEP 1)
    in_discount = False
    discount_lines = []
    for line in lines:
        if "할인은 오직" in line or "할인크기" in line or "할인혜택" in line or "결합할인은 필수" in line:
            in_discount = True
        if in_discount:
            discount_lines.append(line)
        if in_discount and ("STEP 2" in line or "셋톱" in line):
            in_discount = False

    if discount_lines:
        content["discount_guide"] = discount_lines

    # 설치/사은품 안내 (STEP 3)
    in_install = False
    install_lines = []
    for line in lines:
        if "설치" in line and ("사은품" in line or "STEP" in line):
            in_install = True
        if in_install:
            install_lines.append(line)
        if in_install and len(install_lines) > 30:
            break

    if install_lines:
        content["install_guide"] = install_lines

    # 전체 유용한 텍스트 (광고/메뉴 제외)
    for line in lines:
        if any(kw in line for kw in ["원", "할인", "결합", "약정", "채널", "속도", "설치", "셋톱", "카드", "사은품"]):
            if len(line) > 5 and len(line) < 200:
                content["full_text"].append(line)

    return content


def save_json(filename, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    crawl()
