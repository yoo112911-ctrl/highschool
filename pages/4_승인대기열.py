import streamlit as st
from db import init_db, get_pending_videos, update_video_status
from utils import youtube_embed_url

st.set_page_config(page_title="승인 대기열", page_icon="🗂️", layout="wide")
init_db()

if st.session_state.get("user") is None:
    st.warning("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user

if user["role"] != "teacher":
    st.error("교사만 접근할 수 있는 페이지입니다.")
    st.stop()

st.title("🗂️ 승인 대기열")

pending = get_pending_videos()

if not pending:
    st.success("승인 대기 중인 영상이 없습니다.")
else:
    st.caption(f"승인 대기 {len(pending)}건")
    for v in pending:
        with st.container(border=True):
            cols = st.columns([3, 2, 1, 1])
            with cols[0]:
                st.markdown(f"**{v['title']}**")
                id_part = f" · {v['uploader_student_id']}" if v.get("uploader_student_id") else ""
                st.caption(f"{v['category']} · {v['uploader_name']} ({v.get('uploader_class') or '-'}){id_part}")
                if v.get("description"):
                    st.write(v["description"])
                embed_url = youtube_embed_url(v["youtube_url"])
                if embed_url:
                    st.video(v["youtube_url"])
            with cols[2]:
                if st.button("✅ 승인", key=f"approve_{v['id']}", use_container_width=True):
                    update_video_status(v["id"], "approved")
                    st.rerun()
            with cols[3]:
                if st.button("❌ 반려", key=f"reject_{v['id']}", use_container_width=True):
                    update_video_status(v["id"], "rejected")
                    st.rerun()
