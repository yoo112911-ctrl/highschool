import streamlit as st
from db import init_db, get_progress_summary

st.set_page_config(page_title="내 진도", page_icon="📊", layout="wide")
init_db()

if st.session_state.get("user") is None:
    st.warning("로그인이 필요합니다.")
    st.stop()

user = st.session_state.user

st.title("📊 내 진도")

completed, avg_score, by_category = get_progress_summary(user["id"])

col1, col2 = st.columns(2)
col1.metric("시청 완료", f"{completed}개")
col2.metric("퀴즈 평균", f"{avg_score}점")

st.divider()
st.subheader("단원별 진도")

if not by_category:
    st.caption("아직 등록된 영상이 없습니다.")
else:
    for row in by_category:
        total = row["total_videos"] or 0
        done = row["completed_videos"] or 0
        pct = int(done / total * 100) if total else 0
        st.write(f"**{row['category']}**  ({done}/{total})")
        st.progress(pct / 100, text=f"{pct}%")
