import json
import streamlit as st

try:
    import anthropic
except ImportError:
    anthropic = None


def ai_available() -> bool:
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        key = None
    return anthropic is not None and bool(key)


def generate_quiz_with_ai(title: str, category: str, description: str, n: int = 3):
    """영상 정보를 바탕으로 객관식 형성평가 문항을 AI로 생성합니다.

    반환값: [{"question": ..., "option_a": ..., ..., "answer": "A"}, ...]
    실패 시 빈 리스트를 반환하고 st.error로 이유를 표시합니다.
    """
    if not ai_available():
        st.error("AI 문제 생성을 사용하려면 Streamlit Cloud의 Secrets에 ANTHROPIC_API_KEY를 설정해주세요.")
        return []

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    prompt = f"""고등학교 수학 영상에 연결할 형성평가 객관식 문항 {n}개를 만들어줘.

영상 제목: {title}
단원: {category}
설명: {description or "(설명 없음)"}

요구사항:
- 문항과 보기에 수식이 필요하면 반드시 LaTeX 문법을 쓰고 인라인은 $...$ 로 감싸줘. 예: $x^2 + 2x + 1$
- 보기는 A, B, C, D 4개
- 정답은 A/B/C/D 중 하나
- 아래 JSON 형식만 출력하고 다른 설명은 절대 붙이지 마.

[
  {{"question": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "answer": "A"}}
]
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.split("\n", 1)[1] if "\n" in text else text
            if text.endswith("json"):
                text = text[:-4]
        quizzes = json.loads(text)
        cleaned = []
        for q in quizzes:
            if all(k in q for k in ("question", "option_a", "option_b", "option_c", "option_d", "answer")):
                if q["answer"].upper() in ("A", "B", "C", "D"):
                    q["answer"] = q["answer"].upper()
                    cleaned.append(q)
        return cleaned
    except Exception as e:
        st.error(f"AI 문제 생성 중 오류가 발생했습니다: {e}")
        return []
