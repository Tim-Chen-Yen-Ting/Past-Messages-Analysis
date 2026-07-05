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

## Analysis Notebook (`analysis.ipynb`)

Runs against the SQLite DB built by `main.py`. Sections build on each other in order:

| Section | What it does |
|---|---|
| 1. Wrapped Stats | Message/word volume, active hours, top threads |
| 2. Communication Style per Contact | Vocab richness, question/emoji rate, avg length per contact |
| 3 / 3a. Social Mask Map | Per-thread style features → z-scored energy/intent axes → KMeans clusters, matched to a reference-mask library (Goffman, Jung, etc.) |
| 4. Relationship Drift | Yearly centroid trajectory per DM contact in energy/intent space |
| 4a. Rolling Lexical/Stylistic Drift | Monthly `avg_len`/`emoji_rate`/`func_rate`/`sent_strength`, rolling mean ± std per contact |
| 5. Sentiment: You vs Them | VADER (EN) / SnowNLP (CJK) compound sentiment, you vs. them, per contact |
| 5a. Sentiment Trajectory & Changepoint Detection | Monthly rolling sentiment + `ruptures` PELT changepoints per contact |
| 5b. Embedding-Space Drift | Monthly `all-MiniLM-L6-v2` centroids via `blocKit`'s BLOC incremental-centroid update; cosine distance between consecutive months |
| 6. Linguistic Mirroring | Style-vector alignment and lexical entrainment between you and each contact |
| 7. Relationship Dynamics | Initiation rate, response latency advantage, session frequency, from timestamps alone |
| 8. LLM-Narrated Evolution | Feeds the *summary statistics* from 4/4a/5a/5b (never raw messages) to an LLM via `litellm` + `instructor` (Pydantic-validated `EvolutionReport`) for a plain-language narration, with explicit confidence/caveats fields |
| 9. Anchored Close-Reading (opt-in) | Off by default (`RUN_RAW_SAMPLE_NARRATION`). For windows already flagged by 5a/5b, sends the small raw message sample from *just that window* to the LLM for a grounded close reading — the only section that sends real message content externally |

Notebook-only dependencies beyond the standard library: `pandas`, `numpy`, `matplotlib`, `scikit-learn`, `scipy`, `sentence-transformers`, `vaderSentiment`, `snownlp`, `ruptures`, `litellm`, `instructor`, `pydantic`. Sections 8–9 call an LLM API (default model `gpt-4.1` via `litellm`) and require the corresponding provider API key (e.g. `OPENAI_API_KEY`) set in the environment.

## Roadmap

- [x] AI analysis layer: statistics-grounded personality/style evolution narration via `litellm` + `instructor` (Section 8)
- [x] Personality evolution report across time periods (Sections 4a/5a/5b + 8)
- [ ] Anchored close-reading (Section 9) is opt-in only — consider a lighter-weight local/offline model path to avoid sending raw message content externally
