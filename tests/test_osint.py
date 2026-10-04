"""
Unit tests for Social Media OSINT Toolkit.
Verifies models, ISO duration parsing, Shorts categorization, and channel analytics.
"""

import unittest
from datetime import datetime
from src.utils.formatters import parse_iso_duration, format_duration, format_number
from src.youtube.models import YouTubeChannel, YouTubeVideo
from src.analytics.channel_analyzer import YouTubeChannelAnalyzer


class TestOSINTToolkit(unittest.TestCase):
    def test_duration_parsing(self):
        # 1 minute 30 seconds
        self.assertEqual(parse_iso_duration("PT1M30S"), 90)
        # 45 seconds (Shorts)
        self.assertEqual(parse_iso_duration("PT45S"), 45)
        # 1 hour 5 minutes 10 seconds
        self.assertEqual(parse_iso_duration("PT1H5M10S"), 3910)
        # Empty/None
        self.assertEqual(parse_iso_duration(None), 0)

    def test_format_duration(self):
        self.assertEqual(format_duration(45), "00:45")
        self.assertEqual(format_duration(90), "01:30")
        self.assertEqual(format_duration(3665), "01:01:05")

    def test_format_number(self):
        self.assertEqual(format_number(950), "950")
        self.assertEqual(format_number(1500), "1.5K")
        self.assertEqual(format_number(2500000), "2.50M")
        self.assertEqual(format_number(1200000000), "1.20B")

    def test_channel_analyzer(self):
        # Create mock videos
        v1 = YouTubeVideo(
            video_id="vid_short_1",
            title="Shorts Test Video #shorts",
            description="Test short",
            published_at="2024-01-01 10:00",
            duration_seconds=45,
            duration_formatted="00:45",
            is_short=True,
            view_count=50000,
            like_count=3000,
        )
        v2 = YouTubeVideo(
            video_id="vid_regular_1",
            title="Long Documentary",
            description="Deep dive",
            published_at="2024-01-02 12:00",
            duration_seconds=1200,
            duration_formatted="20:00",
            is_short=False,
            view_count=100000,
            like_count=8000,
        )
        v3 = YouTubeVideo(
            video_id="vid_short_2",
            title="Another Fast Tip",
            description="Fast tips",
            published_at="2024-01-03 15:00",
            duration_seconds=58,
            duration_formatted="00:58",
            is_short=True,
            view_count=20000,
            like_count=1200,
        )

        channel = YouTubeChannel(
            channel_id="UC_TEST_CHANNEL_123",
            title="Test Science Channel",
            custom_url="@testscience",
            description="A test channel",
            published_at="2020-01-01 00:00",
            subscriber_count=150000,
            video_count=3,
            view_count=170000,
            videos=[v1, v2, v3],
        )

        analyzer = YouTubeChannelAnalyzer(channel)
        metrics = analyzer.get_summary_metrics()

        self.assertEqual(metrics["total_analyzed_videos"], 3)
        self.assertEqual(metrics["shorts_count"], 2)
        self.assertEqual(metrics["regular_videos_count"], 1)
        self.assertEqual(metrics["shorts_percentage"], 66.7)
        self.assertEqual(metrics["total_views_analyzed"], 170000)

        # Test Top by Views
        top_views = analyzer.get_top_videos_by_views(2)
        self.assertEqual(len(top_views), 2)
        self.assertEqual(top_views.iloc[0]["video_id"], "vid_regular_1")

        # Test Top Shorts
        top_shorts = analyzer.get_top_shorts_by_views(5)
        self.assertEqual(len(top_shorts), 2)
        self.assertEqual(top_shorts.iloc[0]["video_id"], "vid_short_1")


if __name__ == "__main__":
    unittest.main()
