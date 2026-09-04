import streamlit as st
from db import (
    init_db, get_video, upsert_progress, get_progress, get_quizzes,
    save_quiz_result, add_comment, get_comments,
)
from utils import extract_youtube_id
from youtube_tracker import youtube_progress_tracker

st.set_page_config(page_title="영상 시청", page_icon="▶️", layout="wide")
init_db()

if st.session_state.get("user") is None:
    st.warning("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user
video_id = st.session_state.get("selected_video_id")

if not video_id:
    st.info("영상 목록에서 시청할 영상을 먼저 선택해주세요.")
    st.stop()

video = get_video(video_id)
if not video:
    st.error("영상을 찾을 수 없습니다.")
    st.stop()

st.title(video["title"])
st.caption(f"{video['category']} · {video['uploader_name']} 업로드")

yt_id = extract_youtube_id(video["youtube_url"])
if yt_id:
    result = youtube_progress_tracker(yt_id, key=f"yt_tracker_{video['id']}")
    if result and result.get("video_id") == yt_id and result.get("percent") is not None:
        upsert_progress(user["id"], video["id"], int(result["percent"]))
else:
    st.error("영상 링크를 재생할 수 없습니다.")

if video.get("description"):
    st.write(video["description"])

st.divider()

# ---- 진도 ----
progress = get_progress(user["id"], video["id"])
current_pct = progress["watched_percent"] if progress else 0

st.subheader("📈 시청 진도")
st.progress(current_pct / 100, text=f"자동으로 감지된 시청 진도 {current_pct}%")
st.caption("영상을 재생하면 시청한 만큼 진도가 자동으로 올라가요.")

with st.expander("자동으로 안 올라가면 여기서 직접 수정하세요"):
    manual_pct = st.slider("시청 진도 수동 입력", 0, 100, current_pct, step=10)
    if st.button("진도 저장"):
        upsert_progress(user["id"], video["id"], manual_pct)
        st.success("진도가 저장되었습니다.")
        st.rerun()

st.divider()

# ---- 형성평가 ----
st.subheader("✏️ 형성평가")
quizzes = get_quizzes(video["id"])

if not quizzes:
    st.caption("이 영상에 연결된 형성평가가 아직 없습니다.")
else:
    with st.form("quiz_form"):
        answers = {}
        for i, q in enumerate(quizzes):
            st.markdown(f"**{i + 1}. {q['question']}**")
            st.markdown(
                f"A. {q['option_a']}  \nB. {q['option_b']}  \nC. {q['option_c']}  \nD. {q['option_d']}"
            )
            answers[q["id"]] = st.radio(
                "답을 선택하세요",
                ["A", "B", "C", "D"],
                key=f"quiz_{q['id']}",
                horizontal=True,
            )
            st.markdown("")
        submitted = st.form_submit_button("제출하기")
        if submitted:
            score = sum(1 for q in quizzes if answers[q["id"]] == q["answer"])
            save_quiz_result(user["id"], video["id"], score, len(quizzes))
            st.success(f"채점 결과: {score} / {len(quizzes)}")

st.divider()

# ---- 댓글 ----
st.subheader("💬 댓글")
comments = get_comments(video["id"])

if not comments:
    st.caption("아직 댓글이 없습니다. 첫 댓글을 남겨보세요.")
else:
    for c in comments:
        role_badge = " 🧑‍🏫" if c["user_role"] == "teacher" else ""
        st.markdown(f"**{c['user_name']}{role_badge}**  ·  {c['created_at']}")
        st.write(c["content"])
        st.markdown("---")

with st.form("comment_form", clear_on_submit=True):
    content = st.text_area("댓글을 입력하세요", label_visibility="collapsed", placeholder="질문이나 의견을 남겨보세요")
    if st.form_submit_button("댓글 등록"):
        if content.strip():
            add_comment(video["id"], user["id"], content.strip())
            st.rerun()
        else:
            st.error("댓글 내용을 입력해주세요.")
