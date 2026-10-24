import unittest
from datetime import datetime, timezone

from app.leaderboard import filter_and_rank_videos


class ChannelDiversityTests(unittest.TestCase):
    NOW = datetime(2026, 10, 24, 18, tzinfo=timezone.utc)

    @staticmethod
    def video(video_id, channel_id, views, title="AI news"):
        return {
            "id": video_id,
            "snippet": {
                "title": title,
                "description": "AI agents and technology",
                "publishedAt": "2026-10-23T12:00:00Z",
                "defaultAudioLanguage": "en",
                "channelId": channel_id,
                "channelTitle": "Shared display name",
            },
            "statistics": {"viewCount": str(views)},
        }

    def test_videos_without_channel_ids_are_not_ranked(self):
        missing = self.video("missing-id", "", 3000)
        absent = self.video("absent-id", "", 4000)
        del absent["snippet"]["channelId"]
        valid = self.video("valid", "channel-a", 100)
        ranked = filter_and_rank_videos([missing, absent, valid], now=self.NOW, days=7, limit=10)
        self.assertEqual([row["video_id"] for row in ranked], ["valid"])

    def test_same_channel_can_appear_in_separate_category_rankings(self):
        ai = self.video("ai-video", "shared-channel", 200, title="AI news")
        business = self.video("business-video", "shared-channel", 300, title="Business strategy")
        pool = [ai, business]
        first = filter_and_rank_videos(pool, now=self.NOW, days=7, limit=10, title_terms=("AI news",))
        second = filter_and_rank_videos(pool, now=self.NOW, days=7, limit=10, title_terms=("Business strategy",))
        self.assertEqual([row["video_id"] for row in first], ["ai-video"])
        self.assertEqual([row["video_id"] for row in second], ["business-video"])
        self.assertEqual(first[0]["channel_id"], second[0]["channel_id"])

    def test_fewer_than_ten_channels_does_not_fill_with_repeat_channels(self):
        videos = [self.video(f"video-{i}", "single-channel", i) for i in range(20)]
        ranked = filter_and_rank_videos(videos, now=self.NOW, days=7, limit=10)
        self.assertEqual([row["video_id"] for row in ranked], ["video-19"])
        self.assertEqual(filter_and_rank_videos(videos, now=self.NOW, days=7, limit=0), [])

    def test_channel_selection_preserves_existing_tie_breakers(self):
        a = self.video("a", "channel", 100)
        b = self.video("b", "channel", 100)
        ranked = filter_and_rank_videos([b, a], now=self.NOW, days=7, limit=10)
        self.assertEqual([row["video_id"] for row in ranked], ["a"])

    def test_topic_fallback_counts_distinct_channels_not_strict_video_count(self):
        from scripts.update_leaderboard import rank_category_videos

        strict = [self.video(f"strict-{i}", "dominant-channel", 2000 - i) for i in range(12)]
        broader = [self.video(f"broader-{i}", f"channel-{i}", 1000 - i, title="Workflow demo") for i in range(9)]
        ranked = rank_category_videos(strict + broader, now=self.NOW, terms=("ai",), title_terms=("AI news",), source_types={})
        self.assertEqual([row["video_id"] for row in ranked], ["strict-0"] + [f"broader-{i}" for i in range(9)])
        self.assertEqual(len({row["channel_id"] for row in ranked}), 10)

    def test_top_ten_keeps_best_video_per_channel_before_limiting(self):
        dominant = [self.video(f"duplicate-{i}", "dominant-channel", 2000 - i) for i in range(12)]
        others = [self.video(f"other-{i}", f"channel-{i}", 1000 - i) for i in range(9)]
        ranked = filter_and_rank_videos(list(reversed(dominant + others)), now=self.NOW, days=7, limit=10)
        self.assertEqual([row["video_id"] for row in ranked], ["duplicate-0"] + [f"other-{i}" for i in range(9)])
        self.assertEqual(len({row["channel_id"] for row in ranked}), 10)


if __name__ == "__main__":
    unittest.main()
