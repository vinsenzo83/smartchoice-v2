"""통신 상품 1차 상담 AI - 리드 생성 → TM 연결"""

import streamlit as st
import json
import csv
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from chatbot.rag import ask, load_and_index, smart_search, get_collection
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
LEADS_PATH = Path(__file__).parent / "data" / "leads.csv"

st.set_page_config(page_title="통신 상품 AI 상담", page_icon="📡", layout="wide")

# 사이드바: 설정 + TM 리드 현황
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Anthropic API Key", type="password", key="api_key")
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key

    st.divider()
    st.header("📊 TM 리드 현황")
    if LEADS_PATH.exists():
        with open(LEADS_PATH, "r", encoding="utf-8") as f:
            leads = list(csv.DictReader(f))
        st.metric("총 상담 신청", f"{len(leads)}건")
        if leads:
            today = datetime.now().strftime("%Y-%m-%d")
            today_leads = [l for l in leads if l.get("date", "").startswith(today)]
            st.metric("오늘 신청", f"{len(today_leads)}건")
            if st.button("리드 목록 보기"):
                st.dataframe([{k: v for k, v in l.items()} for l in leads[-10:]])
    else:
        st.write("아직 상담 신청이 없습니다")

    st.divider()
    if st.button("데이터 재인덱싱"):
        with st.spinner("인덱싱 중..."):
            load_and_index()
        st.success("완료!")

    try:
        collection = get_collection()
        data_files = list(DATA_DIR.glob("*.json")) if DATA_DIR.exists() else []
        if collection.count() == 0 and data_files:
            with st.spinner("최초 인덱싱 중..."):
                load_and_index()
    except Exception:
        pass


# ===== 의도 분석 =====
PROVIDER_MAP = {"sk": "SKT", "skt": "SKT", "skb": "SKT", "브로드": "SKT", "kt": "KT", "케이티": "KT", "lg": "LG U+", "유플": "LG U+", "엘지": "LG U+"}
NEED_INFO_KEYWORDS = ["추천", "바꿀", "바꾸", "가입", "변경", "알려", "어때", "좋아", "비교", "뭐가", "어떤", "상담", "싼", "저렴", "최저"]


def detect_provider(text):
    q = text.lower()
    for kw, prov in PROVIDER_MAP.items():
        if kw in q:
            return prov
    return None


def needs_provider(text):
    q = text.lower()
    return any(kw in q for kw in NEED_INFO_KEYWORDS) and not detect_provider(text)


LEADS_FIELDS = ["date", "time", "ticket_id", "type", "name", "phone", "provider", "product", "speed", "price", "note", "status"]


def save_lead(data):
    """TM 리드 CSV 저장"""
    file_exists = LEADS_PATH.exists()
    with open(LEADS_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEADS_FIELDS)
        if not file_exists:
            writer.writeheader()
        row = {k: data.get(k, "") for k in LEADS_FIELDS}
        writer.writerow(row)


TICKET_COUNTER_PATH = Path(__file__).parent / "data" / "ticket_counter.json"

def generate_ticket_id(provider=""):
    """간단한 티켓 ID: S001, K002, L003, B004"""
    prefix_map = {"SKT": "S", "KT": "K", "LG U+": "L", "SKB": "B"}
    prefix = prefix_map.get(provider, "X")

    # 카운터 로드
    counter = {}
    if TICKET_COUNTER_PATH.exists():
        with open(TICKET_COUNTER_PATH, "r") as f:
            counter = json.load(f)

    num = counter.get(prefix, 0) + 1
    counter[prefix] = num

    with open(TICKET_COUNTER_PATH, "w") as f:
        json.dump(counter, f)

    return f"{prefix}{num:03d}"


# ===== 메인 =====
st.title("📡 통신 상품 AI 상담")
st.caption("인터넷 · TV · 결합상품 · 제휴카드 — 최저가 맞춤 상담")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_lead_form" not in st.session_state:
    st.session_state.show_lead_form = False
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "waiting_provider" not in st.session_state:
    st.session_state.waiting_provider = False

# 이전 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ===== 통신사 선택 (필요할 때만) =====
if st.session_state.waiting_provider:
    with st.chat_message("assistant"):
        st.markdown("**어떤 통신사 상품을 보여드릴까요?**")
        cols = st.columns(5)
        for i, p in enumerate(["SKT", "KT", "LG U+", "전체 비교"]):
            with cols[i]:
                if st.button(p, key=f"prov_{p}", use_container_width=True):
                    st.session_state.waiting_provider = False
                    selected = p if p != "전체 비교" else None
                    question = st.session_state.pending_question

                    if selected:
                        full_prompt = f"[사용자 프로필]\n통신사: {selected}\n\n사용자 질문: {question}"
                    else:
                        full_prompt = f"[사용자 프로필]\n통신사: 전체 비교\n\n사용자 질문: {question}"

                    st.session_state.messages.append({"role": "user", "content": f"{p} 선택"})
                    st.session_state.pending_question = None
                    st.session_state["run_prompt"] = full_prompt
                    st.rerun()

