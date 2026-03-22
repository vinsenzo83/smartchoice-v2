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

st.set_page_config(page_title="돈줄 - 인터넷TV 사은품", page_icon="💰", layout="centered")

st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    /* ============ 공통 ============ */
    html, body, .stApp {
        background: #0d1117 !important;
        color: #c9d1d9;
        overflow-x: hidden !important;
        font-size: 15px !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }
    [data-testid="stSidebar"], header, footer { display: none !important; }

    .block-container {
        max-width: 600px !important;
        padding: 0 0.8rem 5rem !important;
    }
    /* 요소간 간격 줄이기 */
    .stElementContainer { margin-bottom: 0.15rem !important; }
    .stMarkdown { margin-bottom: 0 !important; }

    /* ---- 헤더 ---- */
    .hero { text-align: center; padding: 0.6rem 0 0.3rem; }
    .hero-icon { font-size: 1.6rem; }
    .hero-title {
        font-size: 1.2rem; font-weight: 800; margin: 0;
        background: linear-gradient(135deg, #3fb950, #2ea043);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-sub { color: #7d8590; font-size: 0.7rem; margin-top: 2px; }

    /* ---- 버튼 ---- */
    div.stButton > button {
        border-radius: 18px;
        border: 1px solid #30363d;
        background: #161b22;
        color: #c9d1d9;
        font-size: 13px; font-weight: 600;
        padding: 6px 4px;
        min-height: 34px;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        border-color: #3fb950; color: #3fb950;
        background: #1c2128;
    }
    div.stButton > button[kind="primary"] {
        background: #238636 !important; color: #fff !important;
        border: none; font-weight: 700;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #2ea043 !important;
    }

    /* ---- 채팅 ---- */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 0.2rem 0 !important;
    }
    [data-testid="stChatMessageContent"] {
        background: #161b22 !important;
        border: 1px solid #21262d !important;
        border-radius: 10px !important;
        padding: 0.5rem 0.7rem !important;
    }
    [data-testid="stChatMessageContent"] p {
        color: #c9d1d9; font-size: 0.95rem; line-height: 1.65;
    }
    [data-testid="stChatMessageContent"] h3 {
        color: #3fb950; font-size: 1.05rem; margin: 0.5rem 0 0.2rem;
    }
    [data-testid="stChatMessageContent"] strong { color: #e6edf3; }

    /* ---- 테이블 ---- */
    table {
        width: 100% !important;
        border-collapse: collapse !important;
        font-size: 0.82rem !important;
        color: #c9d1d9 !important;
        margin: 0.3rem 0 !important;
    }
    th {
        background: #1c2128 !important;
        color: #3fb950 !important;
        font-weight: 600 !important;
        padding: 5px 6px !important;
        font-size: 0.68rem !important;
        border-bottom: 2px solid #30363d !important;
        white-space: nowrap;
        text-align: left !important;
    }
    td {
        padding: 4px 6px !important;
        border-bottom: 1px solid #21262d !important;
        background: transparent !important;
        color: #c9d1d9 !important;
        font-size: 0.7rem !important;
    }
    tr:hover td { background: rgba(63, 185, 80, 0.04) !important; }

    /* ---- 입력창 (하단 고정) ---- */
    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999 !important;
        background: #0d1117 !important;
        border-top: 1px solid #21262d;
        padding: 0.4rem !important;
    }
    [data-testid="stChatInput"] textarea {
        font-size: 16px !important;
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        color: #e6edf3 !important;
    }

    /* ---- 폼 ---- */
    .stTextInput input {
        background: #161b22; color: #e6edf3;
        border: 1px solid #30363d; border-radius: 8px;
        font-size: 16px !important;
    }
    .stTextInput input:focus { border-color: #3fb950; }
    .stSelectbox > div > div { background: #161b22; color: #e6edf3; }

    /* ---- 코드/티켓 ---- */
    code {
        background: #238636 !important; color: #fff !important;
        padding: 2px 8px !important; border-radius: 5px !important;
        font-weight: 700 !important; font-size: 0.72rem !important;
    }

    /* ---- 다이얼로그 ---- */
    [data-testid="stDialog"] > div {
        background: #161b22 !important;
        border: 1px solid #30363d; border-radius: 14px !important;
        width: 95vw !important; max-width: 95vw !important;
    }
    [data-testid="stAlert"] { border-radius: 8px !important; font-size: 0.78rem; }
    [data-testid="stColumn"] { padding: 0 2px !important; }

    /* 모바일에서 columns 가로 배치 강제 */
    @media (max-width: 640px) {
        [data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 4px !important;
        }
        [data-testid="stColumn"] {
            flex: 1 1 0 !important;
            min-width: 0 !important;
            width: auto !important;
        }
    }

    .hide-buttons div.stButton { display: none !important; }

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


# 세션 초기화
for key, val in [("messages", []), ("show_lead", False), ("last_provider", ""), ("pending_q", None), ("survey_done", False), ("page", "landing")]:
    if key not in st.session_state:
        st.session_state[key] = val

# 랜딩 칩 클릭 처리 (query param) → 설문으로 이동 (통신사 미리 선택)
_p = st.query_params.get("p")
if _p and st.session_state.page == "landing":
    _prov_map = {"skt": "SK", "kt": "KT", "lg": "LG", "compare": "무관"}
    if _p in _prov_map:
        st.session_state["sel_provider"] = _prov_map[_p]
        st.session_state.page = "survey"
        st.query_params.clear()
        st.rerun()

# =============================================
# 페이지 1: 랜딩
# =============================================
if st.session_state.page == "landing":
    st.markdown('<div style="height: 25vh"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-size: 1.5rem; font-weight: 800; color: #e6edf3;">💰 돈줄</div>
        <div style="color: #484f58; font-size: 0.72rem; margin-top: 6px;">무엇을 도와드릴까요?</div>
    </div>
    <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; max-width: 320px; margin: 0 auto;">
        <a href="?p=skt" target="_self" style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:22px;background:#161b22;border:1px solid #30363d;color:#c9d1d9;font-size:12px;font-weight:600;text-decoration:none;">
            <span style="width:8px;height:8px;border-radius:50%;background:#E4002B;display:inline-block;"></span> SK 상품보기</a>
        <a href="?p=kt" target="_self" style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:22px;background:#161b22;border:1px solid #30363d;color:#c9d1d9;font-size:12px;font-weight:600;text-decoration:none;">
            <span style="width:8px;height:8px;border-radius:50%;background:#ED1C24;display:inline-block;"></span> KT 상품보기</a>
        <a href="?p=lg" target="_self" style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:22px;background:#161b22;border:1px solid #30363d;color:#c9d1d9;font-size:12px;font-weight:600;text-decoration:none;">
            <span style="width:8px;height:8px;border-radius:50%;background:#E6007E;display:inline-block;"></span> LG 상품보기</a>
        <a href="?p=compare" target="_self" style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:22px;background:#161b22;border:1px solid #30363d;color:#c9d1d9;font-size:12px;font-weight:600;text-decoration:none;">
            <span style="font-size:10px;">📊</span> 3사 비교</a>
    </div>
    """, unsafe_allow_html=True)

# =============================================
# 페이지 2: 설문
# =============================================
elif st.session_state.page == "survey":
    st.markdown("""<style>
        /* 라디오 버튼 컴팩트하게 */
        .survey-page [data-testid="stRadio"] > div { gap: 0.3rem !important; }
        .survey-page [data-testid="stRadio"] label {
            font-size: 0.7rem !important;
            padding: 0 !important;
        }
        .survey-page [data-testid="stRadio"] p { font-size: 0.72rem !important; }
        .survey-page .stElementContainer { margin-bottom: 0rem !important; }
    </style><div class="survey-page">""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding: 0.8rem 0 0.3rem;">
        <span style="font-size:1rem;">💰</span>
        <span style="font-size:0.9rem; font-weight:700; color:#e6edf3;"> 돈줄</span>
    </div>
    <div style="background:#161b22; border:1px solid #21262d; border-radius:12px; padding:0.7rem 0.9rem; margin-bottom:0.8rem;">
        <span style="font-size:0.82rem; color:#c9d1d9; line-height:1.5;">
            안녕하세요! 💰 <b>돈줄</b>이에요~<br>
            사은품 최대로 챙겨드릴게요!<br>
            아래만 선택하면 딱 맞는 상품 추천해드릴게요 👇
        </span>
    </div>
    """, unsafe_allow_html=True)

    family = st.radio("🏠 가족 수", ["1인", "2인", "3~4인", "5인+"], horizontal=True, key="sel_family", index=None)
    usage = st.radio("🖥 용도", ["웹서핑", "OTT", "게임"], horizontal=True, key="sel_usage", index=None)
    tv = st.radio("📺 TV", ["필요", "불필요"], horizontal=True, key="sel_tv", index=None)
    provider = st.radio("📶 통신사", ["무관", "SK", "KT", "LG"], horizontal=True, key="sel_provider",
                        index=["무관", "SK", "KT", "LG"].index(st.session_state.get("sel_provider")) if st.session_state.get("sel_provider") in ["무관", "SK", "KT", "LG"] else None)

    st.markdown('</div>', unsafe_allow_html=True)

    all_selected = family and usage and tv and provider
    if all_selected:
        if st.button("✅ 추천 받기", type="primary", use_container_width=True, key="survey_submit"):
            st.session_state.survey_done = True
            st.session_state.page = "chat"
            prov_map = {"SK": "SKT", "KT": "KT", "LG": "LG U+", "무관": "상관없음"}
            prov_name = prov_map.get(provider, "상관없음")
            pending = st.session_state.get("pending_q", "")
            q = f"{pending + ' / ' if pending else ''}{family} 가구, {usage} 위주, TV {'필요' if tv == '필요' else '불필요'}, 통신사 {prov_name}"
            st.session_state.messages.append({"role": "user", "content": q})
            prov_detect = {"SK": "skt", "KT": "kt", "LG": "lg"}.get(provider)
            if prov_detect:
                st.session_state.last_provider = prov_name
            st.session_state["run"] = {"q": q, "pkey": prov_detect}
            st.rerun()

# =============================================
# 페이지 3: 채팅
# =============================================
elif st.session_state.page == "chat":
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="💰" if msg["role"] == "assistant" else "🙋"):
            st.markdown(msg["content"])

    # 설문 안 했으면 채팅 아래에 설문 표시
    if not st.session_state.survey_done and len(st.session_state.messages) >= 2:
        with st.expander("🎯 맞춤 추천 받기 — 선택하면 딱 맞는 상품 추천해드려요!", expanded=True):
            family = st.radio("🏠 가족 수", ["1인", "2인", "3~4인", "5인+"], horizontal=True, key="sel_family2", index=None)
            usage = st.radio("🖥 용도", ["웹서핑", "OTT", "게임"], horizontal=True, key="sel_usage2", index=None)
            tv = st.radio("📺 TV", ["필요", "불필요"], horizontal=True, key="sel_tv2", index=None)
            provider = st.radio("📶 통신사", ["무관", "SK", "KT", "LG"], horizontal=True, key="sel_provider2", index=None)
            if family and usage and tv and provider:
                if st.button("✅ 추천 받기", type="primary", use_container_width=True, key="survey_chat"):
                    st.session_state.survey_done = True
                    prov_map = {"SK": "SKT", "KT": "KT", "LG": "LG U+", "무관": "상관없음"}
                    prov_name = prov_map.get(provider, "상관없음")
                    q = f"{family} 가구, {usage} 위주, TV {'필요' if tv == '필요' else '불필요'}, 통신사 {prov_name}"
                    st.session_state.messages.append({"role": "user", "content": q})
                    prov_detect = {"SK": "skt", "KT": "kt", "LG": "lg"}.get(provider)
                    if prov_detect:
                        st.session_state.last_provider = prov_name
                    st.session_state["run"] = {"q": q, "pkey": prov_detect}
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

# 채팅 입력 (설문 페이지에서는 숨김)
if st.session_state.page == "survey":
    st.markdown('<style>[data-testid="stChatInput"]{display:none !important;}</style>', unsafe_allow_html=True)
prompt = st.chat_input("💬 인터넷·TV 사은품, 요금 뭐든 물어보세요!")
if prompt:
    # 채팅 입력은 항상 AI가 바로 답변
    if st.session_state.page == "landing":
        st.session_state.page = "chat"
        st.session_state.survey_done = True
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🙋"):
        st.markdown(prompt)
        prov = detect_prov(prompt)
        if not prov and st.session_state.last_provider:
            prov = st.session_state.last_provider
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

    # 추천 상품번호 추출
    import re as _re
    _bpids = []
    for _line in answer.split("\n"):
        if any(kw in _line for kw in ["🥇", "🥈", "추천 1", "추천 2"]):
            _bpids.extend(_re.findall(r'[SKL]\d{3}', _line))
    if not _bpids:
        _bpids = _re.findall(r'[SKL]\d{3}', answer)
    if _bpids:
        st.session_state["best_pids"] = list(dict.fromkeys(_bpids))[:2]
        st.session_state["selected_pid"] = ""
        st.session_state["selected_info"] = ""
        st.rerun()

