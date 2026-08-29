import streamlit as st
from db import init_db, add_video, get_my_videos, add_quiz, CATEGORIES
from utils import extract_youtube_id

st.set_page_config(page_title="영상 업로드", page_icon="⬆️", layout="wide")
init_db()

if st.session_state.get("user") is None:
    st.warning("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user

st.title("⬆️ 영상 올리기")

if user["role"] == "student":
    st.info("제출한 영상은 선생님 승인 후에 다른 학생들에게 공개됩니다.", icon="⏳")

with st.form("upload_form", clear_on_submit=True):
    title = st.text_input("제목")
    category = st.selectbox("카테고리", CATEGORIES)
    youtube_url = st.text_input("유튜브 링크", placeholder="https://www.youtube.com/watch?v=...")
    description = st.text_area("설명 (선택)")

    st.caption("영상에 연결할 형성평가 문항 (선택, 최대 3문항)")
    quiz_inputs = []
    for i in range(3):
        with st.expander(f"문항 {i + 1}"):
            q = st.text_input("질문", key=f"q_{i}")
            a = st.text_input("보기 A", key=f"a_{i}")
            b = st.text_input("보기 B", key=f"b_{i}")
            c = st.text_input("보기 C", key=f"c_{i}")
            d = st.text_input("보기 D", key=f"d_{i}")
            ans = st.selectbox("정답", ["A", "B", "C", "D"], key=f"ans_{i}")
            quiz_inputs.append((q, a, b, c, d, ans))

    submitted = st.form_submit_button("제출하기", use_container_width=True)

    if submitted:
        if not title or not youtube_url:
            st.error("제목과 유튜브 링크는 필수입니다.")
        elif not extract_youtube_id(youtube_url):
            st.error("유효한 유튜브 링크가 아닙니다.")
        else:
            add_video(title, category, youtube_url, description, user["id"])
            # 방금 등록한 영상의 id를 가져와 퀴즈 연결
            my_videos = get_my_videos(user["id"])
            new_video_id = my_videos[0]["id"]  # 최신순 정렬
            for q, a, b, c, d, ans in quiz_inputs:
                if q and a and b and c and d:
                    add_quiz(new_video_id, q, a, b, c, d, ans)
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
