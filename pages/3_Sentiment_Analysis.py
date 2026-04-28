import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data import load_movies, load_reviews_with_sentiment  # noqa: E402
from utils.style import apply_editorial_style, chapter_cover, chapter_footer, COLORS  # noqa: E402

st.set_page_config(page_title="Sentiment Analysis", layout="wide")
apply_editorial_style()
alt.data_transformers.disable_max_rows()

movies = load_movies()
reviews = load_reviews_with_sentiment()


@st.cache_data
def build_merged(reviews, movies_df):
    movie_agg = reviews.groupby('movie_id').agg(
        n_reviews=('content', 'count'),
        avg_sentiment=('sentiment', 'mean'),
        avg_user_rating=('rating', 'mean'),
    ).reset_index()
    valid = movies_df[(movies_df['budget'] > 0) & (movies_df['revenue'] > 0)]
    return valid.merge(movie_agg, left_on='id', right_on='movie_id', how='inner')


merged = build_merged(reviews, movies)

chapter_cover(
    number="Chapter 03",
    title="Sentiment Analysis",
    deck="Do review sentiments predict box office success — or are they decoupled?"
)

# ---------- Sidebar ----------
st.sidebar.header("Settings")
min_reviews = st.sidebar.slider("Minimum reviews per movie", 1, 10, 1)
merged_f = merged[merged['n_reviews'] >= min_reviews].copy()
st.sidebar.caption(f"{len(merged_f)} movies with {min_reviews}+ reviews")

st.sidebar.markdown("---")
st.sidebar.markdown("**Sentiment vs Success scatter plots**")
color_mode = st.sidebar.radio(
    "Color points by",
    ["Single color", "Primary genre"],
    help="Color by primary genre to see whether the sentiment/revenue relationship varies across categories."
)

# Attach primary genre (first genre in the list) to each movie
merged_f['primary_genre'] = merged_f['genre_list'].apply(
    lambda gl: gl[0] if isinstance(gl, list) and len(gl) > 0 else 'Unknown'
)
# Keep only top 8 genres + "Other" to avoid legend overload
top_genres = (merged_f['primary_genre'].value_counts().head(8).index.tolist())
merged_f['primary_genre_grouped'] = merged_f['primary_genre'].apply(
    lambda g: g if g in top_genres else 'Other'
)

# ---------- Top-line metrics ----------
pos_pct = (reviews['sentiment'] > 0).mean() * 100
col_s1, col_s2, col_s3 = st.columns(3)
col_s1.metric("Total Reviews", f"{len(reviews):,}")
col_s2.metric("Positive Reviews", f"{pos_pct:.0f}%")
col_s3.metric("Avg Sentiment", f"{reviews['sentiment'].mean():.2f}")

st.markdown("")

# ---------- Distributions ----------
st.markdown("### Distribution of Reviews")
st.markdown("Three angles on the review data: how many each movie gets, "
            "what ratings users give, and what VADER reads from the text.")

col1, col2, col3 = st.columns(3)

with col1:
    rpm = reviews.groupby('movie_id').size().reset_index(name='review_count')
    h1 = alt.Chart(rpm).mark_bar(color=COLORS['blue'], opacity=0.85).encode(
        x=alt.X('review_count:Q', bin=alt.Bin(maxbins=20),
                title='Reviews per Movie'),
        y=alt.Y('count():Q', title='Movies'),
        tooltip=[
            alt.Tooltip('review_count:Q', bin=alt.Bin(maxbins=20),
                        title='Reviews'),
            alt.Tooltip('count():Q', title='Movies'),
        ]
    ).properties(height=260, title='Reviews per Movie')
    st.altair_chart(h1, use_container_width=True)

