"""
Social Media OSINT Interactive Dashboard
Built with Streamlit & Plotly.
Run with: streamlit run dashboard.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import Config
from src.youtube.client import YouTubeOSINTClient
from src.instagram.client import InstagramOSINTClient
from src.analytics.channel_analyzer import YouTubeChannelAnalyzer
from src.analytics.metrics import InstagramProfileAnalyzer
from src.utils.storage import DataExporter
from src.utils.formatters import format_number, format_duration

# Page configuration
st.set_page_config(
    page_title="Social Media OSINT Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF0055, #7928CA, #0070F3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #888888;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1e1e24;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2d2d38;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

exporter = DataExporter()


def render_sidebar():
    """Render sidebar inputs and settings."""
    st.sidebar.markdown("### 🛠️ OSINT Control Panel")
    platform = st.sidebar.radio("Target Platform", ["YouTube Channel", "Instagram Profile"])

    st.sidebar.markdown("---")
    if platform == "YouTube Channel":
        identifier = st.sidebar.text_input(
            "Channel Identifier",
            value="@veritasium",
            help="Enter channel handle (e.g. @MrBeast), Channel ID (UC...), or YouTube Channel URL",
        )
        max_items = st.sidebar.slider("Videos to Analyze", min_value=10, max_value=300, value=60, step=10)

        with st.sidebar.expander("🔑 API Configuration (Optional)"):
            api_key = st.sidebar.text_input(
                "YouTube API Key",
                value=Config.YOUTUBE_API_KEY,
                type="password",
                help="Leave empty to use automatic keyless fallback scraper!",
            )
            if api_key != Config.YOUTUBE_API_KEY:
                Config.set_youtube_api_key(api_key)

        fetch_btn = st.sidebar.button("🚀 Analyze YouTube Channel", type="primary", use_container_width=True)
        return platform, identifier, max_items, fetch_btn

    else:
        identifier = st.sidebar.text_input(
            "Instagram Username",
            value="instagram",
            help="Enter username or instagram.com profile link",
        )
        max_items = st.sidebar.slider("Recent Posts to Inspect", min_value=5, max_value=50, value=20, step=5)
        fetch_btn = st.sidebar.button("🚀 Analyze Instagram Profile", type="primary", use_container_width=True)
        return platform, identifier, max_items, fetch_btn


def render_youtube_dashboard(identifier: str, max_videos: int, trigger: bool):
    """Render YouTube Channel Analysis and interactive tables."""
    st.markdown('<div class="main-title">YouTube Channel Intelligence & Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Detailed breakdown of videos, shorts, durations, view metrics, and top rankings</div>', unsafe_allow_html=True)

    if trigger or "yt_channel" not in st.session_state or st.session_state.get("yt_identifier") != identifier:
        if trigger:
            with st.spinner(f"Scanning channel '{identifier}' and analyzing video metrics..."):
                client = YouTubeOSINTClient()
                progress_bar = st.progress(0, text="Connecting to YouTube...")

                def update_progress(curr, total, msg):
                    progress_bar.progress(min(1.0, curr / 100), text=msg)

                try:
                    channel, videos = client.analyze_channel(identifier, max_videos=max_videos, progress_callback=update_progress)
                    st.session_state["yt_channel"] = channel
                    st.session_state["yt_videos"] = videos
                    st.session_state["yt_identifier"] = identifier
                    progress_bar.empty()
                except Exception as e:
                    st.error(f"Failed to analyze channel: {e}")
                    return

    if "yt_channel" not in st.session_state:
        st.info("👈 Enter a YouTube Channel handle or URL in the sidebar and click **Analyze YouTube Channel** to begin.")
        return

    channel = st.session_state["yt_channel"]
    videos = st.session_state["yt_videos"]

    if not videos:
        st.warning("No videos retrieved for this channel.")
        return

    analyzer = YouTubeChannelAnalyzer(channel, videos)
    metrics = analyzer.get_summary_metrics()
    df = analyzer.dataframe

    # Channel Header Profile
    col_av, col_info = st.columns([1, 6])
    with col_av:
        if channel.avatar_url:
            st.image(channel.avatar_url, width=110)
        else:
            st.markdown("### 📺")
    with col_info:
        st.markdown(f"## {channel.title}  `{channel.custom_url or '@' + channel.channel_id}`")
        if channel.description:
            with st.expander("Channel Description"):
                st.write(channel.description)

    # Top KPI Metrics Cards
    st.markdown("### 📊 High-Level Metrics")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Subscribers", format_number(metrics["subscribers"]))
    with kpi2:
        st.metric("Total Videos Analyzed", f"{metrics['total_analyzed_videos']}")
    with kpi3:
        st.metric("Shorts Count (<=60s)", f"{metrics['shorts_count']} ({metrics['shorts_percentage']}%)")
    with kpi4:
        st.metric("Regular Videos (>60s)", f"{metrics['regular_videos_count']}")
    with kpi5:
        st.metric("Total Views (Analyzed)", format_number(metrics["total_views_analyzed"]))

    kpi6, kpi7, kpi8, kpi9, kpi10 = st.columns(5)
    with kpi6:
        st.metric("Avg Views / Video", format_number(metrics["avg_views_per_video"]))
    with kpi7:
        st.metric("Total Catalog Duration", f"{metrics['total_duration_hours']} hrs")
    with kpi8:
        st.metric("Avg Video Duration", metrics["avg_duration_formatted"])
    with kpi9:
        st.metric("Avg Regular Length", metrics["avg_regular_duration_formatted"])
    with kpi10:
        st.metric("Avg Shorts Length", metrics["avg_shorts_duration_formatted"])

    st.markdown("---")

    # Visualizations Section
    st.markdown("### 📈 Visual Analysis")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Donut chart: Shorts vs Regular Videos
        fig_donut = px.pie(
            names=["YouTube Shorts (≤60s)", "Regular Videos (>60s)"],
            values=[metrics["shorts_count"], metrics["regular_videos_count"]],
            title="Video Composition: Shorts vs Regular Videos",
            hole=0.45,
            color_discrete_sequence=["#FF0055", "#0070F3"],
        )
        fig_donut.update_layout(margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_donut, use_container_width=True)

    with chart_col2:
        # Duration distribution histogram
        # Create readable bins
        df["duration_mins"] = df["duration_seconds"] / 60.0
        fig_hist = px.histogram(
            df,
            x="duration_mins",
            nbins=25,
            color="is_short",
            color_discrete_map={True: "#FF0055", False: "#0070F3"},
            labels={"duration_mins": "Duration (Minutes)", "is_short": "Is Short?"},
            title="Video Duration Distribution",
        )
        fig_hist.update_layout(margin=dict(t=40, b=20, l=20, r=20), xaxis_title="Duration (Minutes)", yaxis_title="Number of Videos")
        st.plotly_chart(fig_hist, use_container_width=True)

    # Upload Timeline Chart
    timeline = analyzer.get_upload_timeline_metrics()
    if timeline.get("by_month"):
        month_df = pd.DataFrame(list(timeline["by_month"].items()), columns=["Month", "Uploads"])
        fig_timeline = px.bar(
            month_df,
            x="Month",
            y="Uploads",
            title="Upload Frequency Over Time (By Month)",
            color="Uploads",
            color_continuous_scale="Purples",
        )
        fig_timeline.update_layout(margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig_timeline, use_container_width=True)

    st.markdown("---")

    # Top 10 Leaderboards
    st.markdown("### 🏆 Top 10 Leaderboards")
    tab_views, tab_longest, tab_shortest, tab_shorts, tab_likes = st.tabs([
        "🔥 Top 10 Most Viewed",
        "⏳ Top 10 Longest Videos",
        "⚡ Top 10 Shortest Videos",
        "📱 Top 10 Shorts",
        "❤️ Top 10 Most Liked",
    ])

    with tab_views:
        top_v = analyzer.get_top_videos_by_views(10)
        _display_rich_table(top_v)

    with tab_longest:
        top_l = analyzer.get_top_videos_by_duration(10, longest=True)
        _display_rich_table(top_l)

    with tab_shortest:
        top_s = analyzer.get_top_videos_by_duration(10, longest=False)
        _display_rich_table(top_s)

    with tab_shorts:
        top_sh = analyzer.get_top_shorts_by_views(10)
        _display_rich_table(top_sh)

    with tab_likes:
        top_lk = analyzer.get_top_videos_by_likes(10)
        _display_rich_table(top_lk)

    st.markdown("---")

    # Complete Interactive Table with Real-time Filters
    st.markdown("### 🔍 Full Video Explorer & Custom Sorter")
    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
    with f_col1:
        type_filter = st.selectbox("Filter Video Type", ["All Formats", "Shorts Only (<=60s)", "Regular Videos Only (>60s)"])
    with f_col2:
        sort_by = st.selectbox(
            "Sort Table By",
            ["Views (High to Low)", "Views (Low to High)", "Duration (Longest First)", "Duration (Shortest First)", "Likes (High to Low)", "Upload Date (Newest First)"],
        )
    with f_col3:
        search_query = st.text_input("Search Video Title / Keyword", "")

    # Apply filters
    filtered_df = df.copy()
    if type_filter == "Shorts Only (<=60s)":
        filtered_df = filtered_df[filtered_df["is_short"] == True]
    elif type_filter == "Regular Videos Only (>60s)":
        filtered_df = filtered_df[filtered_df["is_short"] == False]

    if search_query.strip():
        filtered_df = filtered_df[filtered_df["title"].str.contains(search_query.strip(), case=False, na=False)]

    if sort_by == "Views (High to Low)":
        filtered_df = filtered_df.sort_values(by="view_count", ascending=False)
    elif sort_by == "Views (Low to High)":
        filtered_df = filtered_df.sort_values(by="view_count", ascending=True)
    elif sort_by == "Duration (Longest First)":
        filtered_df = filtered_df.sort_values(by="duration_seconds", ascending=False)
    elif sort_by == "Duration (Shortest First)":
        filtered_df = filtered_df.sort_values(by="duration_seconds", ascending=True)
    elif sort_by == "Likes (High to Low)":
        filtered_df = filtered_df.sort_values(by="like_count", ascending=False)
    elif sort_by == "Upload Date (Newest First)":
        filtered_df = filtered_df.sort_values(by="published_at", ascending=False)

    st.caption(f"Showing {len(filtered_df)} of {len(df)} videos")
    _display_rich_table(filtered_df)

    # Export Section
    st.markdown("---")
    st.markdown("### 💾 Export OSINT Data")
    exp_c1, exp_c2, exp_c3 = st.columns(3)
    with exp_c1:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Videos CSV",
            data=csv_data,
            file_name=f"youtube_{channel.channel_id}_videos.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with exp_c2:
        import json
        json_data = json.dumps(
            {"channel": channel.to_dict(include_videos=False), "metrics": metrics, "videos": [v.to_dict() for v in videos]},
            indent=2,
            default=str,
        ).encode("utf-8")
        st.download_button(
            label="📥 Download Full OSINT JSON",
            data=json_data,
            file_name=f"youtube_{channel.channel_id}.json",
            mime="application/json",
            use_container_width=True,
        )
    with exp_c3:
        if st.button("🗄️ Save into SQLite Database", use_container_width=True):
            db_path = exporter.export_to_sqlite(
                channel.to_dict(include_videos=False),
                [v.to_dict() for v in videos],
            )
            st.success(f"Saved into SQLite database at `{db_path.name}` (compatible with Grafana)!")


def _display_rich_table(data_df: pd.DataFrame):
    """Format and display video table with clean columns."""
    if data_df.empty:
        st.info("No matching videos found.")
        return

    display_cols = ["title", "duration_formatted", "view_count", "like_count", "comment_count", "published_at", "url"]
    existing_cols = [c for c in display_cols if c in data_df.columns]

    renamed = {
        "title": "Title",
        "duration_formatted": "Duration",
        "view_count": "Views",
        "like_count": "Likes",
        "comment_count": "Comments",
        "published_at": "Published Date",
        "url": "YouTube Link",
    }

    render_df = data_df[existing_cols].rename(columns=renamed)
    st.dataframe(
        render_df,
        use_container_width=True,
        column_config={
            "YouTube Link": st.column_config.LinkColumn("Link"),
            "Views": st.column_config.NumberColumn("Views", format="%d"),
            "Likes": st.column_config.NumberColumn("Likes", format="%d"),
            "Comments": st.column_config.NumberColumn("Comments", format="%d"),
        },
        hide_index=True,
    )


def render_instagram_dashboard(identifier: str, max_posts: int, trigger: bool):
    """Render Instagram Profile OSINT dashboard."""
    st.markdown('<div class="main-title">Instagram Profile OSINT & Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Profile details, follower metrics, engagement rate, and recent post types</div>', unsafe_allow_html=True)

    if trigger or "ig_profile" not in st.session_state or st.session_state.get("ig_identifier") != identifier:
        if trigger:
            with st.spinner(f"Fetching Instagram profile '{identifier}'..."):
                client = InstagramOSINTClient()
                try:
                    profile, posts = client.analyze_profile(identifier, max_posts=max_posts)
                    st.session_state["ig_profile"] = profile
                    st.session_state["ig_posts"] = posts
                    st.session_state["ig_identifier"] = identifier
                except Exception as e:
                    st.error(f"Failed to inspect Instagram profile: {e}")
                    return

    if "ig_profile" not in st.session_state:
        st.info("👈 Enter an Instagram Username in the sidebar and click **Analyze Instagram Profile** to begin.")
        return

    profile = st.session_state["ig_profile"]
    posts = st.session_state["ig_posts"]

    analyzer = InstagramProfileAnalyzer(profile, posts)
    metrics = analyzer.get_summary_metrics()

    col_av, col_info = st.columns([1, 6])
    with col_av:
        if profile.profile_pic_url:
            st.image(profile.profile_pic_url, width=100)
        else:
            st.markdown("### 📸")
    with col_info:
        st.markdown(f"## {profile.full_name or profile.username} `@{profile.username}`")
        if profile.biography:
            st.markdown(f"**Bio:** {profile.biography}")

    # Metrics
    st.markdown("### 📊 Profile KPIs")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Followers", format_number(metrics["followers"]))
    with m2:
        st.metric("Following", format_number(metrics["following"]))
    with m3:
        st.metric("Total Profile Posts", f"{metrics['total_profile_posts']:,}")
    with m4:
        st.metric("Engagement Rate", f"{metrics['engagement_rate_pct']}%")
    with m5:
        st.metric("Account Type", "Verified ✓" if metrics["is_verified"] else "Standard")

    st.markdown("---")

    if posts:
        post_df = analyzer.dataframe
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            fig_types = px.pie(
                post_df,
                names="post_type",
                title="Post Types Breakdown (Photos vs Reels vs Carousel)",
                color_discrete_sequence=px.colors.sequential.RdPu,
            )
            st.plotly_chart(fig_types, use_container_width=True)
        with p_c2:
            fig_bar = px.bar(
                post_df,
                x="published_at",
                y="like_count",
                color="post_type",
                title="Likes per Post Timeline",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("### 📝 Recent Posts Table")
        st.dataframe(
            post_df[["post_type", "like_count", "comment_count", "published_at", "caption", "url"]].rename(
                columns={
                    "post_type": "Type",
                    "like_count": "Likes",
                    "comment_count": "Comments",
                    "published_at": "Posted At",
                    "caption": "Caption",
                    "url": "Post Link",
                }
            ),
            use_container_width=True,
            column_config={
                "Post Link": st.column_config.LinkColumn("Link"),
            },
            hide_index=True,
        )


def main():
    platform, identifier, max_items, trigger = render_sidebar()

    if platform == "YouTube Channel":
        render_youtube_dashboard(identifier, max_items, trigger)
    else:
        render_instagram_dashboard(identifier, max_items, trigger)


if __name__ == "__main__":
    main()
