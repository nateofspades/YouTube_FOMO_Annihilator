"""Pure ranking rules for the YouTube FOMO Annihilator."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

AI_TERMS = (
    "ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "llm",
    "large language model",
    "generative",
    "chatgpt",
    "openai",
    "anthropic",
    "claude",
    "gemini",
    "gpt",
    "agent",
    "neural network",
    "deepmind",
    "hugging face",
)
NEW_YORK = ZoneInfo("America/New_York")
_DURATION_PATTERN = re.compile(r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$")


def parse_published_at(value: str) -> datetime:
    """Parse a YouTube RFC 3339 timestamp into a UTC datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def parse_duration_minutes(value: str) -> int:
    """Convert an ISO 8601 video duration to minutes rounded half up."""
    match = _DURATION_PATTERN.fullmatch(value)
    if not match:
        return 0
    parts = {name: int(raw or 0) for name, raw in match.groupdict().items()}
    total_seconds = parts["days"] * 86400 + parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]
    return (total_seconds + 30) // 60


def should_run_now(now: datetime) -> bool:
    """Return whether a UTC time falls within the target midnight NY hour."""
    return now.astimezone(NEW_YORK).hour == 0


def _is_english(video: dict) -> bool:
    language = video.get("snippet", {}).get("defaultAudioLanguage", "")
    return language.lower().startswith("en")


def _is_related(video: dict, terms: tuple[str, ...]) -> bool:
    snippet = video.get("snippet", {})
    text = " ".join(
        [snippet.get("title", ""), snippet.get("description", ""), " ".join(snippet.get("tags", []))]
    ).lower()
    return any(re.search(r"\bai\b", text) if term == "ai" else term.lower() in text for term in terms)


def _is_recent(video: dict, now: datetime, days: int) -> bool:
    published_at = parse_published_at(video["snippet"]["publishedAt"])
    return now - timedelta(days=days) <= published_at <= now


def merge_archive_index(existing: list[dict], date: str, result_count: int) -> list[dict]:
    """Upsert a daily archive entry and return newest-first records."""
    retained = [entry for entry in existing if entry.get("date") != date]
    retained.append({"date": date, "result_count": result_count})
    return sorted(retained, key=lambda entry: entry["date"], reverse=True)


def filter_and_rank_videos(
    videos: list[dict],
    *,
    now: datetime,
    days: int,
    limit: int,
    terms: tuple[str, ...] = AI_TERMS,
    source_types: dict[str, str] | None = None,
) -> list[dict]:
    """Return eligible curated-source videos ordered by current public view count."""
    source_types = source_types or {}
    eligible = []
    for video in videos:
        if not (_is_recent(video, now, days) and _is_english(video) and _is_related(video, terms)):
            continue
        snippet = video["snippet"]
        channel_id = snippet.get("channelId", "")
        eligible.append(
            {
                "video_id": video["id"],
                "title": snippet["title"],
                "channel_id": channel_id,
                "channel_title": snippet.get("channelTitle", ""),
                "source_type": source_types.get(channel_id, "Curated channel"),
                "published_at": snippet["publishedAt"],
                "view_count": int(video.get("statistics", {}).get("viewCount", 0)),
                "duration_minutes": parse_duration_minutes(video.get("contentDetails", {}).get("duration", "")),
                "url": f"https://www.youtube.com/watch?v={video['id']}",
            }
        )
    return sorted(eligible, key=lambda item: (-item["view_count"], item["published_at"], item["video_id"]))[:limit]
