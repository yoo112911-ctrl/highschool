import streamlit as st
from db import init_db, get_approved_videos, get_progress, CATEGORIES

st.set_page_config(page_title="영상 목록", page_icon="📚", layout="wide")
init_db()

if st.session_state.get("user") is None:
    st.warning("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user

st.title("📚 영상 목록")

category = st.selectbox("카테고리", ["전체"] + CATEGORIES)
videos = get_approved_videos(category)

if not videos:
    st.info("아직 공개된 영상이 없습니다.")
else:
    for v in videos:
        with st.container(border=True):
            cols = st.columns([5, 2, 2, 1])
            with cols[0]:
                st.markdown(f"**{v['title']}**")
                st.caption(f"{v['category']} · {v['uploader_name']}{' (학생)' if v['uploader_role'] == 'student' else ' (교사)'}")
            with cols[1]:
                p = get_progress(user["id"], v["id"])
                pct = p["watched_percent"] if p else 0
                st.progress(pct / 100, text=f"진도 {pct}%")
            with cols[2]:
                st.caption(v.get("description") or "")
            with cols[3]:
                if st.button("시청하기", key=f"watch_{v['id']}", use_container_width=True):
                    st.session_state.selected_video_id = v["id"]
                    st.switch_page("pages/2_영상시청.py")
