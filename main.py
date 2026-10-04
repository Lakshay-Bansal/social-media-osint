#!/usr/bin/env python3
"""
Social Media OSINT & Channel Analyzer CLI
Entrypoint script located outside src/ as specified.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to sys.path so src imports resolve cleanly
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm

from src.config import Config
from src.youtube.client import YouTubeOSINTClient
from src.instagram.client import InstagramOSINTClient
from src.analytics.channel_analyzer import YouTubeChannelAnalyzer
from src.analytics.metrics import InstagramProfileAnalyzer
from src.utils.storage import DataExporter
from src.ui.terminal import (
    print_banner,
    display_youtube_summary_panel,
    display_videos_table,
    display_instagram_summary_panel,
)

console = Console()
exporter = DataExporter()


def handle_youtube_osint():
    """Interactive workflow for YouTube Channel OSINT."""
    console.print("\n[bold cyan]─── YouTube Channel Intelligence ───[/bold cyan]")
    identifier = Prompt.ask(
        "[bold white]Enter YouTube Channel (Handle e.g. @MrBeast, Channel ID UC..., or URL)[/bold white]",
        default="@veritasium",
    )

    max_videos = IntPrompt.ask(
        "[bold white]Number of recent videos to analyze (for deep stats & shorts breakdown)[/bold white]",
        default=50,
    )

    # Allow custom API key entry if not in .env
    if not Config.has_youtube_api_key():
        console.print("[dim yellow]Note: No YOUTUBE_API_KEY found in .env. Will use fallback extractor.[/dim yellow]")
        custom_key = Prompt.ask(
            "[dim]Paste YouTube API Key (press Enter to skip and use automatic scraper)[/dim]",
            default="",
        )
        if custom_key.strip():
            Config.set_youtube_api_key(custom_key.strip())

    with console.status(f"[bold green]Fetching & analyzing channel data for {identifier}...[/bold green]"):
        client = YouTubeOSINTClient()
        try:
            channel, videos = client.analyze_channel(identifier, max_videos=max_videos)
        except Exception as e:
            console.print(f"[bold red]Error fetching YouTube channel:[/bold red] {e}")
            return

    analyzer = YouTubeChannelAnalyzer(channel, videos)
    metrics = analyzer.get_summary_metrics()

    # Display KPI Panel
    display_youtube_summary_panel(metrics)

    # Interactive Table Inspection
    while True:
        console.print("\n[bold cyan]Select Table View / Sorting Options:[/bold cyan]")
        console.print("  [1] Top 10 Most Viewed Videos")
        console.print("  [2] Top 10 Longest Videos")
        console.print("  [3] Top 10 Shortest Videos")
        console.print("  [4] Top 10 Most Viewed YouTube Shorts")
        console.print("  [5] Top 10 Most Liked Videos")
        console.print("  [6] View All Videos (Interactive Table)")
        console.print("  [7] Export to JSON, CSV & SQLite Database")
        console.print("  [8] Back to Main Menu")

        choice = Prompt.ask("[bold white]Choose an option[/bold white]", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="1")

        if choice == "1":
            top_views = analyzer.get_top_videos_by_views(10)
            display_videos_table(top_views, title="Top 10 Most Viewed Videos", max_rows=10)
        elif choice == "2":
            top_long = analyzer.get_top_videos_by_duration(10, longest=True)
            display_videos_table(top_long, title="Top 10 Longest Videos", max_rows=10)
        elif choice == "3":
            top_short = analyzer.get_top_videos_by_duration(10, longest=False)
            display_videos_table(top_short, title="Top 10 Shortest Videos", max_rows=10)
        elif choice == "4":
            top_shorts = analyzer.get_top_shorts_by_views(10)
            display_videos_table(top_shorts, title="Top 10 Most Viewed Shorts", max_rows=10)
        elif choice == "5":
            top_likes = analyzer.get_top_videos_by_likes(10)
            display_videos_table(top_likes, title="Top 10 Most Liked Videos", max_rows=10)
        elif choice == "6":
            display_videos_table(analyzer.dataframe, title="All Analyzed Videos", max_rows=min(len(videos), 30))
        elif choice == "7":
            json_path = exporter.export_to_json(
                {"channel": channel.to_dict(include_videos=False), "metrics": metrics, "videos": [v.to_dict() for v in videos]},
                filename_prefix=f"youtube_{channel.channel_id}",
            )
            csv_path = exporter.export_videos_to_csv(
                [v.to_dict() for v in videos],
                filename_prefix=f"youtube_{channel.channel_id}",
            )
            sqlite_path = exporter.export_to_sqlite(
                channel.to_dict(include_videos=False),
                [v.to_dict() for v in videos],
            )
            console.print(f"[bold green]Exported successfully![/bold green]")
            console.print(f"  • JSON: [cyan]{json_path}[/cyan]")
            console.print(f"  • CSV:  [cyan]{csv_path}[/cyan]")
            console.print(f"  • SQLite DB: [cyan]{sqlite_path}[/cyan]")
        elif choice == "8":
            break


def handle_instagram_osint():
    """Interactive workflow for Instagram Profile OSINT."""
    console.print("\n[bold magenta]─── Instagram Profile Intelligence ───[/bold magenta]")
    identifier = Prompt.ask(
        "[bold white]Enter Instagram Username or Profile URL[/bold white]",
        default="instagram",
    )

    max_posts = IntPrompt.ask(
        "[bold white]Number of recent posts to inspect[/bold white]",
        default=25,
    )

    with console.status(f"[bold magenta]Fetching profile data for {identifier}...[/bold magenta]"):
        client = InstagramOSINTClient()
        try:
            profile, posts = client.analyze_profile(identifier, max_posts=max_posts)
        except Exception as e:
            console.print(f"[bold red]Error fetching Instagram profile:[/bold red] {e}")
            return

    analyzer = InstagramProfileAnalyzer(profile, posts)
    metrics = analyzer.get_summary_metrics()

    display_instagram_summary_panel(metrics)

    if posts:
        top_posts = analyzer.get_top_posts_by_likes(10)
        console.print(f"\n[bold]Top Recent Posts (by Likes):[/bold]")
        for idx, p in enumerate(posts[:10], start=1):
            console.print(f"  [cyan]{idx}.[/cyan] [{p.post_type}] {p.published_at} | [green]{p.like_count:,} likes[/green] | [magenta]{p.comment_count:,} comments[/magenta]")
            console.print(f"     [dim]{p.caption[:80]}...[/dim]")
            console.print(f"     [blue underline]{p.url}[/blue underline]")

        if Confirm.ask("\nExport Instagram profile & posts to file?", default=True):
            j_path = exporter.export_to_json(
                {"profile": profile.to_dict(include_posts=False), "metrics": metrics, "posts": [p.to_dict() for p in posts]},
                filename_prefix=f"instagram_{profile.username}",
            )
            c_path = exporter.export_videos_to_csv(
                [p.to_dict() for p in posts],
                filename_prefix=f"instagram_{profile.username}",
            )
            console.print(f"[bold green]Saved to:[/bold green] {j_path} and {c_path}")


def launch_dashboard():
    """Launches the Streamlit interactive dashboard."""
    console.print("[bold green]Starting interactive Web Dashboard (Streamlit)...[/bold green]")
    dashboard_file = ROOT_DIR / "dashboard.py"
    try:
        # Run using python -m streamlit run dashboard.py
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_file)])
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed to launch dashboard:[/bold red] {e}")


def main():
    """Main CLI driver."""
    print_banner()

    while True:
        console.print("\n[bold white]OSINT Suite Main Menu:[/bold white]")
        console.print("  [1] YouTube Channel OSINT & Video/Shorts Analysis")
        console.print("  [2] Instagram Profile OSINT")
        console.print("  [3] Launch Interactive Web Dashboard")
        console.print("  [4] Exit")

        choice = Prompt.ask("[bold cyan]Enter your choice[/bold cyan]", choices=["1", "2", "3", "4"], default="1")

        if choice == "1":
            handle_youtube_osint()
        elif choice == "2":
            handle_instagram_osint()
        elif choice == "3":
            launch_dashboard()
        elif choice == "4":
            console.print("[dim]Exiting Social Media OSINT Suite. Happy investigating![/dim]")
            break


if __name__ == "__main__":
    main()
