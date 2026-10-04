from typing import Any, Dict, List, Optional
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
import pandas as pd
from ..utils.formatters import format_number, format_duration

console = Console()


def print_banner():
    """Display modern CLI banner."""
    banner_text = Text()
    banner_text.append("╔══════════════════════════════════════════════════════════════╗\n", style="cyan bold")
    banner_text.append("║           SOCIAL MEDIA OSINT & CHANNEL ANALYZER              ║\n", style="cyan bold")
    banner_text.append("║    YouTube & Instagram Intelligence Suite • Multi-Platform   ║\n", style="magenta")
    banner_text.append("╚══════════════════════════════════════════════════════════════╝", style="cyan bold")
    console.print(banner_text)


def display_youtube_summary_panel(metrics: Dict[str, Any]):
    """Render high-level YouTube channel KPIs in rich panels."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="bold white")
    table.add_column("Key2", style="bold cyan")
    table.add_column("Value2", style="bold white")

    table.add_row(
        "Channel Title:", str(metrics.get("title")),
        "Subscribers:", format_number(metrics.get("subscribers", 0)),
    )
    table.add_row(
        "Custom URL / Handle:", str(metrics.get("custom_url", "N/A")),
        "Channel ID:", str(metrics.get("channel_id")),
    )
    table.add_row(
        "Total Channel Uploads:", f"{metrics.get('total_channel_videos', 0):,}",
        "Videos Analyzed:", f"{metrics.get('total_analyzed_videos', 0):,}",
    )
    table.add_row(
        "Shorts Count (<=60s):", f"[yellow]{metrics.get('shorts_count', 0):,} ({metrics.get('shorts_percentage', 0)}%)[/yellow]",
        "Regular Videos Count:", f"[green]{metrics.get('regular_videos_count', 0):,}[/green]",
    )
    table.add_row(
        "Total Views (Analyzed):", f"[bold green]{format_number(metrics.get('total_views_analyzed', 0))}[/bold green]",
        "Avg Views / Video:", format_number(metrics.get("avg_views_per_video", 0)),
    )
    table.add_row(
        "Total Catalog Duration:", f"{metrics.get('total_duration_hours', 0)} hrs",
        "Avg Duration:", str(metrics.get("avg_duration_formatted")),
    )
    table.add_row(
        "Avg Regular Video Length:", str(metrics.get("avg_regular_duration_formatted")),
        "Avg Short Length:", str(metrics.get("avg_shorts_duration_formatted")),
    )
    table.add_row(
        "Longest Video:", str(metrics.get("max_duration_formatted")),
        "Shortest Video:", str(metrics.get("min_duration_formatted")),
    )

    console.print(Panel(table, title="[bold yellow]Channel Intelligence Overview[/bold yellow]", border_style="cyan"))


def display_videos_table(df: pd.DataFrame, title: str = "Video Analysis", max_rows: int = 10):
    """Render a formatted, colored table of videos with sorting and duration metrics."""
    if df.empty:
        console.print("[yellow]No video data available to display.[/yellow]")
        return

    table = Table(title=f"[bold]{title} (Top {min(len(df), max_rows)})[/bold]", show_lines=True)
    table.add_column("#", style="dim", justify="right", width=3)
    table.add_column("Type", justify="center", width=8)
    table.add_column("Title", style="bold white", no_wrap=False, max_width=45)
    table.add_column("Duration", justify="center", style="cyan", width=10)
    table.add_column("Views", justify="right", style="green", width=10)
    table.add_column("Likes", justify="right", style="magenta", width=10)
    table.add_column("Uploaded", justify="center", style="dim", width=12)
    table.add_column("URL", style="blue underline", max_width=32)

    subset = df.head(max_rows)
    for idx, (_, row) in enumerate(subset.iterrows(), start=1):
        is_short = bool(row.get("is_short"))
        type_badge = "[yellow bold]Short[/yellow bold]" if is_short else "[blue]Video[/blue]"

        table.add_row(
            str(idx),
            type_badge,
            str(row.get("title", ""))[:60],
            str(row.get("duration_formatted", "00:00")),
            format_number(row.get("view_count", 0)),
            format_number(row.get("like_count", 0)),
            str(row.get("published_at", "N/A"))[:10],
            str(row.get("url", "")),
        )

    console.print(table)


def display_instagram_summary_panel(metrics: Dict[str, Any]):
    """Render high-level Instagram profile KPIs in rich panels."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold magenta")
    table.add_column("Value", style="bold white")
    table.add_column("Key2", style="bold magenta")
    table.add_column("Value2", style="bold white")

    table.add_row(
        "Username:", f"@{metrics.get('username')}",
        "Followers:", format_number(metrics.get("followers", 0)),
    )
    table.add_row(
        "Full Name:", str(metrics.get("full_name")),
        "Following:", format_number(metrics.get("following", 0)),
    )
    table.add_row(
        "Total Profile Posts:", f"{metrics.get('total_profile_posts', 0):,}",
        "Analyzed Posts:", f"{metrics.get('analyzed_posts_count', 0):,}",
    )
    table.add_row(
        "Photos / Reels / Videos:",
        f"{metrics.get('photos_count', 0)} Photos | {metrics.get('reels_count', 0)} Reels | {metrics.get('videos_count', 0)} Videos",
        "Avg Likes / Post:", format_number(metrics.get("avg_likes_per_post", 0)),
    )
    table.add_row(
        "Engagement Rate:", f"[bold green]{metrics.get('engagement_rate_pct', 0.0)}%[/bold green]",
        "Account Status:", "Verified ✓" if metrics.get("is_verified") else "Standard",
    )

    console.print(Panel(table, title="[bold magenta]Instagram Profile Overview[/bold magenta]", border_style="magenta"))
