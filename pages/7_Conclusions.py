import json
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data import load_movies, load_reviews_with_sentiment  # noqa: E402
from utils.style import apply_editorial_style, chapter_cover, chapter_footer, COLORS  # noqa: E402

st.set_page_config(page_title="Conclusions", layout="wide")
apply_editorial_style()
alt.data_transformers.disable_max_rows()


chapter_cover(
    number="Chapter 07",
    title="Conclusions",
    deck="Six chapters, one consistent finding."
)


@st.cache_data
def load_conclusion_metrics():
    movies = load_movies()
    reviews = load_reviews_with_sentiment()

    valid_fin = movies[(movies['budget'] > 0) & (movies['revenue'] > 0)].copy()
    valid_fin['lost_money'] = valid_fin['revenue'] < valid_fin['budget']
    loss_rate = valid_fin['lost_money'].mean() * 100 if len(valid_fin) else np.nan

    def safe_json_loads(x):
        if isinstance(x, str):
            try:
                return json.loads(x)
            except Exception:
                return []
        if isinstance(x, list):
            return x
        return []

    country_rows = []
    for _, row in movies.iterrows():
        for c in safe_json_loads(row.get('production_countries', [])):
            country_name = c.get('name') if isinstance(c, dict) else None
            if country_name:
                country_rows.append(country_name)

    country_counts = pd.Series(country_rows).value_counts()
    us_share = (
        country_counts.get('United States of America', 0) / country_counts.sum() * 100
        if country_counts.sum() > 0 else np.nan
    )

    movie_agg = reviews.groupby('movie_id').agg(
        avg_sentiment=('sentiment', 'mean')
    ).reset_index()
    merged = valid_fin.merge(movie_agg, left_on='id', right_on='movie_id', how='inner')
    merged['log_revenue'] = np.log10(merged['revenue'].clip(lower=1))

    corr_rat = merged[['vote_average', 'avg_sentiment']].corr().iloc[0, 1]
    corr_rev = merged[['avg_sentiment', 'log_revenue']].corr().iloc[0, 1]

    return loss_rate, us_share, corr_rat, corr_rev


loss_rate, us_share, corr_rat, corr_rev = load_conclusion_metrics()

