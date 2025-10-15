import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.db")

def init_history_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filetype TEXT NOT NULL,
            converted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_history(filename, filetype, user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (filename, filetype, user_id) VALUES (?, ?, ?)",
        (filename, filetype, user_id)
    )
    conn.commit()
    conn.close()

def get_all_history(user_id, limit=200):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, filetype, converted_at FROM history WHERE user_id=? ORDER BY converted_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_counts(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM history WHERE user_id=? AND filetype='audio'", (user_id,))
    total_audio = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM history WHERE user_id=? AND filetype IN ('docx','pdf')", (user_id,))
    total_converted = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM history WHERE user_id=? AND filetype='docx'", (user_id,))
    docx_count = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM history WHERE user_id=? AND filetype='pdf'", (user_id,))
    pdf_count = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM history WHERE user_id=?", (user_id,))
    total_files = cursor.fetchone()[0] or 0
    conn.close()
    return {
        "total_audio": total_audio,
        "total_converted": total_converted,
        "docx_count": docx_count,
        "pdf_count": pdf_count,
        "total_files": total_files
    }
