import streamlit as st
import pandas as pd
import json

st.set_page_config(
    page_title="What Drives Movie Success?",
    page_icon="🎬",
    layout="wide"
)

# ---- Load data (cached) ----
@st.cache_data
def load_data():
    movies = pd.read_csv("data/tmdb_5000_movies.csv")
    credits = pd.read_csv("data/tmdb_5000_credits.csv")
    reviews = pd.read_csv("data/tmdb_reviews.csv")
    movies['genre_list'] = movies['genres'].apply(lambda g: [x['name'] for x in json.loads(g)])
    movies['release_date'] = pd.to_datetime(movies['release_date'], errors='coerce')
    movies['year'] = movies['release_date'].dt.year
    return movies, credits, reviews

movies, credits, reviews = load_data()
valid = movies[(movies['budget'] > 0) & (movies['revenue'] > 0)]

# ---- Title ----
st.title("🎬 What Drives Movie Success?")
st.markdown("### Content, Sentiment, and Collaboration Networks")
st.markdown("---")

# ---- Introduction ----
st.markdown("""
We explore what drives movie success by combining content features, audience sentiment, 
and collaboration structures in the film industry. Using TMDB movie metadata, user reviews 
collected via the TMDB API, and cast/crew data, we analyze patterns across multiple dimensions.
""")

# ---- Key stats ----
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Movies", f"{len(movies):,}")
col2.metric("With Financial Data", f"{len(valid):,}")
col3.metric("User Reviews", f"{len(reviews):,}")
col4.metric("Countries", f"{len(set(c['name'] for g in movies['production_countries'] for c in json.loads(g)))}")

st.markdown("---")

# ---- Navigation guide ----
st.markdown("### Explore the Data")
st.markdown("""
Use the sidebar to navigate through different analyses:

- **Movie Overview** — How do budget, runtime, and release year relate to revenue and ratings?
- **Genre Analysis** — Which genres perform best, and how have trends changed over time?
- **Sentiment Analysis** — Do review sentiments predict box office success?
- **Text Analysis** — What language distinguishes high-rated from low-rated reviews?
- **Network Analysis** — How are actors connected, and does centrality relate to performance?
- **Geo Analysis** — How is movie production distributed around the world?
""")

# ---- Data sources ----
st.markdown("---")
st.markdown("### Data Sources")
st.markdown("""
- **TMDB 5000 Movies & Credits** — [Kaggle](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata)
- **TMDB User Reviews** — Collected via [TMDB API](https://developer.themoviedb.org/reference/movie-reviews)
""")

st.markdown("---")
st.caption("QMSS GR5063 Data Visualization — Group I — Spring 2026")