with col2:
    r_clean = reviews[reviews['rating'].notna()].copy()
    h2 = alt.Chart(r_clean).mark_bar(color=COLORS['green'], opacity=0.85).encode(
        x=alt.X('rating:Q', bin=alt.Bin(maxbins=20), title='Rating (0–10)'),
        y=alt.Y('count():Q', title='Reviews'),
        tooltip=[
            alt.Tooltip('rating:Q', bin=alt.Bin(maxbins=20), title='Rating'),
            alt.Tooltip('count():Q', title='Count'),
        ]
    ).properties(height=260, title='User Rating Distribution')
    st.altair_chart(h2, use_container_width=True)

with col3:
    h3 = alt.Chart(reviews).mark_bar(color=COLORS['dark'], opacity=0.85).encode(
        x=alt.X('sentiment:Q', bin=alt.Bin(maxbins=40),
                title='VADER Compound'),
        y=alt.Y('count():Q', title='Reviews'),
        tooltip=[
            alt.Tooltip('sentiment:Q', bin=alt.Bin(maxbins=40),
                        title='Sentiment'),
            alt.Tooltip('count():Q', title='Count'),
        ]
    ).properties(height=260, title='VADER Sentiment')
    st.altair_chart(h3, use_container_width=True)

st.warning(f"**Methodological note:** {pos_pct:.0f}% of reviews are positive, so TMDB reviews have a strong positivity bias. "
           "We therefore interpret sentiment as a signal from engaged reviewers, not as a perfectly representative measure of all audience opinion.")

# ---------- Sentiment vs Success ----------
st.markdown("---")
st.markdown("### Sentiment vs Movie Success")
st.markdown("Does positive sentiment translate into higher ratings or more revenue? "
            "This connects audience language back to the project's central question of movie success. "
            "Hover over any dot to see the movie.")

col4, col5 = st.columns(2)

with col4:
    corr1 = merged_f[['vote_average', 'avg_sentiment']].corr().iloc[0, 1]
    legend_sel_1 = alt.selection_point(fields=['primary_genre_grouped'], bind='legend')
    base_s1 = alt.Chart(merged_f).mark_circle(opacity=0.55).encode(
        x=alt.X('vote_average:Q', title='TMDB Rating', scale=alt.Scale(zero=False)),
        y=alt.Y('avg_sentiment:Q', title='Average Sentiment'),
        tooltip=[
            alt.Tooltip('title:N', title='Movie'),
            alt.Tooltip('primary_genre:N', title='Primary genre'),
            alt.Tooltip('vote_average:Q', title='Rating', format='.1f'),
            alt.Tooltip('avg_sentiment:Q', title='Sentiment', format='.2f'),
            alt.Tooltip('n_reviews:Q', title='Reviews'),
        ]
    )
    if color_mode == "Single color":
        s1 = base_s1.encode(color=alt.value(COLORS['green'])).interactive().properties(
            height=380, title=f'Sentiment vs Rating  (r = {corr1:.2f})'
        )
    else:
        s1 = base_s1.encode(
            color=alt.Color('primary_genre_grouped:N',
                            scale=alt.Scale(scheme='set2'),
                            title='Primary genre'),
            opacity=alt.condition(legend_sel_1, alt.value(0.7), alt.value(0.1)),
        ).add_params(legend_sel_1).interactive().properties(
            height=380, title=f'Sentiment vs Rating  (r = {corr1:.2f})'
        )
    st.altair_chart(s1, use_container_width=True)

