"""Quick test to verify SQLite export and DataFrame generation."""
from src.youtube.models import YouTubeChannel, YouTubeVideo
from src.analytics.channel_analyzer import YouTubeChannelAnalyzer
from src.utils.storage import DataExporter

v1 = YouTubeVideo(
    video_id="test1",
    title="Sample Short #shorts",
    description="Test",
    published_at="2024-05-01 10:00",
    duration_seconds=30,
    duration_formatted="00:30",
    is_short=True,
    view_count=12000,
    like_count=500,
)
v2 = YouTubeVideo(
    video_id="test2",
    title="Sample Regular Video",
    description="Test",
    published_at="2024-05-02 12:00",
    duration_seconds=950,
    duration_formatted="15:50",
    is_short=False,
    view_count=54000,
    like_count=2100,
)
channel = YouTubeChannel(
    channel_id="UC_SAMPLE",
    title="Sample Channel",
    custom_url="@sample",
    description="Test",
    published_at="2022-01-01",
    subscriber_count=10000,
    video_count=2,
    view_count=66000,
    videos=[v1, v2],
)

exporter = DataExporter()
db = exporter.export_to_sqlite(channel.to_dict(include_videos=False), [v.to_dict() for v in [v1, v2]])
print(f"SQLite DB created successfully at: {db}")

analyzer = YouTubeChannelAnalyzer(channel)
metrics = analyzer.get_summary_metrics()
print("Metrics successfully calculated:", metrics["shorts_count"], "Shorts,", metrics["regular_videos_count"], "Regular")
