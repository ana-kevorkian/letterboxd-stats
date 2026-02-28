import streamlit as st
import pandas as pd
import plotly.express as px

from scraper import DiaryEntry, scrape_user

st.set_page_config(
    page_title="Letterboxd Tag Stats",
    page_icon="🎬",
    layout="wide",
)

# ── helpers ────────────────────────────────────────────────────────────────────

def entries_to_df(entries: list[DiaryEntry]) -> pd.DataFrame:
    """
    Convert diary entries to a DataFrame.
    Films with multiple tags get one row per tag (exploded).
    Films with no tags get a single row with tag=None.
    """
    rows = []
    for e in entries:
        base = dict(
            title=e.title,
            year=e.year,
            rating=e.rating,
            date=e.date,
            rewatch=e.rewatch,
        )
        if e.tags:
            for tag in e.tags:
                rows.append({**base, "tag": tag.strip()})
        else:
            rows.append({**base, "tag": None})
    return pd.DataFrame(rows)


def compute_tag_stats(df: pd.DataFrame, overall_avg: float) -> pd.DataFrame:
    rated = df[df["rating"].notna() & df["tag"].notna()]
    stats = (
        rated.groupby("tag")
        .agg(films=("rating", "count"), avg=("rating", "mean"), median=("rating", "median"))
        .reset_index()
        .assign(vs_avg=lambda d: d["avg"] - overall_avg)
        .round({"avg": 2, "median": 2, "vs_avg": 2})
        .sort_values("films", ascending=False)
    )
    return stats


# ── page ───────────────────────────────────────────────────────────────────────

st.title("🎬 Letterboxd Tag Stats")
st.caption(
    "Do you rate movies higher at a certain theater? With a certain person? "
    "Tag your Letterboxd diary entries and find out."
)

with st.form("search"):
    col1, col2 = st.columns([4, 1])
    username = col1.text_input(
        "Letterboxd username",
        placeholder="e.g. zackdanger",
    )
    deep_scan = col2.checkbox(
        "Deep scan",
        help=(
            "Visit each diary entry's individual page to find tags. "
            "Much slower, but catches tags that Letterboxd doesn't show "
            "on the diary listing page."
        ),
    )
    submitted = st.form_submit_button("Analyze ▶", type="primary")

if not submitted:
    st.stop()

if not username.strip():
    st.warning("Please enter a username.")
    st.stop()

username = username.strip()

# ── scrape ─────────────────────────────────────────────────────────────────────

# Use session state to avoid re-scraping on widget interactions
cache_key = f"{username}|{deep_scan}"
if st.session_state.get("_cache_key") == cache_key and "entries" in st.session_state:
    entries = st.session_state["entries"]
else:
    status = st.empty()
    prog = st.progress(0)

    def on_progress(msg: str, pct):
        status.caption(msg)
        if pct is not None:
            prog.progress(pct)

    entries = scrape_user(username, on_progress=on_progress, deep_scan=deep_scan)

    prog.empty()
    status.empty()

    st.session_state["entries"] = entries
    st.session_state["_cache_key"] = cache_key

if not entries:
    st.error(
        f"No diary entries found for **{username}**. "
        "Check that the username is correct and the profile is public."
    )
    st.stop()

# ── build dataframe ────────────────────────────────────────────────────────────

df = entries_to_df(entries)
rated = df[df["rating"].notna()]
overall_avg = rated["rating"].mean()
unique_tags = int(df["tag"].dropna().nunique())

# ── top-line metrics ───────────────────────────────────────────────────────────

st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Diary entries", len(entries))
c2.metric("Rated films", rated["title"].nunique())
c3.metric("Avg rating", f"{overall_avg:.2f} ★")
c4.metric("Unique tags", unique_tags)

if unique_tags == 0:
    st.info(
        "No tags were found in this diary. "
        "Tags are added to individual Letterboxd diary entries — "
        "look for the tag field when logging or editing a film."
    )
    if not deep_scan:
        st.caption(
            "💡 Tags sometimes don't appear on the diary listing page. "
            "Try enabling **Deep scan** to check each entry individually."
        )
    st.stop()