with col5:
    merged_log = merged_f.copy()
    merged_log['log_revenue'] = np.log10(merged_log['revenue'].clip(lower=1))
    corr2 = merged_log[['avg_sentiment', 'log_revenue']].corr().iloc[0, 1]

    legend_sel_2 = alt.selection_point(fields=['primary_genre_grouped'], bind='legend')
    base_s2 = alt.Chart(merged_log).mark_circle(opacity=0.55).encode(
        x=alt.X('avg_sentiment:Q', title='Average Sentiment'),
        y=alt.Y('log_revenue:Q', title='log₁₀(Revenue)'),
        tooltip=[
            alt.Tooltip('title:N', title='Movie'),
            alt.Tooltip('primary_genre:N', title='Primary genre'),
            alt.Tooltip('avg_sentiment:Q', title='Sentiment', format='.2f'),
            alt.Tooltip('revenue:Q', title='Revenue ($)', format=',.0f'),
        ]
    )
    if color_mode == "Single color":
        s2 = base_s2.encode(color=alt.value(COLORS['primary'])).interactive().properties(
            height=380, title=f'Sentiment vs Revenue  (r = {corr2:.2f})'
        )
    else:
        s2 = base_s2.encode(
            color=alt.Color('primary_genre_grouped:N',
                            scale=alt.Scale(scheme='set2'),
                            title='Primary genre'),
            opacity=alt.condition(legend_sel_2, alt.value(0.7), alt.value(0.1)),
        ).add_params(legend_sel_2).interactive().properties(
            height=380, title=f'Sentiment vs Revenue  (r = {corr2:.2f})'
        )
    st.altair_chart(s2, use_container_width=True)

st.markdown(f"""
> **Key Finding:** Sentiment has a weak positive correlation with ratings (r = {corr1:.2f})
but almost no relationship with revenue (r = {corr2:.2f}). **Critical reception
and commercial success are largely independent** — a movie can be a box-office hit
regardless of how reviewers feel about it.
>
> Try switching to **"Color points by Primary genre"** in the sidebar: genre differences become easier to see,
but the pattern should be interpreted cautiously because each movie is assigned only one primary genre.
""")

# ---------- VADER accuracy ----------
st.markdown("---")
st.markdown("### How Well Does VADER Capture Sentiment?")
st.markdown("Each faint dot is one review. The red line shows the **average VADER score** "
            "at each user-rating level — if VADER were perfect, the line would rise steeply "
            "from left to right.")

valid_both = reviews[reviews['rating'].notna()].copy()
valid_both['rating_bin'] = (valid_both['rating'] * 2).round() / 2
trend = valid_both.groupby('rating_bin')['sentiment'].mean().reset_index()

sample_n = min(3000, len(valid_both))
sample = valid_both.sample(sample_n, random_state=42)

dots = alt.Chart(sample).mark_circle(
    opacity=0.15, size=15, color=COLORS['dark']
).encode(
    x=alt.X('rating:Q', title='User Rating'),
    y=alt.Y('sentiment:Q', title='VADER Compound'),
    tooltip=[
        alt.Tooltip('rating:Q', title='Rating'),
        alt.Tooltip('sentiment:Q', title='Sentiment', format='.2f'),
    ]
)

trend_line = alt.Chart(trend).mark_line(
    color=COLORS['primary'], strokeWidth=3
).encode(x='rating_bin:Q', y='sentiment:Q')

trend_points = alt.Chart(trend).mark_circle(
    color=COLORS['primary'], size=60
).encode(
    x='rating_bin:Q', y='sentiment:Q',
    tooltip=[
        alt.Tooltip('rating_bin:Q', title='Rating'),
        alt.Tooltip('sentiment:Q', title='Avg VADER', format='.2f'),
    ]
)

corr3 = valid_both[['sentiment', 'rating']].corr().iloc[0, 1]
st.altair_chart(
    (dots + trend_line + trend_points).properties(
        height=400,
        title=f'VADER vs User Rating  (r = {corr3:.2f})'
    ),
    use_container_width=True
)

st.markdown(f"> VADER's correlation with user ratings is modest (r = {corr3:.2f}). "
            "Long reviews often contain mixed language — praising visuals while "
            "criticizing the plot — which dilutes VADER's single compound score.")

chapter_footer(
    prev_label="Chapter 02 · Genre Analysis",
    prev_path="pages/2_Genre_Analysis.py",
    next_label="Chapter 04 · Text Analysis",
    next_path="pages/4_Text_Analysis.py",
)
