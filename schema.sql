CREATE TABLE IF NOT EXISTS threads (
    thread_id           TEXT PRIMARY KEY,
    platform            TEXT NOT NULL,
    thread_name         TEXT,
    is_group            INTEGER NOT NULL DEFAULT 0,  -- 0=false, 1=true
    participant_count   INTEGER,
    first_message_ts    INTEGER,
    last_message_ts     INTEGER,
    your_message_count  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform        TEXT NOT NULL,
    thread_id       TEXT NOT NULL,
    timestamp_ms    INTEGER NOT NULL,
    sender          TEXT NOT NULL,
    content         TEXT,
    content_type    TEXT NOT NULL DEFAULT 'text',  -- text, photo, video, audio, sticker, call, share
    word_count      INTEGER DEFAULT 0,
    char_count      INTEGER DEFAULT 0,
    FOREIGN KEY (thread_id) REFERENCES threads(thread_id)
);

CREATE TABLE IF NOT EXISTS reactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id  INTEGER NOT NULL,
    reactor     TEXT NOT NULL,
    emoji       TEXT,
    FOREIGN KEY (message_id) REFERENCES messages(id)
);

CREATE TABLE IF NOT EXISTS contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name  TEXT NOT NULL,       -- the "real" name you know them by
    platform        TEXT NOT NULL,       -- facebook / instagram / you
    platform_name   TEXT NOT NULL UNIQUE -- raw sender name as it appears in exports
);

CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp_ms);
CREATE INDEX IF NOT EXISTS idx_messages_sender    ON messages(sender);
CREATE INDEX IF NOT EXISTS idx_messages_thread    ON messages(thread_id);
