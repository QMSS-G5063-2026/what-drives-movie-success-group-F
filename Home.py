import base64
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.style import apply_cinema_style  # noqa: E402

st.set_page_config(
    page_title="What Drives Movie Success?",
    layout="wide",
)

apply_cinema_style()


def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


@st.cache_data
def load_summary():
    movies = pd.read_csv("data/tmdb_5000_movies.csv")
    reviews = pd.read_csv("data/tmdb_reviews.csv")
    n_countries = len(set(
        c["name"]
        for g in movies["production_countries"]
        for c in json.loads(g)
    ))
    valid_count = int(((movies["budget"] > 0) & (movies["revenue"] > 0)).sum())
    return len(movies), valid_count, len(reviews), n_countries


n_movies, n_valid, n_reviews, n_countries = load_summary()
banner_base64 = get_base64_image("assets/banner.png")

st.markdown(
    f"""
    <style>
        .block-container {{ padding-top: 0rem !important; }}
        .home-hero {{
            width: 100vw;
            height: 440px;
            margin-left: calc(-50vw + 50%);
            margin-top: -4.5rem;
            margin-bottom: 2.0rem;
            background-image:
                linear-gradient(
                    to bottom,
                    rgba(0, 0, 0, 0.40) 0%,
                    rgba(0, 0, 0, 0.28) 44%,
                    rgba(245, 239, 229, 0.82) 82%,
                    rgba(245, 239, 229, 1) 100%
                ),
                url("data:image/png;base64,{banner_base64}");
            background-size: cover;
            background-position: center top;
            background-repeat: no-repeat;
            position: relative;
            overflow: hidden;
            font-family: Georgia, serif;
        }}
        .hero-content {{
            position: absolute;
            left: 4.6rem;
            top: 5.2rem;
            max-width: 780px;
        }}
        .hero-kicker {{
            color: #A61E2E;
            font-family: Arial, sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.28rem;
            text-transform: uppercase;
            margin-bottom: 1.4rem;
            text-shadow: 0 2px 10px rgba(0,0,0,0.75);
        }}
        .hero-title-overlay {{
            color: #F7F1E8;
            font-size: 3.9rem;
            line-height: 0.98;
            font-weight: 800;
            letter-spacing: -0.04rem;
            text-shadow: 0 4px 18px rgba(0,0,0,0.78);
            margin-bottom: 1.1rem;
        }}
        .hero-stars {{
            color: #A61E2E;
            font-size: 1.55rem;
            letter-spacing: 0.85rem;
            margin-bottom: 1.8rem;
            text-shadow: 0 2px 10px rgba(0,0,0,0.35);
        }}
        .hero-subtitle {{
            color: #242424;
            font-style: italic;
            font-size: 1.2rem;
            line-height: 1.55;
            max-width: 980px;
        }}
        .hero-authors {{
            color: #666666;
            font-family: Arial, sans-serif;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.22rem;
            text-transform: uppercase;
            margin-top: 1.3rem;
        }}
    </style>

    <div class="home-hero">
        <div class="hero-content">
            <div class="hero-kicker">A Data Visualization Project · Group F · Spring 2026</div>
            <div class="hero-title-overlay">What Drives<br>Movie Success?</div>
            <div class="hero-stars">★ ★ ★</div>
            <div class="hero-subtitle">
                Content, sentiment, and collaboration networks — a visual exploration of
                {n_movies:,} films, {n_reviews:,} audience reviews, and {n_countries} countries of production.
            </div>
            <div class="hero-authors">By Jiahui Lou · Ivy Li · Zihan Yang · Yixuan Huang</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
<p class="lead-paragraph">
We argue that movie success is not explained by one factor alone. Instead, it emerges from three layers: market features, audience response, and industry structure. To tell this story visually, we combine TMDB movie metadata, user reviews collected via the TMDB API, and cast data to uncover patterns across genres, time periods, and the film industry's social structure.
</p>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Movies", f"{n_movies:,}")
col2.metric("With Financial Data", f"{n_valid:,}")
col3.metric("User Reviews", f"{n_reviews:,}")
col4.metric("Countries", f"{n_countries}")

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("## Our Core Questions")
st.markdown("""
1. **Movie level** — How do budget, runtime, and release year relate to revenue and ratings?
2. **Genre level** — Which genres earn the most, and how have trends shifted over decades?
3. **Sentiment level** — Does review sentiment predict box office success?
4. **Text level** — What words distinguish glowing reviews from harsh ones?
5. **Network level** — Are well-connected actors in higher-grossing films?
6. **Geographic level** — How is movie production distributed globally?
""")

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("## Chapters")
st.markdown("")

pages_meta = [
    ("01", "pages/1_Movie_Overview.py", "Movie Overview",
     "How do budget, runtime, and release year relate to revenue and ratings?"),
    ("02", "pages/2_Genre_Analysis.py", "Genre Analysis",
     "Which genres perform best? How have genre trends shifted over time?"),
    ("03", "pages/3_Sentiment_Analysis.py", "Sentiment Analysis",
     "Does review sentiment predict box office success — or are they decoupled?"),
    ("04", "pages/4_Text_Analysis.py", "Text Analysis",
     "What words distinguish glowing reviews from harsh ones?"),
    ("05", "pages/5_Network_Analysis.py", "Network Analysis",
     "How are actors connected through collaborations, and does centrality matter?"),
    ("06", "pages/6_Geo_Analysis.py", "Geo Analysis",
     "How is movie production distributed around the world?"),
    ("07", "pages/7_Conclusions.py", "Conclusions",
     "What have we learned about what drives movie success?"),
]

for num, path, title, desc in pages_meta:
    col_n, col_main = st.columns([0.12, 0.88])
    with col_n:
        st.markdown(f'<div class="toc-number">{num}</div>',
                    unsafe_allow_html=True)
    with col_main:
        st.page_link(path, label=f"**{title}**")
        st.markdown(f'<div class="toc-chapter-desc">{desc}</div>',
                    unsafe_allow_html=True)
    st.markdown('<div style="height:1px;background:#E0DBD1;margin:1rem 0;"></div>',
                unsafe_allow_html=True)

st.markdown("")
st.caption("You can also use the sidebar to navigate between chapters.")

st.markdown("<hr>", unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("##### Data Sources")
    st.markdown("""
- [TMDB 5000 Movies & Credits](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) (Kaggle)
- [TMDB User Reviews](https://developer.themoviedb.org/reference/movie-reviews) (collected via API)
    """)

with col_b:
    st.markdown("##### Project")
    st.markdown("""
QMSS GR5063 Data Visualization · Columbia University · Spring 2026  
Jiahui Lou · Ivy Li · Zihan Yang · Yixuan Huang
    """)
