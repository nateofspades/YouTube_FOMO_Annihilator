#!/usr/bin/env python3
"""Fetch, rank, and publish curated YouTube leaderboards."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.leaderboard import AI_TERMS, filter_and_rank_videos, merge_archive_index, parse_published_at, should_run_now

API_BASE = "https://www.googleapis.com/youtube/v3"
WINDOW_DAYS = 7
RESULT_LIMIT = 10


def load_categories() -> list[dict]:
    """Read approved category source lists while preserving every source type."""
    raw_categories = json.loads((ROOT / "config/categories.json").read_text())["categories"]
    return [
        {
            **category,
            "terms": tuple(category["terms"]),
            "channels": [
                {"name": name, "handle": handle, "source_type": source_type}
                for name, handle, source_type in category["channels"]
            ],
        }
        for category in raw_categories
    ]


def youtube_get(resource: str, parameters: dict[str, str], api_key: str) -> dict:
    query = urlencode({**parameters, "key": api_key})
    try:
        with urlopen(f"{API_BASE}/{resource}?{query}", timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"YouTube API request failed ({exc.code}): {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"YouTube API request could not be completed: {exc.reason}") from exc


def resolve_channel(handle: str, api_key: str) -> dict:
    lookup = {"part": "id,contentDetails"}
    if handle.startswith("UC"):
        lookup["id"] = handle
    elif handle.startswith("@"):
        lookup["forHandle"] = handle
    else:
        lookup["forUsername"] = handle
    payload = youtube_get("channels", lookup, api_key)
    items = payload.get("items", [])
    if not items:
        raise RuntimeError(f"No YouTube channel found for handle {handle}")
    channel = items[0]
    return {"id": channel["id"], "uploads_playlist": channel["contentDetails"]["relatedPlaylists"]["uploads"]}


def recent_video_ids(uploads_playlist: str, cutoff: datetime, api_key: str) -> list[str]:
    video_ids: list[str] = []
    page_token = None
    while True:
        params = {"part": "contentDetails,snippet", "playlistId": uploads_playlist, "maxResults": "50"}
        if page_token:
            params["pageToken"] = page_token
        payload = youtube_get("playlistItems", params, api_key)
        items = payload.get("items", [])
        for item in items:
            published_at = parse_published_at(item["contentDetails"]["videoPublishedAt"])
            if published_at >= cutoff:
                video_ids.append(item["contentDetails"]["videoId"])
        if not items or parse_published_at(items[-1]["contentDetails"]["videoPublishedAt"]) < cutoff:
            break
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
    return video_ids


def videos_by_id(video_ids: list[str], api_key: str) -> list[dict]:
    videos: list[dict] = []
    for start in range(0, len(video_ids), 50):
        payload = youtube_get(
            "videos",
            {"part": "snippet,statistics,contentDetails", "id": ",".join(video_ids[start : start + 50])},
            api_key,
        )
        videos.extend(payload.get("items", []))
    return videos


def collect_leaderboard(api_key: str, now: datetime, *, slug: str, title: str, terms: tuple[str, ...], channels: list[dict], universe_version: int) -> dict:
    cutoff = now.replace(microsecond=0) - timedelta(days=WINDOW_DAYS)
    candidates: list[dict] = []
    sources: list[dict] = []
    source_types: dict[str, str] = {}

    for source in channels:
        try:
            resolved = resolve_channel(source["handle"], api_key)
        except RuntimeError as exc:
            print(f"Skipping unavailable source {source['name']}: {exc}")
            sources.append({**source, "channel_id": None, "recent_video_count": 0, "status": "unavailable"})
            continue
        ids = recent_video_ids(resolved["uploads_playlist"], cutoff, api_key)
        source_types[resolved["id"]] = source["source_type"]
        sources.append({**source, "channel_id": resolved["id"], "recent_video_count": len(ids)})
        candidates.extend(videos_by_id(ids, api_key))

    unique_candidates = {video["id"]: video for video in candidates}
    ranked = filter_and_rank_videos(
        list(unique_candidates.values()),
        now=now,
        days=WINDOW_DAYS,
        limit=RESULT_LIMIT,
        terms=terms,
        source_types=source_types,
    )
    return {
        "slug": slug,
        "title": title,
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "time_zone": "America/New_York",
        "window_days": WINDOW_DAYS,
        "universe_version": universe_version,
        "source_channels": sources,
        "candidate_count": len(unique_candidates),
        "results": ranked,
    }


def collect_ai(api_key: str, now: datetime) -> dict:
    config = json.loads((ROOT / "config/channels.json").read_text())
    channels = [{**source, "source_type": "AI-focused channel"} for source in config["channels"]]
    return collect_leaderboard(
        api_key,
        now,
        slug="ai",
        title="Artificial intelligence",
        terms=AI_TERMS,
        channels=channels,
        universe_version=config["universe_version"],
    )


def write_results(payload: dict, data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    (data_dir / "latest.json").write_text(rendered)
    local_date = datetime.fromisoformat(payload["generated_at"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York")).date().isoformat()
    (data_dir / f"{local_date}.json").write_text(rendered)
    index_path = data_dir / "archive.json"
    existing = json.loads(index_path.read_text()) if index_path.exists() else []
    index_path.write_text(json.dumps(merge_archive_index(existing, local_date, len(payload["results"])), indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Run outside the scheduled 6 a.m. NY hour")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    if not args.force and not should_run_now(now):
        print("Skipping: this workflow is not running during the 6 a.m. America/New_York hour.")
        return 0

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY is required")

    ai_payload = collect_ai(api_key, now)
    write_results(ai_payload, ROOT / "docs/data")
    print(f"Published AI: {len(ai_payload['results'])} ranked videos from {ai_payload['candidate_count']} candidates.")
    for category in load_categories():
        payload = collect_leaderboard(api_key, now, universe_version=1, **category)
        write_results(payload, ROOT / "docs/data" / category["slug"])
        print(f"Published {category['slug']}: {len(payload['results'])} ranked videos from {payload['candidate_count']} candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
