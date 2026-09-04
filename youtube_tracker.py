import os
import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.join(os.path.dirname(__file__), "components", "youtube_tracker")

_component_func = components.declare_component("youtube_tracker", path=_COMPONENT_DIR)


def youtube_progress_tracker(video_id: str, key: str):
    """유튜브 영상을 재생하면서 실시간 시청 진도(%)를 자동으로 추적합니다.

    반환값: {"video_id": ..., "percent": 0~100} 또는 아직 값이 없으면 None
    """
    return _component_func(video_id=video_id, key=key, default=None)
