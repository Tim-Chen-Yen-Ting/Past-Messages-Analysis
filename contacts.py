"""
Contact management utilities.

Commands:
    python contacts.py seed     -- insert your own aliases + all known mappings (run once)
    python contacts.py export   -- dump all unique senders to senders.txt for review
    python contacts.py apply    -- read senders.txt and insert filled canonical_names into DB

Private data (your aliases and contact mappings) lives in contacts_data.py which is gitignored.
"""

import sys
import sqlite3

DB = "messages.db"

try:
    from contacts_data import YOUR_CANONICAL, YOUR_ALIASES, KNOWN_CONTACTS
except ImportError:
    print("[WARNING] contacts_data.py not found — using empty defaults. Create it from contacts_data.example.py.")
    YOUR_CANONICAL = "Your Name"
    YOUR_ALIASES = []
    KNOWN_CONTACTS = {}


def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed(conn):
    for platform_name, platform in YOUR_ALIASES:
        conn.execute("""
            INSERT OR IGNORE INTO contacts (canonical_name, platform, platform_name)
            VALUES (?, ?, ?)
        """, (YOUR_CANONICAL, platform, platform_name))

    inserted = skipped = 0
    for canonical, aliases in KNOWN_CONTACTS.items():
        for platform_name, platform in aliases:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO contacts (canonical_name, platform, platform_name)
                    VALUES (?, ?, ?)
                """, (canonical, platform, platform_name))
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1

    conn.commit()
    print(f"Seeded your aliases + {inserted} contact mappings ({skipped} already existed).")


def export_senders(conn):
    your_names = {a[0] for a in YOUR_ALIASES}
    rows = conn.execute("""
        SELECT sender, platform, COUNT(*) as msg_count
        FROM messages
        WHERE sender NOT IN ({})
        GROUP BY sender, platform
        ORDER BY platform, msg_count DESC
    """.format(",".join("?" * len(your_names))), list(your_names)).fetchall()

    with open("senders.txt", "w", encoding="utf-8") as f:
        f.write("platform_name\tplatform\tmsg_count\tcanonical_name\n")
        for platform_name, platform, count in rows:
            f.write(f"{platform_name}\t{platform}\t{count}\t\n")

    print(f"Exported {len(rows)} unique senders to senders.txt")


def apply(conn):
    inserted = skipped = 0
    with open("senders.txt", "r", encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            platform_name, platform, _, canonical_name = parts
            canonical_name = canonical_name.strip()
            if not canonical_name:
                skipped += 1
                continue
            conn.execute("""
                INSERT OR IGNORE INTO contacts (canonical_name, platform, platform_name)
                VALUES (?, ?, ?)
            """, (canonical_name, platform, platform_name))
            inserted += 1
    conn.commit()
    print(f"Inserted {inserted} contacts, skipped {skipped} unmapped senders.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    conn = get_conn()

    if cmd == "seed":
        seed(conn)
    elif cmd == "export":
        export_senders(conn)
    elif cmd == "apply":
        apply(conn)
    else:
        print(__doc__)
