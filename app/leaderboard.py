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


def parse_published_at(value: str) -> datetime:
    """Parse a YouTube RFC 3339 timestamp into a UTC datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def should_run_now(now: datetime) -> bool:
    """Return whether a UTC time falls within the target 6 a.m. NY hour."""
    return now.astimezone(NEW_YORK).hour == 6


def _is_english(video: dict) -> bool:
    language = video.get("snippet", {}).get("defaultAudioLanguage", "")
    return language.lower().startswith("en")


def _is_ai_related(video: dict) -> bool:
    snippet = video.get("snippet", {})
    text = " ".join(
        [
            snippet.get("title", ""),
            snippet.get("description", ""),
            " ".join(snippet.get("tags", [])),
        ]
    ).lower()
    return any(
        re.search(r"\bai\b", text) if term == "ai" else term in text
        for term in AI_TERMS
    )


def _is_recent(video: dict, now: datetime, days: int) -> bool:
    published_at = parse_published_at(video["snippet"]["publishedAt"])
    return now - timedelta(days=days) <= published_at <= now


def filter_and_rank_videos(
    videos: list[dict], *, now: datetime, days: int, limit: int
) -> list[dict]:
    """Return eligible videos ordered by current public lifetime view count."""
    eligible = []
    for video in videos:
        if not (_is_recent(video, now, days) and _is_english(video) and _is_ai_related(video)):
            continue
        snippet = video["snippet"]
        eligible.append(
            {
                "video_id": video["id"],
                "title": snippet["title"],
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": snippet["publishedAt"],
                "view_count": int(video.get("statistics", {}).get("viewCount", 0)),
                "url": f"https://www.youtube.com/watch?v={video['id']}",
            }
        )
    return sorted(
        eligible,
        key=lambda item: (-item["view_count"], item["published_at"], item["video_id"]),
    )[:limit]