# =========================================================
# THE THESIS — single sentence, large, centered
# =========================================================
st.markdown(
    """
    <div style="
        margin: 2.5rem auto 3rem auto;
        max-width: 820px;
        text-align: center;
        font-family: 'DM Serif Display', Georgia, serif;
        line-height: 1.35;
    ">
        <div style="
            color: #A02030;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.32em;
            text-transform: uppercase;
            font-family: 'Source Sans 3', sans-serif;
            margin-bottom: 1.6rem;
        ">The Central Finding</div>
        <div style="font-size: 2.1rem; color: #1A1A1A;">
            The factors that predict <span style="color:#A02030;">box office revenue</span>
            are largely different from the factors that predict
            <span style="color:#A02030;">audience ratings</span>.
        </div>
        <div style="
            font-family: 'Source Serif 4', Georgia, serif;
            font-style: italic;
            font-size: 1.1rem;
            color: #5A5A5A;
            margin-top: 1.6rem;
            max-width: 640px;
            margin-left: auto;
            margin-right: auto;
        ">
            Across budget, genre, sentiment, language, networks, and geography &mdash;
            commercial success and critical reception operate on separate axes.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# THREE BIG NUMBERS
# =========================================================
def big_number(value, label, sublabel):
    return f"""
    <div style="
        text-align: center;
        padding: 1.5rem 1rem;
        border-top: 2px solid #A02030;
    ">
        <div style="
            font-family: 'DM Serif Display', Georgia, serif;
            font-size: 3.2rem;
            color: #1A1A1A;
            line-height: 1;
            margin-bottom: 0.6rem;
        ">{value}</div>
        <div style="
            font-family: 'Source Sans 3', sans-serif;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: #A02030;
            margin-bottom: 0.6rem;
        ">{label}</div>
        <div style="
            font-family: 'Source Serif 4', Georgia, serif;
            font-style: italic;
            font-size: 0.95rem;
            color: #4A4A4A;
            line-height: 1.45;
        ">{sublabel}</div>
    </div>
    """

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        big_number(
            f"r = {corr_rev:.2f}",
            "Sentiment vs Revenue",
            "Audience sentiment and box office are essentially uncorrelated."
        ),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        big_number(
            f"{loss_rate:.0f}%",
            "of Films Lost Money",
            "And many were well-reviewed &mdash; quality does not guarantee profit."
        ),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        big_number(
            f"{us_share:.0f}%",
            "Hollywood Concentration",
            "US share of production-country entries &mdash; the lens through which we see global film."
        ),
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:3rem;'></div>", unsafe_allow_html=True)

# =========================================================
# THE PROOF — bubble chart from Chapter 02
# =========================================================
st.markdown("### The Clearest Proof")
st.markdown(
    "If commercial and critical success were aligned, the genres earning the most would also "
    "be rated the highest. **They are not.** The top-right corner is empty."
)

@st.cache_data
def load_genre_data():
    movies = load_movies()
    valid = movies[(movies['budget'] > 0) & (movies['revenue'] > 0)].copy()
    exploded = valid.explode('genre_list')
    exploded = exploded[exploded['genre_list'].notna()]
    genre_both = exploded.groupby('genre_list').agg(
        avg_revenue=('revenue', 'mean'),
        avg_rating=('vote_average', 'mean'),
        count=('id', 'size')
    ).reset_index()
    genre_both = genre_both[genre_both['count'] >= 20]
    genre_both['avg_revenue_m'] = genre_both['avg_revenue'] / 1e6
    return genre_both

genre_both = load_genre_data()
label_threshold = genre_both.nlargest(10, 'count')

bubble = alt.Chart(genre_both).mark_circle(
    opacity=0.7, stroke='white', strokeWidth=0.5
).encode(
    x=alt.X('avg_revenue_m:Q', title='Average Revenue (Million $)'),
    y=alt.Y('avg_rating:Q', title='Average Rating', scale=alt.Scale(zero=False)),
    size=alt.Size('count:Q', title='Number of Movies', scale=alt.Scale(range=[100, 2000])),
    color=alt.value(COLORS['blue']),
    tooltip=[
        alt.Tooltip('genre_list:N', title='Genre'),
        alt.Tooltip('avg_revenue_m:Q', title='Avg Revenue ($M)', format='.0f'),
        alt.Tooltip('avg_rating:Q', title='Avg Rating', format='.2f'),
        alt.Tooltip('count:Q', title='Movies'),
    ]
)

text = alt.Chart(label_threshold).mark_text(dy=-14, fontSize=11, fontWeight='bold').encode(
    x='avg_revenue_m:Q', y='avg_rating:Q', text='genre_list:N'
)

annotation_x = float(genre_both['avg_revenue_m'].quantile(0.80))
annotation_y = float(genre_both['avg_rating'].quantile(0.92))
annotation_df = pd.DataFrame({
    'x': [annotation_x],
    'y': [annotation_y],
    'label': ['← This corner is nearly empty']
})
annotation = alt.Chart(annotation_df).mark_text(
    align='left', fontSize=11, color=COLORS['primary'], fontStyle='italic'
).encode(x='x:Q', y='y:Q', text='label:N')

st.altair_chart(
    (bubble + text + annotation).properties(height=460),
    use_container_width=True
)

st.markdown("<div style='height:2.5rem;'></div>", unsafe_allow_html=True)

# =========================================================
# SIX FINDINGS — one line each
# =========================================================
st.markdown("### What Each Chapter Showed")

findings = [
    ("01", "Budget buys revenue, not ratings.",
     "Expensive films earn more &mdash; but they are not better reviewed."),
    ("02", "The highest-rated genres are the least produced.",
     "Documentary and History top the ratings; Animation and Adventure dominate revenue. The two lists barely overlap."),
    ("03", "Sentiment is decoupled from box office.",
     f"Review sentiment correlates weakly with ratings (r = {corr_rat:.2f}) and almost not at all with revenue (r = {corr_rev:.2f})."),
    ("04", "Review language describes experience, not sales.",
     "Distinctive words separate good reviews from bad &mdash; but say little about what audiences pay to see."),
    ("05", "High-revenue actors do not cluster together.",
     "Top earners are scattered across every community in the collaboration network."),
    ("06", "Production volume and rating quality are inversely related.",
     "Smaller markets like Argentina and Sweden rate higher than the largest producers."),
]

for num, headline, detail in findings:
    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: baseline;
            gap: 1.6rem;
            padding: 1.2rem 0;
            border-bottom: 1px solid #E0DBD1;
        ">
            <div style="
                font-family: 'DM Serif Display', Georgia, serif;
                font-size: 1.8rem;
                color: #A02030;
                min-width: 2.6rem;
                line-height: 1;
            ">{num}</div>
            <div style="flex: 1;">
                <div style="
                    font-family: 'DM Serif Display', Georgia, serif;
                    font-size: 1.25rem;
                    color: #1A1A1A;
                    margin-bottom: 0.35rem;
                    line-height: 1.35;
                ">{headline}</div>
                <div style="
                    font-family: 'Source Serif 4', Georgia, serif;
                    font-size: 1rem;
                    color: #4A4A4A;
                    line-height: 1.55;
                ">{detail}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:4rem;'></div>", unsafe_allow_html=True)

# =========================================================
# CLOSING — hero block
# =========================================================
st.markdown(
    """
    <div style="
        margin: 2rem auto 3rem auto;
        max-width: 760px;
        text-align: center;
        font-family: 'DM Serif Display', Georgia, serif;
    ">
        <div style="
            color: #A02030;
            font-size: 1.05rem;
            letter-spacing: 0.85rem;
            margin-bottom: 1.6rem;
        ">★ ★ ★</div>
        <div style="
            font-style: italic;
            font-size: 1.55rem;
            line-height: 1.55;
            color: #2A2A2A;
        ">
            Commercial success and critical reception are not opposing forces.<br>
            They are simply different things &mdash; shaped by different audiences,<br>
            different incentives, and different definitions of what a film is for.
        </div>
        <div style="
            margin-top: 2rem;
            font-size: 1.15rem;
            color: #6E0F1A;
            font-style: italic;
        ">
            The film industry resists single-factor explanations &mdash;<br>
            and that, perhaps, is what makes it worth studying.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

chapter_footer(
    prev_label="Chapter 06 · Geo Analysis",
    prev_path="pages/6_Geo_Analysis.py",
    next_label="Back to Home",
    next_path="Home.py",
)
