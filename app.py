"""💰 돈줄 - 인터넷/TV 사은품 AI 상담"""

import streamlit as st
import csv
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from chatbot.rag import ask, detect_provider

DATA_DIR = Path(__file__).parent / "data"
LEADS_PATH = DATA_DIR / "leads.csv"
TICKET_PATH = DATA_DIR / "ticket_counter.json"

st.set_page_config(page_title="돈줄 - 인터넷TV 사은품", page_icon="💰", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #1a1a2e; color: #e0e0e0; }
    [data-testid="stSidebar"] { display: none; }
    header { display: none; }
    .big-title { font-size: 2.5rem; text-align: center; margin-bottom: 0; color: #2ecc71; }
    .sub-title { text-align: center; color: #aaa; margin-top: 0; font-size: 1.1rem; }
    [data-testid="stChatMessage"] { background: transparent !important; }
    [data-testid="stChatMessageContent"] p { color: #e0e0e0; }
    table { color: #e0e0e0 !important; }
    th { background: #2a2a4a !important; color: #2ecc71 !important; }
    td { background: #16213e !important; color: #e0e0e0 !important; }
    div.stButton > button {
        border-radius: 24px; border: 1px solid #333;
        background: #16213e; color: #ccc; font-size: 14px;
        padding: 8px 16px; transition: all 0.2s;
    }
    div.stButton > button:hover { border-color: #2ecc71; color: #2ecc71; }
    div.stButton > button[kind="primary"] { background: #2ecc71; color: #1a1a2e; border: none; font-weight: bold; }
    .stTextInput input { background: #16213e; color: #e0e0e0; border: 1px solid #333; border-radius: 12px; }
    .stSelectbox > div > div { background: #16213e; color: #e0e0e0; }
    code { background: #2ecc71 !important; color: #1a1a2e !important; padding: 4px 10px !important; border-radius: 8px !important; font-weight: bold !important; }
    .hide-buttons div.stButton { display: none !important; }
    .hide-buttons [data-testid="stAlert"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

PROVIDER_MAP = {"sk": "SKT", "skt": "SKT", "skb": "SKT", "kt": "KT", "lg": "LG U+", "유플": "LG U+", "엘지": "LG U+"}
PROVIDER_KEY = {"SKT": "skt", "KT": "kt", "LG U+": "lg"}
NEED_KW = ["추천", "바꿀", "바꾸", "가입", "변경", "알려", "어때", "좋아", "비교", "뭐가", "어떤", "상담", "싼", "저렴"]


def gen_ticket(prov=""):
    prefix = {"SKT": "S", "KT": "K", "LG U+": "L"}.get(prov, "X")
    counter = json.load(open(TICKET_PATH)) if TICKET_PATH.exists() else {}
    num = counter.get(prefix, 0) + 1
    counter[prefix] = num
    json.dump(counter, open(TICKET_PATH, "w"), indent=2)
    return f"{prefix}{num:03d}"


def save_lead(data):
    fields = ["date", "time", "ticket_id", "type", "name", "phone", "provider", "product", "note", "status"]
    exists = LEADS_PATH.exists()
    with open(LEADS_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            w.writeheader()
        w.writerow({k: data.get(k, "") for k in fields})


def detect_prov(text):
    for kw, prov in PROVIDER_MAP.items():
        if kw in text.lower():
            return prov
    return None


# ===== 메인 =====
st.markdown('<p class="big-title">💰 돈줄</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">인터넷·TV 사은품 받고, 요금도 확 줄여드릴게요!</p>', unsafe_allow_html=True)

# 칩
chips = [("🔴 SKT", "skt", "SKT"), ("🟡 KT", "kt", "KT"), ("🟣 LG U+", "lg", "LG U+"), ("📊 3사 비교", None, "")]
cols = st.columns(len(chips))
for i, (label, pkey, prov) in enumerate(chips):
    with cols[i]:
        if st.button(label, key=f"chip_{i}", use_container_width=True):
            q = f"{prov} 인터넷 TV 추천해줘" if prov else "3사 인터넷 TV 요금 비교해줘"
            if "messages" not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "user", "content": q})
            if prov:
                st.session_state["last_provider"] = prov
            st.session_state["run"] = {"q": q, "pkey": pkey}
            st.rerun()

# 세션 초기화
for key, val in [("messages", []), ("show_lead", False), ("last_provider", ""), ("waiting_prov", False), ("pending_q", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

# 이전 메시지
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="💰" if msg["role"] == "assistant" else "🙋"):
        st.markdown(msg["content"])

# 통신사 선택
if st.session_state.waiting_prov:
    with st.chat_message("assistant", avatar="💰"):
        st.markdown("**어떤 통신사 상품을 보여드릴까요?**")
        cols = st.columns(4)
        for i, p in enumerate(["SKT", "KT", "LG U+", "전체 비교"]):
            with cols[i]:
                if st.button(p, key=f"prov_{p}", use_container_width=True):
                    st.session_state.waiting_prov = False
                    st.session_state.messages.append({"role": "user", "content": p})
                    pkey = PROVIDER_KEY.get(p)
                    if p != "전체 비교":
                        st.session_state.last_provider = p
                    st.session_state["run"] = {"q": st.session_state.pending_q, "pkey": pkey}
                    st.session_state.pending_q = None
                    st.rerun()

# 상품번호 → 상품정보 조회
def _get_product_info(pid):
    cat_path = DATA_DIR / "product_catalog.json"
    if cat_path.exists() and pid:
        catalog = json.load(open(cat_path, encoding="utf-8"))
        p = catalog.get(pid.strip().upper(), {})
        if p:
            return f"{p['provider']} {p['name']} {p['speed']} (1대결합 {p['price']:,}원)"
    return ""

# 상담 팝업
@st.dialog("📞 바로 상담 연결")
def direct_dialog():
    prov = st.session_state.last_provider
    pid = st.session_state.get("selected_pid", "")
    info = st.session_state.get("selected_info", "")
    ticket = pid if pid else gen_ticket(prov)

    if info:
        st.markdown(f"📦 **{pid}** — {info}")
    st.markdown(f"🎫 티켓: **`{ticket}`**")
    st.markdown("---")
    st.markdown("### 📞 1833-3504")
    st.caption("전화하시고 티켓번호만 말씀해주세요!")

    if st.button("✅ 확인", use_container_width=True, type="primary"):
        product_str = f"[{pid}] {info}" if info else prov
        save_lead({"date": datetime.now().strftime("%Y-%m-%d"), "time": datetime.now().strftime("%H:%M"),
                   "ticket_id": ticket, "type": "바로상담", "provider": prov, "product": product_str, "status": "대기"})
        msg = f"📞 바로상담 🎫 **{ticket}**"
        if info:
            msg += f"\n📦 {pid} — {info}"
        msg += "\n📞 1833-3504"
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.session_state["selected_pid"] = ""
        st.session_state["selected_info"] = ""
        st.rerun()

@st.dialog("📋 연락받기 신청")
def callback_dialog():
    prov = st.session_state.last_provider
    pid = st.session_state.get("selected_pid", "")
    info = st.session_state.get("selected_info", "")
    ticket = pid if pid else gen_ticket(prov)

    if info:
        st.markdown(f"📦 **{pid}** — {info}")
    st.markdown(f"🎫 티켓: **`{ticket}`**")
    st.markdown("---")
    name = st.text_input("이름 *")
    phone = st.text_input("연락처 *", placeholder="010-0000-0000")
    call_time = st.selectbox("연락 시간", ["가능한 빨리", "오전", "오후", "저녁"])

    if st.button("📞 신청", use_container_width=True, type="primary"):
        if name and phone:
            product_str = f"[{pid}] {info}" if info else prov
            save_lead({"date": datetime.now().strftime("%Y-%m-%d"), "time": datetime.now().strftime("%H:%M"),
                       "ticket_id": ticket, "type": "연락받기", "name": name, "phone": phone,
                       "provider": prov, "product": product_str, "note": call_time, "status": "대기"})
            msg = f"✅ 신청완료 🎫 **{ticket}**"
            if info:
                msg += f"\n📦 {pid} — {info}"
            msg += f"\n👤 {name} | 📞 {phone} | {call_time}"
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.session_state["selected_pid"] = ""
            st.session_state["selected_info"] = ""
            st.rerun()
        else:
            st.error("이름/연락처 필수!")

# AI 답변
if st.session_state.get("run"):
    run = st.session_state.pop("run")
    with st.chat_message("assistant", avatar="💰"):
        with st.spinner("💰 사은품 찾는 중..."):
            try:
                answer = ask(run["q"], provider_key=run["pkey"], chat_history=st.session_state.messages)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"오류: {e}")

    # BEST 추천 상품번호 저장
    import re
    best_pids = []
    for line in answer.split("\n"):
        if "🥇" in line or "🥈" in line or "1위" in line or "2위" in line or "추천" in line or "상담 신청" in line:
            found = re.findall(r'[SKL]\d{3}', line)
            best_pids.extend(found)
    # 못 찾으면 답변 전체에서 추출
    if not best_pids:
        best_pids = re.findall(r'[SKL]\d{3}', answer)
    st.session_state["best_pids"] = list(dict.fromkeys(best_pids))[:2]

# 추천 상품 선택 버튼 (run 블록 밖)
if st.session_state.get("best_pids"):
    st.markdown("**🎯 추천 상품 선택**")
    cols = st.columns(len(st.session_state["best_pids"]))
    for i, pid in enumerate(st.session_state["best_pids"]):
        info = _get_product_info(pid)
        short = info.split("(")[0].strip() if info else pid
        with cols[i]:
            if st.button(f"{'🥇' if i==0 else '🥈'} {pid} {short}", key=f"pick_{pid}", use_container_width=True):
                st.session_state["selected_pid"] = pid
                st.session_state["selected_info"] = info
                st.rerun()

# 선택 표시 + 상담 버튼 (추천 있을 때만 렌더링)
if st.session_state.get("best_pids"):
    if st.session_state.get("selected_pid"):
        st.success(f"✅ **{st.session_state['selected_pid']}** — {st.session_state.get('selected_info','')}")
    _has = bool(st.session_state.get("selected_pid"))
    _c1, _c2 = st.columns(2)
    with _c1:
        if st.button("📞 바로 상담", key="best_direct", use_container_width=True, type="primary", disabled=not _has):
            direct_dialog()
    with _c2:
        if st.button("📋 연락받기", key="best_callback", use_container_width=True, disabled=not _has):
            callback_dialog()

# 채팅 입력
if not st.session_state.waiting_prov:
    prompt = st.chat_input("💬 인터넷·TV 사은품, 요금 뭐든 물어보세요!")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🙋"):
            st.markdown(prompt)

        prov = detect_prov(prompt)
        if not prov and st.session_state.last_provider:
            prov = st.session_state.last_provider

        if any(kw in prompt for kw in NEED_KW) and not prov:
            st.session_state.pending_q = prompt
            st.session_state.waiting_prov = True
            st.rerun()
        else:
            pkey = PROVIDER_KEY.get(prov)
            if prov:
                st.session_state.last_provider = prov

            with st.chat_message("assistant", avatar="💰"):
                if not os.environ.get("ANTHROPIC_API_KEY"):
                    st.warning("API Key 필요!")
                else:
                    with st.spinner("💰 답변 준비 중..."):
                        try:
                            answer = ask(prompt, provider_key=pkey, chat_history=st.session_state.messages)
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        except Exception as e:
                            st.error(f"오류: {e}")

            if any(kw in prompt for kw in NEED_KW):
                import re as _re
                _bpids = []
                for _line in answer.split("\n"):
                    if "🥇" in _line or "🥈" in _line or "1위" in _line or "2위" in _line or "추천" in _line or "상담 신청" in _line:
                        _bpids.extend(_re.findall(r'[SKL]\d{3}', _line))
                if not _bpids:
                    _bpids = _re.findall(r'[SKL]\d{3}', answer)
                st.session_state["best_pids"] = list(dict.fromkeys(_bpids))[:2]
                st.session_state["selected_pid"] = ""
                st.session_state["selected_info"] = ""
                st.rerun()

    pass  # 상담 버튼은 아래 통합

