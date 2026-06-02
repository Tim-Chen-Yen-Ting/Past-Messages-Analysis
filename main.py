"""
Usage:
    python main.py --input <path_to_facebook_export> --db messages.db --you "Tim Chen"

Example:
    python main.py --input "e:/past_msg/your_facebook_activity" --db messages.db --you "Tim Chen"
"""

import argparse
from pathlib import Path

import db as database
from facebook_parser import parse_thread


def ingest_facebook(export_root: Path, conn, your_name: str):
    inbox = export_root / "messages" / "inbox"
    if not inbox.exists():
        print(f"[ERROR] Could not find inbox at {inbox}")
        return

    thread_dirs = [d for d in inbox.iterdir() if d.is_dir()]
    total = len(thread_dirs)

    for i, thread_dir in enumerate(thread_dirs, 1):
        print(f"[{i}/{total}] {thread_dir.name}", end="\r")

        thread_row, message_rows, reaction_rows_pending = parse_thread(thread_dir, your_name)

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

    print(f"\nDone. Ingested {total} threads.")


def main():
    parser = argparse.ArgumentParser(description="Ingest messenger exports into SQLite.")
    parser.add_argument("--input",  required=True, help="Path to the Facebook export root folder")
    parser.add_argument("--db",     default="messages.db", help="Output SQLite file (default: messages.db)")
    parser.add_argument("--you",    required=True, help='Your display name as it appears in the export, e.g. "Tim Chen"')
    args = parser.parse_args()

    conn = database.connect(args.db)
    database.create_tables(conn)

    ingest_facebook(Path(args.input), conn, args.you)

    conn.close()
    print(f"Database saved to: {args.db}")


if __name__ == "__main__":
    main()
