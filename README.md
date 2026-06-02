# Past Messages Analysis

A pipeline to ingest Facebook Messenger (and eventually Instagram) message exports into a local SQLite database, enabling SQL-based analysis and AI-powered personality/socialization insights over time.

## Setup

```bash
pip install -r requirements.txt  # nothing yet, standard library only
```

## Usage

```bash
python main.py --input "path/to/your_facebook_activity" --db messages.db --you "Your Name"
```

- `--input` — root folder of your Facebook data export
- `--db` — output SQLite file (created if it doesn't exist)
- `--you` — your display name exactly as it appears in the export

## Database Schema

| Table | Description |
|---|---|
| `messages` | Every message: sender, timestamp, content, type, word/char count |
| `threads` | One row per conversation: name, group/DM, participant count, date range |
| `reactions` | Emoji reactions, linked to messages |

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
FROM messages WHERE sender = 'Your Name' GROUP BY month;
```

## Roadmap

- [ ] Instagram export parser
- [ ] AI analysis layer: per-month and per-thread summaries via Claude API
- [ ] Personality evolution report across time periods
