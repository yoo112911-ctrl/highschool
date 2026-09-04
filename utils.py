import re


def extract_youtube_id(url: str) -> str | None:
    """유튜브 URL에서 영상 ID를 추출합니다. 실패 시 None을 반환합니다."""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def youtube_embed_url(url: str) -> str | None:
    vid = extract_youtube_id(url)
    if vid:
        return f"https://www.youtube.com/embed/{vid}"
    return None
