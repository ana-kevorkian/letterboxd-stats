import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Letterboxd Stats",
    page_icon="🎬",
    layout="wide",
)

# ── Letterboxd-style CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;600;700&display=swap');

/* Base */
html, body, .stApp {
    background-color: #14181c !important;
    font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #fff;
}

/* Hide Streamlit chrome */
#MainMenu, footer, .stDeployButton { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }

/* Nav bar */
.lb-nav {
    background: #14181c;
    border-bottom: 1px solid #456;
    padding: 0.85rem 2rem;
    margin: -4rem -4rem 2.5rem -4rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.lb-nav-logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
}
.lb-nav-circles {
    display: flex;
    gap: -4px;
}
.lb-circle {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    margin-right: -5px;
    opacity: 0.9;
}
.lb-circle-1 { background: #40bcf4; }
.lb-circle-2 { background: #00e054; }
.lb-circle-3 { background: #ff8000; }
.lb-nav-wordmark {
    font-size: 1.05rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.lb-nav-subtitle {
    font-size: 0.8rem;
    color: #678;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-left: 1px solid #456;
    padding-left: 1rem;
    margin-left: 0.25rem;
}

/* Page title */
.lb-page-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.25rem;
    letter-spacing: -0.01em;
}
.lb-page-subtitle {
    font-size: 0.95rem;
    color: #9ab;
    margin-bottom: 2rem;
}

/* Section headers */
.lb-section-header {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #9ab;
    border-bottom: 1px solid #2c3440;
    padding-bottom: 0.5rem;
    margin-bottom: 1.25rem;
    margin-top: 2rem;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #2c3440 !important;
    border: 1px solid #456 !important;
    border-radius: 6px !important;
    padding: 1.1rem 1.25rem !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #9ab !important;
}
[data-testid="stMetricValue"] {
    color: #00e054 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* Upload area */
[data-testid="stFileUploader"] {
    background: #2c3440 !important;
    border: 2px dashed #456 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
}

/* Expander */
details {
    background: #2c3440 !important;
    border: 1px solid #456 !important;
    border-radius: 6px !important;
}
details summary {
    color: #9ab !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.75rem 1rem !important;
}
details > div {
    padding: 0 1rem 1rem 1rem !important;
}

/* Instruction steps */
.lb-steps ol {
    padding-left: 1.25rem;
    color: #9ab;
    line-height: 2;
    font-size: 0.95rem;
}
.lb-steps a { color: #00e054 !important; text-decoration: none; }
.lb-steps a:hover { text-decoration: underline; }

/* Submit button */
[data-testid="stFormSubmitButton"] > button {
    background: #00e054 !important;
    color: #14181c !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 0.55rem 1.75rem !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    transition: background 0.15s ease !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: #b4e000 !important;
}

/* Selectbox */
[data-testid="stSelectbox"] label {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #9ab !important;
}

/* Slider */
[data-testid="stSlider"] label {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #9ab !important;
}

/* Divider */
hr { border-color: #2c3440 !important; margin: 2rem 0 !important; }

/* DataFrames */
[data-testid="stDataFrame"] {
    border: 1px solid #2c3440;
    border-radius: 6px;
    overflow: hidden;
}
[data-testid="stDataFrame"] table {
    background: #1e2530 !important;
}
[data-testid="stDataFrame"] th {
    background: #2c3440 !important;
    color: #9ab !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid #456 !important;
}
[data-testid="stDataFrame"] td {
    color: #fff !important;
    border-bottom: 1px solid #1e2530 !important;
}

/* Info / warning boxes */
[data-testid="stAlert"] {
    background: #2c3440 !important;
    border: 1px solid #456 !important;
    border-radius: 6px !important;
    color: #9ab !important;
}
</style>

<div class="lb-nav">
    <div class="lb-nav-logo">
        <div class="lb-nav-circles">
            <div class="lb-circle lb-circle-1"></div>
            <div class="lb-circle lb-circle-2"></div>
            <div class="lb-circle lb-circle-3"></div>
        </div>
        <span class="lb-nav-wordmark">Letterboxd</span>
    </div>
    <span class="lb-nav-subtitle">Tag Stats</span>
</div>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="lb-page-title">Your Letterboxd Stats</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="lb-page-subtitle">Discover whether you rate films higher at a certain theater, '
    'with a certain person, or in any context you track with tags.</p>',
    unsafe_allow_html=True,
)

# ── Upload ─────────────────────────────────────────────────────────────────────
with st.expander("HOW TO EXPORT YOUR DATA", expanded=True):
    st.markdown(
        """<div class="lb-steps"><ol>
        <li>Go to <a href="https://letterboxd.com/settings/data" target="_blank">letterboxd.com/settings/data</a></li>
        <li>Click <strong>Export your data</strong> — Letterboxd will email you a ZIP file</li>
        <li>Unzip it and upload the <strong>diary.csv</strong> file below</li>
        </ol></div>""",
        unsafe_allow_html=True,
    )

uploaded = st.file_uploader("", type="csv", label_visibility="collapsed")

if not uploaded:
    st.stop()

# ── Parse CSV ──────────────────────────────────────────────────────────────────
raw = pd.read_csv(uploaded)
raw.columns = [c.strip() for c in raw.columns]

if "Name" not in raw.columns or "Rating" not in raw.columns:
    st.error("This doesn't look like a Letterboxd diary.csv. Make sure you're uploading the right file.")
    st.stop()

raw = raw.rename(columns={
    "Name": "title", "Year": "year", "Rating": "rating",
    "Watched Date": "date", "Rewatch": "rewatch", "Tags": "tags_raw",
})
raw["rating"] = pd.to_numeric(raw["rating"], errors="coerce")
raw["rewatch"] = raw["rewatch"].fillna("").str.strip().str.lower() == "yes"
raw["tags_list"] = raw["tags_raw"].fillna("").apply(
    lambda x: [t.strip() for t in str(x).split(",") if t.strip()]
    if str(x).strip() not in ("", "nan") else []
)

tagged = raw[raw["tags_list"].map(len) > 0].explode("tags_list").rename(columns={"tags_list": "tag"})
untagged = raw[raw["tags_list"].map(len) == 0].copy()
untagged["tag"] = None
df = pd.concat(
    [tagged[["title", "year", "rating", "date", "rewatch", "tag"]],
     untagged[["title", "year", "rating", "date", "rewatch", "tag"]]],
    ignore_index=True,
)

# ── Metrics ────────────────────────────────────────────────────────────────────
rated = df[df["rating"].notna()]
overall_avg = rated["rating"].mean()
unique_tags = int(df["tag"].dropna().nunique())

st.markdown('<p class="lb-section-header">Overview</p>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Diary entries", f"{len(raw):,}")
c2.metric("Rated films", f"{rated['title'].nunique():,}")
c3.metric("Avg rating", f"{overall_avg:.2f} ★")
c4.metric("Unique tags", f"{unique_tags:,}")

if unique_tags == 0:
    st.info(
        "No tags found in your diary.csv. "
        "Add tags to your Letterboxd diary entries, re-export, and upload again."
    )
    st.stop()

# ── Tag stats ──────────────────────────────────────────────────────────────────
tag_stats = (
    rated[rated["tag"].notna()]
    .groupby("tag")
    .agg(films=("rating", "count"), avg=("rating", "mean"), median=("rating", "median"))
    .reset_index()
    .assign(vs_avg=lambda d: d["avg"] - overall_avg)
    .round({"avg": 2, "median": 2, "vs_avg": 2})
    .sort_values("films", ascending=False)
)

max_films = int(tag_stats["films"].max())

st.markdown('<p class="lb-section-header">Rating by tag</p>', unsafe_allow_html=True)

min_films = st.slider(
    "Minimum films per tag",
    min_value=1, max_value=max(max_films, 2), value=min(3, max_films),
)
filtered = tag_stats[tag_stats["films"] >= min_films]

if filtered.empty:
    st.info("No tags with that many films. Lower the slider.")
    st.stop()

# Bar chart
fig = px.bar(
    filtered.sort_values("avg"),
    x="avg", y="tag", orientation="h",
    color="vs_avg",
    color_continuous_scale=[[0, "#ff8000"], [0.5, "#2c3440"], [1, "#00e054"]],
    color_continuous_midpoint=0,
    range_x=[0, 5.2],
    labels={"avg": "Avg Rating (★)", "tag": "Tag", "vs_avg": "vs Your Avg",
            "films": "Films", "median": "Median"},
    hover_data={"films": True, "median": True, "vs_avg": True},
    height=max(380, len(filtered) * 32),
)
fig.add_vline(
    x=overall_avg, line_dash="dash", line_color="#678",
    annotation_text=f"your avg ({overall_avg:.2f})",
    annotation_font_color="#9ab",
    annotation_position="top right",
)
fig.update_layout(
    paper_bgcolor="#14181c",
    plot_bgcolor="#1e2530",
    font_color="#fff",
    font_family="Source Sans 3, sans-serif",
    yaxis_title=None,
    xaxis=dict(gridcolor="#2c3440", zerolinecolor="#456"),
    yaxis=dict(gridcolor="#2c3440"),
    coloraxis_colorbar=dict(
        title="vs avg",
        tickfont=dict(color="#9ab"),
        titlefont=dict(color="#9ab"),
    ),
    margin=dict(l=0, r=10, t=10, b=20),
)
st.plotly_chart(fig, use_container_width=True)

# Table
st.dataframe(
    filtered.rename(columns={
        "tag": "Tag", "films": "Films", "avg": "Avg Rating",
        "median": "Median", "vs_avg": "vs Your Avg",
    }),
    use_container_width=True, hide_index=True,
    column_config={
        "vs Your Avg": st.column_config.NumberColumn(format="%+.2f ★"),
        "Avg Rating": st.column_config.NumberColumn(format="%.2f ★"),
        "Median": st.column_config.NumberColumn(format="%.1f ★"),
    },
)

# ── Rating distribution ────────────────────────────────────────────────────────
st.markdown('<p class="lb-section-header">Rating distribution</p>', unsafe_allow_html=True)

tag_choice_dist = st.selectbox(
    "Compare tag vs. overall", options=sorted(filtered["tag"].tolist()), key="dist"
)
if tag_choice_dist:
    dist_df = pd.concat([
        df[df["tag"] == tag_choice_dist]["rating"].dropna().to_frame().assign(group=f"#{tag_choice_dist}"),
        rated["rating"].dropna().to_frame().assign(group="All films"),
    ])
    fig2 = px.histogram(
        dist_df, x="rating", color="group", barmode="overlay", nbins=10, opacity=0.75,
        labels={"rating": "Rating (★)", "group": ""},
        color_discrete_map={f"#{tag_choice_dist}": "#00e054", "All films": "#456"},
    )
    fig2.update_layout(
        paper_bgcolor="#14181c", plot_bgcolor="#1e2530",
        font_color="#fff", font_family="Source Sans 3, sans-serif",
        xaxis=dict(gridcolor="#2c3440", zerolinecolor="#456"),
        yaxis=dict(gridcolor="#2c3440"),
        bargap=0.1, margin=dict(t=10, b=20),
        legend=dict(bgcolor="#2c3440", bordercolor="#456", borderwidth=1),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Film explorer ──────────────────────────────────────────────────────────────
st.markdown('<p class="lb-section-header">Films by tag</p>', unsafe_allow_html=True)

tag_choice_films = st.selectbox(
    "Browse films tagged with…", options=sorted(filtered["tag"].tolist()), key="films"
)
if tag_choice_films:
    film_rows = (
        df[df["tag"] == tag_choice_films][["title", "year", "rating", "date", "rewatch"]]
        .drop_duplicates("title")
        .sort_values("rating", ascending=False)
    )
    st.dataframe(
        film_rows, use_container_width=True, hide_index=True,
        column_config={
            "rating": st.column_config.NumberColumn("Rating", format="%.1f ★"),
            "rewatch": st.column_config.CheckboxColumn("Rewatch"),
        },
    )
