# Past Messages Analysis

A pipeline to ingest Facebook Messenger and Instagram message exports into a local SQLite database, enabling SQL-based analysis and AI-powered personality/socialization insights over time.

## Setup

No external dependencies — standard library only.

```bash
python main.py --data "path/to/data" --db messages.db --you "Your Name"
```

- `--data` — folder containing `your_facebook_activity/` and/or `your_instagram_activity/`
- `--db` — output SQLite file (created if it doesn't exist)
- `--you` — your display name exactly as it appears in the export

## Data Folder Structure

```
data/
├── your_facebook_activity/
│   └── messages/inbox/<thread>/message_1.json ...
└── your_instagram_activity/
    └── messages/inbox/<thread>/message_1.json ...
```

The `data/` folder is gitignored — raw exports never get committed.

## Database Schema

| Table | Description |
|---|---|
| `messages` | Every message: sender, timestamp, content, type (text/photo/video/audio/sticker/share/call), word/char count |
| `threads` | One row per conversation: name, group or DM, participant count, date range, your message count |
| `reactions` | Emoji reactions linked to messages |

Non-text messages (photos, videos, etc.) are recorded with `content = NULL` and the appropriate `content_type` — media files stay in `data/` untouched.

## Useful Queries

```sql
-- Message volume by year
SELECT strftime('%Y', timestamp_ms/1000, 'unixepoch') AS year, COUNT(*)
FROM messages GROUP BY year;

-- Your most active threads
SELECT thread_name, your_message_count
FROM threads ORDER BY your_message_count DESC LIMIT 20;

-- Your messages only, by month
SELECT strftime('%Y-%m', timestamp_ms/1000, 'unixepoch') AS month, COUNT(*)
FROM messages WHERE sender = 'Name' GROUP BY month;

-- Media you sent over time
SELECT strftime('%Y', timestamp_ms/1000, 'unixepoch') AS year, content_type, COUNT(*)
FROM messages WHERE sender = 'Name' AND content_type != 'text'
GROUP BY year, content_type;
```

## Roadmap

- [ ] AI analysis layer: per-month and per-thread summaries via Claude API
- [ ] Personality evolution report across time periods
