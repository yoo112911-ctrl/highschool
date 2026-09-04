import streamlit as st
from db import init_db, add_video, get_my_videos, add_quiz, CATEGORIES
from utils import extract_youtube_id
from ai_quiz import generate_quiz_with_ai, ai_available

st.set_page_config(page_title="영상 업로드", page_icon="⬆️", layout="wide")
init_db()

if st.session_state.get("user") is None:
    st.warning("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user

st.title("⬆️ 영상 올리기")

if user["role"] == "student":
    st.info("제출한 영상은 선생님 승인 후에 다른 학생들에게 공개됩니다.", icon="⏳")

if "ai_quiz" not in st.session_state:
    st.session_state.ai_quiz = None

st.subheader("1. 영상 정보")
title = st.text_input("제목", key="up_title")
category = st.selectbox("카테고리", CATEGORIES, key="up_category")
youtube_url = st.text_input("유튜브 링크", placeholder="https://www.youtube.com/watch?v=...", key="up_url")
description = st.text_area("설명 (선택)", key="up_description")

st.divider()
st.subheader("2. 형성평가 문항 (선택, 최대 3문항)")

if ai_available():
    st.caption("수식이 들어간 문제도 AI가 자동으로 만들어줘요. 영상 제목/카테고리/설명을 참고합니다.")
    if st.button("✨ AI로 형성평가 자동 생성", use_container_width=False):
        if not title:
            st.error("먼저 제목을 입력해주세요.")
        else:
            with st.spinner("AI가 문제를 만들고 있어요..."):
                st.session_state.ai_quiz = generate_quiz_with_ai(title, category, description)
            if st.session_state.ai_quiz:
                st.success(f"{len(st.session_state.ai_quiz)}개 문항이 생성되었습니다. 아래에서 확인하고 필요하면 수정하세요.")
else:
    st.caption("AI 자동 생성을 쓰려면 Streamlit Cloud의 Secrets에 ANTHROPIC_API_KEY를 등록해주세요.")

ai_quiz = st.session_state.ai_quiz or []

with st.form("upload_form", clear_on_submit=False):
    quiz_inputs = []
    for i in range(3):
        prefill = ai_quiz[i] if i < len(ai_quiz) else {}
        with st.expander(f"문항 {i + 1}", expanded=bool(prefill)):
            q = st.text_input("질문 (수식은 $...$ 로 감싸주세요, 예: $x^2+1$)", value=prefill.get("question", ""), key=f"q_{i}")
            a = st.text_input("보기 A", value=prefill.get("option_a", ""), key=f"a_{i}")
            b = st.text_input("보기 B", value=prefill.get("option_b", ""), key=f"b_{i}")
            c = st.text_input("보기 C", value=prefill.get("option_c", ""), key=f"c_{i}")
            d = st.text_input("보기 D", value=prefill.get("option_d", ""), key=f"d_{i}")
            default_ans_idx = ["A", "B", "C", "D"].index(prefill["answer"]) if prefill.get("answer") in ("A", "B", "C", "D") else 0
            ans = st.selectbox("정답", ["A", "B", "C", "D"], index=default_ans_idx, key=f"ans_{i}")
            if q:
                st.caption("미리보기")
                st.markdown(f"**{q}**  \nA. {a}  \nB. {b}  \nC. {c}  \nD. {d}")
            quiz_inputs.append((q, a, b, c, d, ans))

    submitted = st.form_submit_button("제출하기", use_container_width=True)

    if submitted:
        if not title or not youtube_url:
            st.error("제목과 유튜브 링크는 필수입니다.")
        elif not extract_youtube_id(youtube_url):
            st.error("유효한 유튜브 링크가 아닙니다.")
        else:
            add_video(title, category, youtube_url, description, user["id"])
            my_videos = get_my_videos(user["id"])
            new_video_id = my_videos[0]["id"]  # 최신순 정렬
            for q, a, b, c, d, ans in quiz_inputs:
                if q and a and b and c and d:
                    add_quiz(new_video_id, q, a, b, c, d, ans)
            st.session_state.ai_quiz = None
            st.success("제출이 완료되었습니다." + (" 선생님 승인 후 공개됩니다." if user["role"] == "student" else ""))

st.divider()
st.subheader("📋 내가 올린 영상")

my_videos = get_my_videos(user["id"])
status_label = {"pending": "⏳ 승인 대기", "approved": "✅ 공개됨", "rejected": "❌ 반려됨"}

if not my_videos:
    st.caption("아직 올린 영상이 없습니다.")
else:
    for v in my_videos:
        with st.container(border=True):
            cols = st.columns([5, 2])
            with cols[0]:
                st.markdown(f"**{v['title']}**")
                st.caption(f"{v['category']} · {v['created_at']}")
            with cols[1]:
                st.write(status_label.get(v["status"], v["status"]))
