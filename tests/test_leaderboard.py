import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.leaderboard import (
    filter_and_rank_videos,
    merge_archive_index,
    parse_duration_minutes,
    parse_published_at,
)
from scripts.update_leaderboard import has_complete_snapshot, load_categories, rank_category_videos


class LeaderboardTests(unittest.TestCase):
    def test_complete_snapshot_requires_every_category_for_the_local_date(self):
        from tempfile import TemporaryDirectory

        now = datetime(2026, 9, 28, 15, 0, tzinfo=timezone.utc)
        slugs = ["ai", "business"]
        with TemporaryDirectory() as directory:
            data_root = Path(directory)
            (data_root / "ai").mkdir()
            (data_root / "business").mkdir()
            (data_root / "ai" / "2026-09-28.json").write_text("{}")
            self.assertFalse(has_complete_snapshot(data_root, slugs, now))

            (data_root / "business" / "2026-09-28.json").write_text("{}")
            self.assertTrue(has_complete_snapshot(data_root, slugs, now))

    def test_filter_and_rank_keeps_recent_english_videos_sorted_by_view_count(self):
        now = datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc)
        videos = [
            {
                "id": "lower-count",
                "snippet": {
                    "title": "How to build an AI agent",
                    "description": "A practical LLM tutorial.",
                    "publishedAt": "2026-09-18T10:00:00Z",
                    "defaultAudioLanguage": "en",
                    "channelId": "channel-a",
                    "channelTitle": "Channel A",
                },
                "statistics": {"viewCount": "100"},
                "contentDetails": {"duration": "PT4M31S"},
            },
            {
                "id": "higher-count",
                "snippet": {
                    "title": "New OpenAI model explained",
                    "description": "AI news and analysis.",
                    "publishedAt": "2026-09-19T10:00:00Z",
                    "defaultAudioLanguage": "en-US",
                    "channelId": "channel-b",
                    "channelTitle": "Channel B",
                },
                "statistics": {"viewCount": "300"},
                "contentDetails": {"duration": "PT1H2M29S"},
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
        ]

        ranked = filter_and_rank_videos(
            videos,
            now=now,
            days=7,
            limit=10,
            terms=("ai", "openai", "llm"),
            source_types={"channel-a": "Independent creator", "channel-b": "Official company"},
        )

        self.assertEqual([item["video_id"] for item in ranked], ["higher-count", "lower-count"])
        self.assertEqual([item["view_count"] for item in ranked], [300, 100])
        self.assertEqual([item["duration_minutes"] for item in ranked], [62, 5])
        self.assertEqual([item["source_type"] for item in ranked], ["Official company", "Independent creator"])

    def test_title_terms_require_ai_agents_as_the_major_topic(self):
        now = datetime(2026, 9, 26, 10, 0, tzinfo=timezone.utc)
        videos = [
            {
                "id": "included",
                "snippet": {"title": "Building AI agents with MCP", "description": "A tutorial.", "publishedAt": "2026-09-25T10:00:00Z", "defaultAudioLanguage": "en", "channelId": "channel-a", "channelTitle": "Channel A"},
                "statistics": {"viewCount": "100"},
                "contentDetails": {"duration": "PT10M"},
            },
            {
                "id": "excluded-incidental",
                "snippet": {"title": "How sports agents negotiate", "description": "We briefly mention an AI agent.", "publishedAt": "2026-09-25T10:00:00Z", "defaultAudioLanguage": "en", "channelId": "channel-a", "channelTitle": "Channel A"},
                "statistics": {"viewCount": "1000"},
                "contentDetails": {"duration": "PT10M"},
            },
        ]

        ranked = filter_and_rank_videos(videos, now=now, days=7, limit=10, terms=("ai agent",), title_terms=("ai agent",), source_types={"channel-a": "AI agent and automation"})

        self.assertEqual([item["video_id"] for item in ranked], ["included"])

        relaxed = rank_category_videos(videos, now=now, terms=("ai agent",), title_terms=("ai agent",), source_types={"channel-a": "AI agent and automation"})

        self.assertEqual([item["video_id"] for item in relaxed], ["excluded-incidental", "included"])

    def test_parse_duration_minutes_rounds_to_nearest_minute(self):
        self.assertEqual(parse_duration_minutes("PT59S"), 1)
        self.assertEqual(parse_duration_minutes("PT1M29S"), 1)
        self.assertEqual(parse_duration_minutes("PT1M30S"), 2)
        self.assertEqual(parse_duration_minutes("PT2H"), 120)
        self.assertEqual(parse_duration_minutes("P1D"), 1440)
        self.assertEqual(parse_duration_minutes("P1DT3H27M25S"), 1647)

    def test_single_leaderboard_page_offers_category_and_date_filters_without_biotech(self):
        root = Path(__file__).resolve().parents[1] / "docs"
        slugs = (
            "ai",
            "ai-agents-and-automation",
            "ai-podcasts",
            "business-podcasts",
            "emerging-businesses-startups",
            "science-future-technology",
            "software-developer-tools",
        )
        content = (root / "index.html").read_text()
        self.assertEqual(content.count("<select"), 1)
        self.assertIn('for="category">Category</label>', content)
        self.assertIn('for="date">Date</label>', content)
        self.assertIn('type="text" readonly disabled', content)
        self.assertIn('id="calendar"', content)
        self.assertNotIn("Leaderboard category", content)
        self.assertNotIn("biotech-health-longevity", content)
        self.assertNotIn("archive.html", content)
        self.assertIn(
            "Top 10 YouTube videos from curated channels in the selected category and date, ranked by public view counts over the previous 7 days.",
            content,
        )
        self.assertIn("<th>Rank</th><th>YouTube Video</th><th>Channel</th><th>Length</th>", content)
        self.assertIn("white-space:nowrap", content)
        self.assertIn('class="table-wrap"', content)
        self.assertIn("padding:32px 48px 64px", content)
        self.assertIn("grid-template-columns:repeat(2,minmax(260px,380px))", content)
        self.assertIn('class="calendar-icon"', content)
        self.assertIn('aria-hidden="true"', content)
        self.assertIn("padding-right:42px", content)
        self.assertIn("overflow:hidden", content)
        self.assertIn("fitTableToViewport", content)
        self.assertIn("table.style.zoom", content)
        self.assertIn("ResizeObserver", content)
        self.assertIn("past=date<earliestDate", content)
        self.assertIn("${past?' past':''}", content)
        self.assertIn("text-decoration:line-through", content)
        self.assertIn('class="video"', content)
        self.assertIn('class="channel"', content)
        self.assertIn("calendar.classList.toggle('open')", content)
        self.assertIn(".calendar-day.disabled", content)
        self.assertIn(".calendar-day.selected", content)
        self.assertIn("dateSelect.dataset.value", content)
        self.assertNotIn("Top English-language videos", content)
        self.assertNotIn("Channel / source", content)
        self.assertNotIn("source-type", content)
        self.assertNotIn("candidates reviewed", content)
        self.assertNotIn("text-overflow:ellipsis", content)
        self.assertNotIn("updated ${new Date(data.generated_at).toLocaleString()}", content)
        for slug in slugs:
            self.assertIn(f'value="{slug}"', content)
            self.assertIn(f"data/{slug}", content)
        self.assertFalse((root / "archive.html").exists())
        self.assertFalse(any(root.glob("*/index.html")))
        self.assertFalse(any(root.glob("*/archive.html")))

    def test_load_categories_keeps_the_approved_source_types_and_channels(self):
        categories = load_categories()

        self.assertEqual(
            [category["slug"] for category in categories],
            [
                "emerging-businesses-startups",
                "science-future-technology",
                "software-developer-tools",
                "ai-agents-and-automation",
                "ai-podcasts",
                "business-podcasts",
            ],
        )
        self.assertEqual([len(category["channels"]) for category in categories], [20, 20, 20, 18, 13, 20])
        self.assertEqual(categories[0]["channels"][0], {"name": "Y Combinator", "handle": "@ycombinator", "source_type": "Accelerator"})
        self.assertEqual(categories[3]["channels"][0], {"name": "All About AI", "handle": "@allaboutai", "source_type": "AI agent and automation"})
        self.assertEqual(categories[4]["channels"][0], {"name": "Lex Fridman", "handle": "UCJIfeSCssxSC_Dhc5s7woww", "source_type": "AI podcast"})
        self.assertEqual(categories[5]["channels"][0], {"name": "The Diary Of A CEO", "handle": "@TheDiaryOfACEO", "source_type": "Business podcast"})

    def test_parse_published_at_returns_utc_datetime(self):
        self.assertEqual(
            parse_published_at("2026-09-21T06:00:00Z"),
            datetime(2026, 9, 21, 6, 0, tzinfo=timezone.utc),
        )


    def test_merge_archive_index_puts_newest_date_first_without_duplicates(self):
        existing = [{"date": "2026-09-20", "result_count": 10}]
        updated = merge_archive_index(existing, "2026-09-21", 8)

        self.assertEqual(
            updated,
            [
                {"date": "2026-09-21", "result_count": 8},
                {"date": "2026-09-20", "result_count": 10},
            ],
        )


if __name__ == "__main__":
    unittest.main()
