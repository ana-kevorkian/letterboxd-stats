import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Letterboxd Tag Stats",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 Letterboxd Tag Stats")
st.caption(
    "Do you rate movies higher at a certain theater? With a certain person? "
    "Tag your Letterboxd diary entries and find out."
)

with st.expander("How to get your data", expanded=True):
    st.markdown(
        """
        1. Go to [letterboxd.com/settings/data](https://letterboxd.com/settings/data)
        2. Click **Export your data** — you'll receive a ZIP file by email
        3. Unzip it and upload the **diary.csv** file below
        """
    )

uploaded = st.file_uploader("Upload your diary.csv", type="csv")

if not uploaded:
    st.stop()

# ── parse ──────────────────────────────────────────────────────────────────────

raw = pd.read_csv(uploaded)
raw.columns = [c.strip() for c in raw.columns]

if "Name" not in raw.columns or "Rating" not in raw.columns:
    st.error(
        "This doesn't look like a Letterboxd diary.csv. "
        "Make sure you're uploading the right file from the export ZIP."
    )
    st.stop()

raw = raw.rename(columns={
    "Name": "title",
    "Year": "year",
    "Rating": "rating",
    "Watched Date": "date",
    "Rewatch": "rewatch",
    "Tags": "tags_raw",
})

raw["rating"] = pd.to_numeric(raw["rating"], errors="coerce")
raw["rewatch"] = raw["rewatch"].fillna("").str.strip().str.lower() == "yes"
raw["tags_list"] = raw["tags_raw"].fillna("").apply(
    lambda x: [t.strip() for t in str(x).split(",") if t.strip()] if str(x).strip() not in ("", "nan") else []
)

# Explode so each (film, tag) pair gets its own row; untagged films keep tag=None
tagged = raw[raw["tags_list"].map(len) > 0].explode("tags_list").rename(columns={"tags_list": "tag"})
untagged = raw[raw["tags_list"].map(len) == 0].copy()
untagged["tag"] = None
df = pd.concat([tagged[["title", "year", "rating", "date", "rewatch", "tag"]],
                untagged[["title", "year", "rating", "date", "rewatch", "tag"]]], ignore_index=True)

# ── top-line metrics ───────────────────────────────────────────────────────────

rated = df[df["rating"].notna()]
overall_avg = rated["rating"].mean()
unique_tags = int(df["tag"].dropna().nunique())

st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Diary entries", len(raw))
c2.metric("Rated films", rated["title"].nunique())
c3.metric("Avg rating", f"{overall_avg:.2f} ★")
c4.metric("Unique tags", unique_tags)

if unique_tags == 0:
    st.info(
        "No tags found in your diary.csv. "
        "Add tags to your Letterboxd diary entries, re-export, and upload again."
    )
    st.stop()

# ── tag stats ──────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Rating by tag")

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

fig = px.bar(
    filtered.sort_values("avg"),
    x="avg",
    y="tag",
    orientation="h",
    color="vs_avg",
    color_continuous_scale="RdYlGn",
    color_continuous_midpoint=0,
    range_x=[0, 5.2],
    labels={"avg": "Avg Rating (★)", "tag": "Tag", "vs_avg": "vs Your Avg", "films": "Films", "median": "Median"},
    hover_data={"films": True, "median": True, "vs_avg": True},
    height=max(350, len(filtered) * 30),
)
fig.add_vline(
    x=overall_avg,
    line_dash="dash",
    line_color="rgba(255,255,255,0.6)",
    annotation_text=f"your avg ({overall_avg:.2f})",
    annotation_position="top right",
)
fig.update_layout(yaxis_title=None, coloraxis_colorbar_title="vs avg", margin=dict(l=0, r=10, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    filtered.rename(columns={"tag": "Tag", "films": "Films", "avg": "Avg Rating",
                              "median": "Median", "vs_avg": "vs Your Avg"}),
    use_container_width=True,
    hide_index=True,
    column_config={
        "vs Your Avg": st.column_config.NumberColumn(format="%+.2f ★"),
        "Avg Rating": st.column_config.NumberColumn(format="%.2f ★"),
        "Median": st.column_config.NumberColumn(format="%.1f ★"),
    },
)

# ── rating distribution ────────────────────────────────────────────────────────

st.divider()
st.subheader("Rating distribution")

tag_choice_dist = st.selectbox("Compare tag vs. overall", options=sorted(filtered["tag"].tolist()), key="dist")

if tag_choice_dist:
    dist_df = pd.concat([
        df[df["tag"] == tag_choice_dist]["rating"].dropna().to_frame().assign(group=f"#{tag_choice_dist}"),
        rated["rating"].dropna().to_frame().assign(group="All films"),
    ])
    fig2 = px.histogram(
        dist_df, x="rating", color="group", barmode="overlay", nbins=10, opacity=0.7,
        labels={"rating": "Rating (★)", "group": ""},
        color_discrete_map={f"#{tag_choice_dist}": "#00c030", "All films": "#888888"},
    )
    fig2.update_layout(bargap=0.1, margin=dict(t=20))
    st.plotly_chart(fig2, use_container_width=True)

# ── film explorer ──────────────────────────────────────────────────────────────

st.divider()
st.subheader("Films by tag")

tag_choice_films = st.selectbox("Browse films tagged with…", options=sorted(filtered["tag"].tolist()), key="films")

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
