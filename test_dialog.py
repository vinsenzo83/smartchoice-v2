import streamlit as st

@st.dialog("테스트 팝업")
def my_dialog():
    st.write("팝업 떴다!")
    name = st.text_input("이름")
    if st.button("확인"):
        st.session_state["result"] = name
        st.rerun()

if st.button("팝업 열기"):
    my_dialog()

if "result" in st.session_state:
    st.write(f"결과: {st.session_state.result}")
