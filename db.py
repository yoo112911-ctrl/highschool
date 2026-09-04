import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'teacher')),
            grade_class TEXT,
            student_id TEXT,
            created_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            description TEXT,
            uploader_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            created_at TEXT NOT NULL,
            FOREIGN KEY (uploader_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            watched_percent INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            UNIQUE(user_id, video_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            answer TEXT NOT NULL CHECK(answer IN ('A', 'B', 'C', 'D')),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (video_id) REFERENCES videos(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- users ----------

def create_user(username, password, name, role, grade_class, student_id=None):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, name, role, grade_class, student_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, hash_password(password), name, role, grade_class, student_id, now_str()),
        )
        conn.commit()
        return True, "가입이 완료되었습니다."
    except sqlite3.IntegrityError:
        return False, "이미 사용 중인 아이디입니다."
    finally:
        conn.close()


def authenticate(username, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password)),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------- videos ----------

def add_video(title, category, youtube_url, description, uploader_id):
    conn = get_conn()
    conn.execute(
        "INSERT INTO videos (title, category, youtube_url, description, uploader_id, status, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
        (title, category, youtube_url, description, uploader_id, now_str()),
    )
    conn.commit()
    conn.close()


def get_approved_videos(category=None):
    conn = get_conn()
    if category and category != "전체":
        rows = conn.execute(
            """SELECT v.*, u.name AS uploader_name, u.role AS uploader_role
               FROM videos v JOIN users u ON v.uploader_id = u.id
               WHERE v.status = 'approved' AND v.category = ?
               ORDER BY v.created_at DESC""",
            (category,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT v.*, u.name AS uploader_name, u.role AS uploader_role
               FROM videos v JOIN users u ON v.uploader_id = u.id
               WHERE v.status = 'approved'
               ORDER BY v.created_at DESC"""
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_videos():
    conn = get_conn()
    rows = conn.execute(
        """SELECT v.*, u.name AS uploader_name, u.grade_class AS uploader_class, u.student_id AS uploader_student_id
           FROM videos v JOIN users u ON v.uploader_id = u.id
           WHERE v.status = 'pending'
           ORDER BY v.created_at ASC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_my_videos(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM videos WHERE uploader_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_video_status(video_id, status):
    conn = get_conn()
    conn.execute("UPDATE videos SET status = ? WHERE id = ?", (status, video_id))
    conn.commit()
    conn.close()


def get_video(video_id):
    conn = get_conn()
    row = conn.execute(
        """SELECT v.*, u.name AS uploader_name FROM videos v
           JOIN users u ON v.uploader_id = u.id WHERE v.id = ?""",
        (video_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------- progress ----------

def upsert_progress(user_id, video_id, watched_percent):
    conn = get_conn()
    completed_at = now_str() if watched_percent >= 90 else None
    conn.execute(
        """INSERT INTO progress (user_id, video_id, watched_percent, completed_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(user_id, video_id) DO UPDATE SET
             watched_percent = MAX(watched_percent, excluded.watched_percent),
             completed_at = COALESCE(progress.completed_at, excluded.completed_at)""",
        (user_id, video_id, watched_percent, completed_at),
    )
    conn.commit()
    conn.close()


def get_progress(user_id, video_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM progress WHERE user_id = ? AND video_id = ?",
        (user_id, video_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_progress_summary(user_id):
    conn = get_conn()
    completed = conn.execute(
        "SELECT COUNT(*) AS n FROM progress WHERE user_id = ? AND completed_at IS NOT NULL",
        (user_id,),
    ).fetchone()["n"]
    avg_score_row = conn.execute(
        "SELECT AVG(score * 100.0 / total) AS avg_score FROM quiz_results WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    avg_score = round(avg_score_row["avg_score"]) if avg_score_row["avg_score"] else 0

    by_category = conn.execute(
        """SELECT v.category,
                  COUNT(DISTINCT v.id) AS total_videos,
                  COUNT(DISTINCT CASE WHEN p.completed_at IS NOT NULL THEN v.id END) AS completed_videos
           FROM videos v
           LEFT JOIN progress p ON p.video_id = v.id AND p.user_id = ?
           WHERE v.status = 'approved'
           GROUP BY v.category""",
        (user_id,),
    ).fetchall()
    conn.close()
    return completed, avg_score, [dict(r) for r in by_category]


# ---------- quizzes ----------

def add_quiz(video_id, question, option_a, option_b, option_c, option_d, answer):
    conn = get_conn()
    conn.execute(
        """INSERT INTO quizzes (video_id, question, option_a, option_b, option_c, option_d, answer)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (video_id, question, option_a, option_b, option_c, option_d, answer),
    )
    conn.commit()
    conn.close()


def get_quizzes(video_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM quizzes WHERE video_id = ?", (video_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_quiz_result(user_id, video_id, score, total):
    conn = get_conn()
    conn.execute(
        "INSERT INTO quiz_results (user_id, video_id, score, total, submitted_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, video_id, score, total, now_str()),
    )
    conn.commit()
    conn.close()


# ---------- comments ----------

def add_comment(video_id, user_id, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO comments (video_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
        (video_id, user_id, content, now_str()),
    )
    conn.commit()
    conn.close()


def get_comments(video_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT c.*, u.name AS user_name, u.role AS user_role
           FROM comments c JOIN users u ON c.user_id = u.id
           WHERE c.video_id = ?
           ORDER BY c.created_at ASC""",
        (video_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


CATEGORIES = ["기하", "미적분", "확률과통계", "대수"]
