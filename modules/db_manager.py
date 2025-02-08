import sqlite3
import threading
from datetime import datetime

DB_FILE = "downloads.db"
DB_LOCK = threading.Lock()  # To ensure thread safety

def get_connection():
    """
    Get a thread-safe database connection.
    """
    return sqlite3.connect(DB_FILE)


def initialize_database():
    """
    Initialize the database and create necessary tables.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            file_name TEXT,
            output_path TEXT NOT NULL,
            status TEXT CHECK(status IN ('ongoing', 'paused', 'completed', 'failed')) NOT NULL DEFAULT 'ongoing',
            progress INTEGER CHECK(progress BETWEEN 0 AND 100) DEFAULT 0,
            file_size INTEGER,
            start_time TEXT,
            end_time TEXT
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON downloads (status)")
        conn.commit()


def add_download(url, output_path, file_name=None, file_size=None):
    """
    Add a new download entry to the database.
    """
    with DB_LOCK, get_connection() as conn:
        cursor = conn.cursor()
        start_time = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO downloads (url, file_name, output_path, file_size, start_time)
        VALUES (?, ?, ?, ?, ?)
        """, (url, file_name, output_path, file_size, start_time))
        conn.commit()
        return cursor.lastrowid


def update_download_progress(download_id, progress, status=None):
    """
    Update the progress or status of a download.
    """
    with DB_LOCK, get_connection() as conn:
        cursor = conn.cursor()
        end_time = datetime.now().isoformat() if status in ("completed", "failed") else None
        if status:
            cursor.execute("""
            UPDATE downloads
            SET progress = ?, status = ?, end_time = COALESCE(?, end_time)
            WHERE id = ?
            """, (progress, status, end_time, download_id))
        else:
            cursor.execute("""
            UPDATE downloads
            SET progress = ?
            WHERE id = ?
            """, (progress, download_id))
        conn.commit()


def get_all_downloads():
    """
    Fetch all downloads from the database.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM downloads")
        return cursor.fetchall()


def get_downloads_by_status(status):
    """
    Fetch downloads filtered by their status.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM downloads WHERE status = ?", (status,))
        return cursor.fetchall()


def delete_download(download_id):
    """
    Delete a specific download entry from the database.
    """
    with DB_LOCK, get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM downloads WHERE id = ?", (download_id,))
        conn.commit()


def resume_download(download_id):
    """
    Resume a paused or failed download by updating its status to 'ongoing'.
    """
    with DB_LOCK, get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE downloads
        SET status = 'ongoing'
        WHERE id = ? AND status IN ('paused', 'failed')
        """, (download_id,))
        conn.commit()