# ── tag stats ──────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Rating by tag")

tag_stats = compute_tag_stats(df, overall_avg)
max_films = int(tag_stats["films"].max())

min_films = st.slider(
    "Minimum films per tag",
    min_value=1,
    max_value=max(max_films, 2),
    value=min(3, max_films),
)
filtered = tag_stats[tag_stats["films"] >= min_films]

if filtered.empty:
    st.info("No tags with that many films. Lower the slider.")
    st.stop()

# Bar chart: avg rating per tag, colored by deviation from your overall avg
bar_height = max(350, len(filtered) * 30)
fig = px.bar(
    filtered.sort_values("avg"),
    x="avg",
    y="tag",
    orientation="h",
    color="vs_avg",
    color_continuous_scale="RdYlGn",
    color_continuous_midpoint=0,
    range_x=[0, 5.2],
    labels={
        "avg": "Avg Rating (★)",
        "tag": "Tag",
        "vs_avg": "vs Your Avg",
        "films": "Films",
        "median": "Median",
    },
    hover_data={"films": True, "median": True, "vs_avg": True},
    height=bar_height,
)
fig.add_vline(
    x=overall_avg,
    line_dash="dash",
    line_color="rgba(255,255,255,0.6)",
    annotation_text=f"your avg ({overall_avg:.2f})",
    annotation_position="top right",
)
fig.update_layout(
    yaxis_title=None,
    coloraxis_colorbar_title="vs avg",
    margin=dict(l=0, r=10, t=20, b=20),
)
st.plotly_chart(fig, use_container_width=True)

# Summary table
st.dataframe(
    filtered.rename(
        columns={
            "tag": "Tag",
            "films": "Films",
            "avg": "Avg Rating",
            "median": "Median",
            "vs_avg": "vs Your Avg",
        }
    ),
    use_container_width=True,
    hide_index=True,
    column_config={
        "vs Your Avg": st.column_config.NumberColumn(format="%+.2f ★"),
        "Avg Rating": st.column_config.NumberColumn(format="%.2f ★"),
        "Median": st.column_config.NumberColumn(format="%.1f ★"),
    },
)

# ── rating distribution per tag ────────────────────────────────────────────────

st.divider()
st.subheader("Rating distribution")

tag_choice_dist = st.selectbox(
    "Compare tag vs. overall",
    options=sorted(filtered["tag"].tolist()),
    key="dist_tag",
)

if tag_choice_dist:
    tag_ratings = df[df["tag"] == tag_choice_dist]["rating"].dropna()
    all_ratings = rated["rating"].dropna()

    dist_df = pd.concat(
        [
            tag_ratings.rename("rating").to_frame().assign(group=f"#{tag_choice_dist}"),
            all_ratings.rename("rating").to_frame().assign(group="All films"),
        ]
    )

    fig2 = px.histogram(
        dist_df,
        x="rating",
        color="group",
        barmode="overlay",
        nbins=10,
        opacity=0.7,
        labels={"rating": "Rating (★)", "group": ""},
        color_discrete_map={
            f"#{tag_choice_dist}": "#00c030",
            "All films": "#888888",
        },
    )
    fig2.update_layout(bargap=0.1, margin=dict(t=20))
    st.plotly_chart(fig2, use_container_width=True)

# ── film explorer ──────────────────────────────────────────────────────────────

st.divider()
st.subheader("Films by tag")

tag_choice_films = st.selectbox(
    "Browse films tagged with…",
    options=sorted(filtered["tag"].tolist()),
    key="films_tag",
)

if tag_choice_films:
    film_rows = (
        df[df["tag"] == tag_choice_films][["title", "year", "rating", "date", "rewatch"]]
        .drop_duplicates("title")
        .sort_values("rating", ascending=False)
    )
    st.dataframe(
        film_rows,
        use_container_width=True,
        hide_index=True,
        column_config={
            "rating": st.column_config.NumberColumn("Rating", format="%.1f ★"),
            "rewatch": st.column_config.CheckboxColumn("Rewatch"),
        },
    )
