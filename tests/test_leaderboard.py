import unittest
from datetime import datetime, timezone

from app.leaderboard import (
    filter_and_rank_videos,
    parse_published_at,
    should_run_now,
)


class LeaderboardTests(unittest.TestCase):
    def test_filter_and_rank_keeps_recent_english_ai_videos_sorted_by_view_count(self):
        now = datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc)
        videos = [
            {
                "id": "lower-count",
                "snippet": {
                    "title": "How to build an AI agent",
                    "description": "A practical LLM tutorial.",
                    "publishedAt": "2026-09-18T10:00:00Z",
                    "defaultAudioLanguage": "en",
                },
                "statistics": {"viewCount": "100"},
            },
            {
                "id": "higher-count",
                "snippet": {
                    "title": "New OpenAI model explained",
                    "description": "AI news and analysis.",
                    "publishedAt": "2026-09-19T10:00:00Z",
                    "defaultAudioLanguage": "en-US",
                },
                "statistics": {"viewCount": "300"},
            },
            {
                "id": "old-video",
                "snippet": {
                    "title": "AI history",
                    "description": "Artificial intelligence retrospective.",
                    "publishedAt": "2026-09-13T09:59:59Z",
                    "defaultAudioLanguage": "en",
                },
                "statistics": {"viewCount": "9999"},
            },
            {
                "id": "non-english",
                "snippet": {
                    "title": "AI novedades",
                    "description": "Noticias de inteligencia artificial.",
                    "publishedAt": "2026-09-20T10:00:00Z",
                    "defaultAudioLanguage": "es",
                },
                "statistics": {"viewCount": "9999"},
            },
            {
                "id": "not-ai",
                "snippet": {
                    "title": "Weekly office update",
                    "description": "Company announcements.",
                    "publishedAt": "2026-09-20T10:00:00Z",
                    "defaultAudioLanguage": "en",
                },
                "statistics": {"viewCount": "9999"},
            },
        ]

        ranked = filter_and_rank_videos(videos, now=now, days=7, limit=10)

        self.assertEqual([item["video_id"] for item in ranked], ["higher-count", "lower-count"])
        self.assertEqual([item["view_count"] for item in ranked], [300, 100])

    def test_parse_published_at_returns_utc_datetime(self):
        self.assertEqual(
            parse_published_at("2026-09-21T06:00:00Z"),
            datetime(2026, 9, 21, 6, 0, tzinfo=timezone.utc),
        )

    def test_should_run_now_accepts_only_the_six_am_new_york_hour(self):
        self.assertTrue(should_run_now(datetime(2026, 7, 1, 10, 5, tzinfo=timezone.utc)))
        self.assertTrue(should_run_now(datetime(2026, 1, 1, 11, 5, tzinfo=timezone.utc)))
        self.assertFalse(should_run_now(datetime(2026, 7, 1, 11, 5, tzinfo=timezone.utc)))


if __name__ == "__main__":
    unittest.main()
