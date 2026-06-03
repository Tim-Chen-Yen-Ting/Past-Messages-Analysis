import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).parent / "schema.sql"


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # lets you access columns by name: row["sender"]
    conn.execute("PRAGMA journal_mode=WAL")  # faster bulk inserts
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def create_tables(conn: sqlite3.Connection):
    conn.executescript(SCHEMA.read_text())
    conn.commit()


def upsert_thread(conn: sqlite3.Connection, thread: dict):
    conn.execute("""
        INSERT INTO threads (thread_id, platform, thread_name, is_group, participant_count,
                             first_message_ts, last_message_ts, your_message_count)
        VALUES (:thread_id, :platform, :thread_name, :is_group, :participant_count,
                :first_message_ts, :last_message_ts, :your_message_count)
        ON CONFLICT(thread_id) DO UPDATE SET
            first_message_ts  = MIN(first_message_ts,  excluded.first_message_ts),
            last_message_ts   = MAX(last_message_ts,   excluded.last_message_ts),
            your_message_count = your_message_count + excluded.your_message_count
    """, thread)


def insert_messages(conn: sqlite3.Connection, rows: list[dict]) -> list[int]:
    """Insert a batch of messages and return their new row IDs."""
    ids = []
    for row in rows:
        cur = conn.execute("""
            INSERT INTO messages (platform, thread_id, timestamp_ms, sender,
                                  content, content_type, call_duration, word_count, char_count)
            VALUES (:platform, :thread_id, :timestamp_ms, :sender,
                    :content, :content_type, :call_duration, :word_count, :char_count)
        """, row)
        ids.append(cur.lastrowid)
    return ids


def insert_reactions(conn: sqlite3.Connection, rows: list[dict]):
    conn.executemany("""
        INSERT INTO reactions (message_id, reactor, emoji)
        VALUES (:message_id, :reactor, :emoji)
    """, rows)
