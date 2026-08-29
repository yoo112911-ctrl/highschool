import streamlit as st
from db import init_db, create_user, authenticate

st.set_page_config(page_title="학습동영상 플랫폼", page_icon="🎬", layout="wide")

init_db()

if "user" not in st.session_state:
    st.session_state.user = None


def login_view():
    st.title("🎬 학습동영상 플랫폼")
    st.caption("영상으로 배우고, 형성평가로 확인하고, 서로 질문해요.")

    tab_login, tab_signup = st.tabs(["로그인", "회원가입"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인", use_container_width=True)
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    with tab_signup:
        with st.form("signup_form"):
            su_username = st.text_input("아이디", key="su_username")
            su_password = st.text_input("비밀번호", type="password", key="su_password")
            su_name = st.text_input("이름", key="su_name")
            su_role = st.selectbox("역할", ["student", "teacher"], format_func=lambda x: "학생" if x == "student" else "교사", key="su_role")
            su_class = st.text_input("학년/반 (예: 3-2)", key="su_class")
            su_student_id = st.text_input("학번 (학생만 입력)", key="su_student_id")
            su_submitted = st.form_submit_button("가입하기", use_container_width=True)
            if su_submitted:
                if not su_username or not su_password or not su_name:
                    st.error("아이디, 비밀번호, 이름은 필수입니다.")
                elif su_role == "student" and not su_student_id:
                    st.error("학생은 학번을 입력해주세요.")
                else:
                    ok, msg = create_user(su_username, su_password, su_name, su_role, su_class, su_student_id or None)
                    if ok:
                        st.success(msg + " 로그인 탭에서 로그인해주세요.")
                    else:
                        st.error(msg)


def main_view():
    st.sidebar.title(f"👋 {st.session_state.user['name']}님")
    role_label = "교사" if st.session_state.user["role"] == "teacher" else "학생"
    id_part = f" · {st.session_state.user['student_id']}" if st.session_state.user.get("student_id") else ""
    st.sidebar.caption(f"{role_label} · {st.session_state.user.get('grade_class') or ''}{id_part}")
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.user = None
        st.rerun()

    st.title("🎬 학습동영상 플랫폼")
    st.write("왼쪽 사이드바에서 페이지를 선택해 시작하세요.")
    st.markdown("""
    - **영상 목록**: 단원별 영상을 찾아보고 시청해요
    - **영상 업로드**: 영상을 등록하면 선생님 승인 후 공개돼요
    - **내 진도**: 시청 현황과 형성평가 결과를 확인해요
    """)
    if st.session_state.user["role"] == "teacher":
        st.markdown("- **승인 대기열**: 학생이 올린 영상을 검토해요")


if st.session_state.user is None:
    login_view()
else:
    main_view()
