"""팝업 테스트 - 상품 선택 후 팝업"""
import streamlit as st

st.title("팝업 테스트")

@st.dialog("📞 상담 신청")
def open_consult():
    pid = st.session_state.get("sel", "없음")
    st.write(f"선택한 상품: **{pid}**")
    name = st.text_input("이름")
    if st.button("신청"):
        st.session_state["done"] = f"{pid} - {name}"
        st.rerun()

# 상품 선택
c1, c2 = st.columns(2)
with c1:
    if st.button("S005 선택"):
        st.session_state["sel"] = "S005"
        st.rerun()
with c2:
    if st.button("K020 선택"):
        st.session_state["sel"] = "K020"
        st.rerun()

# 선택 표시
if st.session_state.get("sel"):
    st.success(f"선택: {st.session_state.sel}")

# 상담 버튼 - 항상 최상위
if st.button("📞 상담 신청", type="primary"):
    open_consult()

if st.session_state.get("done"):
    st.write(f"결과: {st.session_state.done}")
