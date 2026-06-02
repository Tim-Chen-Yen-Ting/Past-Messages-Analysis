import json
from pathlib import Path


def fix_encoding(text: str) -> str:
    """Fix Facebook's mojibake: UTF-8 bytes mis-decoded as Latin-1."""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def detect_content_type(msg: dict) -> str:
    if "photos" in msg:
        return "photo"
    if "videos" in msg:
        return "video"
    if "audio_files" in msg:
        return "audio"
    if "sticker" in msg:
        return "sticker"
    if "share" in msg:
        return "share"
    if msg.get("type") == "Call":
        return "call"
    return "text"


def parse_thread(thread_dir: Path, your_name: str, platform: str = "facebook") -> tuple[dict, list[dict], list[dict]]:
    """
    Parse all message_N.json files in a thread folder.
    Returns (thread_row, message_rows, reaction_rows).
    """
    thread_id = thread_dir.name
    all_messages = []

    for json_file in sorted(thread_dir.glob("message_*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not all_messages:
            # grab participants from the first file
            participants = [fix_encoding(p["name"]) for p in data.get("participants", [])]
            thread_name_raw = data.get("title", thread_id)
            thread_name = fix_encoding(thread_name_raw)
            is_group = len(participants) > 2

        all_messages.extend(data.get("messages", []))

    if not all_messages:
        return None, [], []

    timestamps = [m["timestamp_ms"] for m in all_messages]
    your_count = sum(1 for m in all_messages if fix_encoding(m.get("sender_name", "")) == your_name)

    thread_row = {
        "thread_id":          thread_id,
        "platform":           platform,
        "thread_name":        thread_name,
        "is_group":           int(is_group),
        "participant_count":  len(participants),
        "first_message_ts":   min(timestamps),
        "last_message_ts":    max(timestamps),
        "your_message_count": your_count,
    }

    message_rows = []
    reaction_rows_pending = []  # (msg_index_in_list, [{reactor, emoji}])

    for msg in all_messages:
        sender = fix_encoding(msg.get("sender_name", ""))
        raw_content = msg.get("content", "")
        content = fix_encoding(raw_content) if raw_content else None
        content_type = detect_content_type(msg)
        words = len(content.split()) if content else 0
        chars = len(content) if content else 0

        message_rows.append({
            "platform":     platform,
            "thread_id":    thread_id,
            "timestamp_ms": msg["timestamp_ms"],
            "sender":       sender,
            "content":      content,
            "content_type": content_type,
            "word_count":   words,
            "char_count":   chars,
        })

        if "reactions" in msg:
            reaction_rows_pending.append([
                {"reactor": fix_encoding(r["actor"]), "emoji": fix_encoding(r["reaction"])}
                for r in msg["reactions"]
            ])
        else:
            reaction_rows_pending.append([])

    return thread_row, message_rows, reaction_rows_pending
