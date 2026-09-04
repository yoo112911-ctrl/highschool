import secrets
import streamlit as st
from db import (
    init_db, create_user, authenticate, get_user_by_token, set_remember_token,
    clear_remember_token, get_user_by_username, check_hint_answer, reset_password,
)

st.set_page_config(page_title="학습동영상 플랫폼", page_icon="🎬", layout="wide")

init_db()

if "user" not in st.session_state:
    st.session_state.user = None

# ---- 자동 로그인: URL의 토큰으로 자동 로그인 시도 ----
if st.session_state.user is None:
    token = st.query_params.get("token")
    if token:
        user = get_user_by_token(token)
        if user:
            st.session_state.user = user


def login_view():
    st.title("🎬 학습동영상 플랫폼")
    st.caption("영상으로 배우고, 형성평가로 확인하고, 서로 질문해요.")

    tab_login, tab_signup, tab_forgot = st.tabs(["로그인", "회원가입", "비밀번호 찾기"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("아이디")
            password = st.text_input("비밀번호", type="password")
            remember = st.checkbox("자동 로그인 (이 브라우저에서 로그인 유지)")
            submitted = st.form_submit_button("로그인", use_container_width=True)
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    if remember:
                        token = secrets.token_hex(16)
                        set_remember_token(user["id"], token)
                        st.query_params["token"] = token
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    with tab_signup:
        with st.form("signup_form"):
            su_username = st.text_input("아이디", key="su_username")
            su_password = st.text_input("비밀번호", type="password", key="su_password")
            su_password2 = st.text_input("비밀번호 확인", type="password", key="su_password2")
            su_name = st.text_input("이름", key="su_name")
            su_role = st.selectbox("역할", ["student", "teacher"], format_func=lambda x: "학생" if x == "student" else "교사", key="su_role")
            su_class = st.text_input("학년/반 (예: 3-2)", key="su_class")
            su_number = st.text_input("번호 (학생만 입력)", key="su_number")
            st.caption("비밀번호를 잊었을 때 본인 확인용으로 사용할 힌트예요.")
            su_hint_q = st.text_input("힌트 질문 (예: 초등학교 때 별명은?)", key="su_hint_q")
            su_hint_a = st.text_input("힌트 답변", key="su_hint_a")
            su_submitted = st.form_submit_button("가입하기", use_container_width=True)
            if su_submitted:
                if not su_username or not su_password or not su_name:
                    st.error("아이디, 비밀번호, 이름은 필수입니다.")
                elif su_password != su_password2:
                    st.error("비밀번호가 서로 일치하지 않습니다.")
                elif su_role == "student" and not su_number:
                    st.error("학생은 번호를 입력해주세요.")
                elif not su_hint_q or not su_hint_a:
                    st.error("비밀번호 찾기를 위한 힌트 질문과 답변을 입력해주세요.")
                else:
                    ok, msg = create_user(
                        su_username, su_password, su_name, su_role, su_class,
                        su_number or None, su_hint_q, su_hint_a,
                    )
                    if ok:
                        st.success(msg + " 로그인 탭에서 로그인해주세요.")
                    else:
                        st.error(msg)

    with tab_forgot:
        st.caption("아이디를 입력하면 가입할 때 설정한 힌트 질문이 표시돼요.")
        fp_username = st.text_input("아이디", key="fp_username")

        if fp_username:
            user = get_user_by_username(fp_username)
            if not user:
                st.error("존재하지 않는 아이디입니다.")
            elif not user.get("hint_question"):
                st.error("이 계정은 힌트가 설정되어 있지 않습니다.")
            else:
                st.info(f"힌트 질문: {user['hint_question']}")
                with st.form("forgot_form"):
                    fp_answer = st.text_input("힌트 답변")
                    fp_new_pw = st.text_input("새 비밀번호", type="password")
                    fp_new_pw2 = st.text_input("새 비밀번호 확인", type="password")
                    fp_submitted = st.form_submit_button("비밀번호 재설정", use_container_width=True)
                    if fp_submitted:
                        if not check_hint_answer(fp_username, fp_answer):
                            st.error("힌트 답변이 일치하지 않습니다.")
                        elif not fp_new_pw:
                            st.error("새 비밀번호를 입력해주세요.")
                        elif fp_new_pw != fp_new_pw2:
                            st.error("새 비밀번호가 서로 일치하지 않습니다.")
                        else:
                            reset_password(fp_username, fp_new_pw)
                            st.success("비밀번호가 재설정되었습니다. 로그인 탭에서 로그인해주세요.")


def main_view():
    st.sidebar.title(f"👋 {st.session_state.user['name']}님")
    role_label = "교사" if st.session_state.user["role"] == "teacher" else "학생"
    number_part = f" · {st.session_state.user['student_number']}번" if st.session_state.user.get("student_number") else ""
    st.sidebar.caption(f"{role_label} · {st.session_state.user.get('grade_class') or ''}{number_part}")
    if st.sidebar.button("로그아웃", use_container_width=True):
        clear_remember_token(st.session_state.user["id"])
        st.session_state.user = None
        st.query_params.clear()
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