# ===== 상담 신청 폼 =====
if st.session_state.show_lead_form:
    lead_type = st.session_state.get("lead_type", "callback")
    provider = st.session_state.get("last_provider", "")

    with st.chat_message("assistant"):
        if lead_type == "direct":
            # 바로 상담 연결
            ticket_id = generate_ticket_id(provider)
            st.session_state["current_ticket"] = ticket_id

            st.markdown(f"""### 📞 바로 상담 연결

🎫 **티켓번호: `{ticket_id}`**

아래 번호로 전화하시고 티켓번호를 말씀해주세요.
상담사가 바로 상품 정보를 확인할 수 있습니다.

| 통신사 | 상담 전화번호 |
|--------|--------------|
| SKT/SKB | **1600-0000** |
| KT | **1600-0001** |
| LG U+ | **1600-0002** |

> 💡 티켓번호 `{ticket_id}`를 말씀하시면 대기 없이 바로 상담 가능합니다.
""")
            # 리드 저장 (바로상담)
            save_lead({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"),
                "ticket_id": ticket_id,
                "type": "바로상담",
                "provider": provider,
                "status": "대기",
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"🎫 티켓번호 **{ticket_id}** 발급 완료! 전화 상담 시 이 번호를 말씀해주세요."
            })
            st.session_state.show_lead_form = False
            if st.button("확인", key="direct_done"):
                st.rerun()

        else:
            # 연락받기
            ticket_id = generate_ticket_id(provider)
            st.session_state["current_ticket"] = ticket_id

            st.markdown(f"### 📋 연락받기 신청")
            st.markdown(f"🎫 티켓번호: **`{ticket_id}`**")

            with st.form("lead_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("이름 *")
                    phone = st.text_input("연락처 *", placeholder="010-0000-0000")
                with col2:
                    product = st.selectbox("희망 상품", ["인터넷", "인터넷+TV", "인터넷+TV+전화", "모바일 요금제", "기타"])
                    call_time = st.selectbox("희망 연락 시간", ["가능한 빨리", "오전 (9~12시)", "오후 (12~18시)", "저녁 (18~21시)"])
                note = st.text_input("요청사항 (선택)", placeholder="예: 현재 타사 사용 중, 위약금 문의")

                submitted = st.form_submit_button("📞 연락받기 신청", use_container_width=True, type="primary")
                if submitted:
                    if name and phone:
                        save_lead({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "time": datetime.now().strftime("%H:%M"),
                            "ticket_id": ticket_id,
                            "type": "연락받기",
                            "name": name,
                            "phone": phone,
                            "provider": provider,
                            "product": product,
                            "note": f"[{call_time}] {note}",
                            "status": "대기",
                        })
                        st.success(f"""✅ **신청 완료!**

🎫 티켓번호: **{ticket_id}**
📞 {call_time}에 **{phone}**으로 연락드리겠습니다.

티켓번호를 메모해주세요. 상담 시 빠르게 안내받으실 수 있습니다.""")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"✅ 연락받기 신청 완료!\n🎫 티켓: **{ticket_id}** | {name} | {phone} | {product} | {call_time}"
                        })
                        st.session_state.show_lead_form = False
                        st.rerun()
                    else:
                        st.error("이름과 연락처는 필수입니다.")

# ===== AI 답변 생성 트리거 =====
if st.session_state.get("run_prompt"):
    full_prompt = st.session_state.pop("run_prompt")

    with st.chat_message("assistant"):
        with st.spinner("맞춤 상품 분석 중..."):
            try:
                answer = ask(full_prompt, chat_history=st.session_state.messages)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"오류 발생: {e}")

    # 상담 신청 버튼 2개
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📞 바로 상담 연결", key="direct_btn", use_container_width=True, type="primary"):
            st.session_state.show_lead_form = True
            st.session_state["lead_type"] = "direct"
            st.rerun()
    with col_b:
        if st.button("📋 연락받기 신청", key="callback_btn", use_container_width=True):
            st.session_state.show_lead_form = True
            st.session_state["lead_type"] = "callback"
            st.rerun()

# ===== 채팅 입력 =====
if not st.session_state.waiting_provider and not st.session_state.show_lead_form:
    prompt = st.chat_input("무엇이든 물어보세요! 예: 인터넷 바꿀건데 추천해줘")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 통신사 감지
        provider = detect_provider(prompt)

        if needs_provider(prompt):
            # 통신사 정보 없음 → 버튼으로 물어보기
            st.session_state.pending_question = prompt
            st.session_state.waiting_provider = True
            st.rerun()
        else:
            # 바로 답변
            if provider:
                st.session_state["last_provider"] = provider
                full_prompt = f"[사용자 프로필]\n통신사: {provider}\n\n사용자 질문: {prompt}"
            else:
                full_prompt = prompt

            with st.chat_message("assistant"):
                if not os.environ.get("ANTHROPIC_API_KEY"):
                    st.warning("사이드바에서 Anthropic API Key를 입력해주세요.")
                else:
                    with st.spinner("답변 생성 중..."):
                        try:
                            answer = ask(full_prompt, chat_history=st.session_state.messages)
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        except Exception as e:
                            st.error(f"오류 발생: {e}")

            # 상담 신청 버튼 (추천/비교 답변 후)
            if any(kw in prompt for kw in NEED_INFO_KEYWORDS):
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("📞 바로 상담 연결", key="direct_btn2", use_container_width=True, type="primary"):
                        st.session_state.show_lead_form = True
                        st.session_state["lead_type"] = "direct"
                        st.rerun()
                with col_b:
                    if st.button("📋 연락받기 신청", key="callback_btn2", use_container_width=True):
                        st.session_state.show_lead_form = True
                        st.session_state["lead_type"] = "callback"
                        st.rerun()
