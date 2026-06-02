"""
Usage:
    python main.py --data <path_to_data_folder> --db messages.db --you "Tim Chen"

Example:
    python main.py --data "e:/past_msg/data" --db messages.db --you "Tim Chen"
"""

import argparse
from pathlib import Path

import db as database
from data_parser import parse_thread


def ingest_platform(inbox: Path, platform: str, conn, your_name: str):
    if not inbox.exists():
        print(f"[SKIP] No inbox found at {inbox}")
        return

    thread_dirs = [d for d in inbox.iterdir() if d.is_dir()]
    total = len(thread_dirs)
    print(f"[{platform}] Ingesting {total} threads...")

    for i, thread_dir in enumerate(thread_dirs, 1):
        print(f"[{platform}] [{i}/{total}] {thread_dir.name}", end="\r")

        thread_row, message_rows, reaction_rows_pending = parse_thread(thread_dir, your_name, platform)

        if thread_row is None:
            continue

        database.upsert_thread(conn, thread_row)
        message_ids = database.insert_messages(conn, message_rows)

        reaction_rows = []
        for msg_id, reactions in zip(message_ids, reaction_rows_pending):
            for r in reactions:
                reaction_rows.append({"message_id": msg_id, **r})

        if reaction_rows:
            database.insert_reactions(conn, reaction_rows)

        conn.commit()

    print(f"\n[{platform}] Done.")


def main():
    parser = argparse.ArgumentParser(description="Ingest messenger exports into SQLite.")
    parser.add_argument("--data", required=True, help="Path to the data/ folder containing platform export folders")
    parser.add_argument("--db",   default="messages.db", help="Output SQLite file (default: messages.db)")
    parser.add_argument("--you",  required=True, help='Your display name as it appears in the export, e.g. "Tim Chen"')
    args = parser.parse_args()

    data = Path(args.data)
    conn = database.connect(args.db)
    database.create_tables(conn)

    ingest_platform(data / "your_facebook_activity"  / "messages" / "inbox", "facebook",  conn, args.you)
    ingest_platform(data / "your_instagram_activity" / "messages" / "inbox", "instagram", conn, args.you)

    conn.close()
    print(f"Database saved to: {args.db}")


if __name__ == "__main__":
    main()
