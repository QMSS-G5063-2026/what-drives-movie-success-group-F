import sys
from collections import Counter
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data import load_movies, load_reviews_with_sentiment, load_reviews_with_tokens  # noqa: E402
from utils.style import apply_editorial_style, chapter_cover, chapter_footer, COLORS  # noqa: E402

st.set_page_config(page_title="Text Analysis", layout="wide")
apply_editorial_style()
alt.data_transformers.disable_max_rows()

movies = load_movies()
reviews = load_reviews_with_tokens()

chapter_cover(
    number="Chapter 04",
    title="Text Analysis",
    deck="What words distinguish glowing reviews from harsh ones?"
)

st.markdown("This page moves from a **comparative** view of language to a more exploratory view. The goal is to explain what sits behind the sentiment patterns from the previous chapter. ")

# ---------- Distinctive words ----------
st.markdown("### Distinctive Words: High vs Low Rated")
st.markdown(
    "Which words appear **disproportionately more often** in positive or negative reviews? "
    "We compute a distinctiveness score for each word — the difference in how often "
    "it appears in high-rated vs low-rated reviews, normalized to the range **−1 to +1**. "
    "Scores near **+1** mean the word is strongly associated with praise; "
    "scores near **−1** mean it is strongly associated with criticism. "
    "**Hover over any bar** to see the exact score and how many times the word appears."
)

high = reviews[reviews['rating'] >= 8]
low = reviews[reviews['rating'] <= 4]
high_words = Counter(w for ws in high['tokens'] for w in ws)
low_words = Counter(w for ws in low['tokens'] for w in ws)
high_total = sum(high_words.values())
low_total = sum(low_words.values())

distinct = []
candidates = set([w for w, _ in high_words.most_common(2000)] + [w for w, _ in low_words.most_common(2000)])
for w in candidates:
    h, l = high_words.get(w, 0), low_words.get(w, 0)
    if h + l < 100:
        continue
    h_rate = h / high_total if high_total else 0
    l_rate = l / low_total if low_total else 0
    if h_rate + l_rate == 0:
        continue
    score = (h_rate - l_rate) / (h_rate + l_rate)
    distinct.append({
        'word': w,
        'score': score,
        'high_count': h,
        'low_count': l,
        'total_count': h + l,
    })

distinct.sort(key=lambda x: x['score'])

col1, col2 = st.columns(2)

with col1:
    top_high_df = pd.DataFrame(distinct[-15:])
    chart_high = alt.Chart(top_high_df).mark_bar(
        cornerRadiusEnd=4, color=COLORS['green']
    ).encode(
        x=alt.X('score:Q', title='Distinctiveness Score',
                scale=alt.Scale(domain=[0, 1])),
        y=alt.Y('word:N', sort='-x', title=None),
        tooltip=[
            alt.Tooltip('word:N', title='Word'),
            alt.Tooltip('score:Q', title='Distinctiveness', format='.3f'),
            alt.Tooltip('high_count:Q', title='In High-Rated'),
            alt.Tooltip('low_count:Q', title='In Low-Rated'),
            alt.Tooltip('total_count:Q', title='Total Occurrences'),
        ]
    ).properties(
        height=440, title='Distinctive in High-Rated Reviews (≥8)'
    )
    st.altair_chart(chart_high, use_container_width=True)

with col2:
    top_low_df = pd.DataFrame(distinct[:15])
    top_low_df['abs_score'] = -top_low_df['score']
    chart_low = alt.Chart(top_low_df).mark_bar(
        cornerRadiusEnd=4, color=COLORS['primary']
    ).encode(
        x=alt.X('abs_score:Q', title='Distinctiveness Score (|negative|)',
                scale=alt.Scale(domain=[0, 1])),
        y=alt.Y('word:N', sort='-x', title=None),
        tooltip=[
            alt.Tooltip('word:N', title='Word'),
            alt.Tooltip('score:Q', title='Distinctiveness', format='.3f'),
            alt.Tooltip('high_count:Q', title='In High-Rated'),
            alt.Tooltip('low_count:Q', title='In Low-Rated'),
            alt.Tooltip('total_count:Q', title='Total Occurrences'),
        ]
    ).properties(
        height=440, title='Distinctive in Low-Rated Reviews (≤4)'
    )
    st.altair_chart(chart_low, use_container_width=True)

st.markdown("> Positive reviews tend to use broad praise and emotional language, "
            "while negative reviews focus on **boredom**, **poor quality**, and specific complaints such as script or CGI.")

# ---------- Review length vs rating ----------
st.markdown("---")
st.markdown("### Do Longer Reviews Signal Stronger Opinions?")
st.markdown(
    "Does the length of a review tell us anything about how the reviewer felt? "
    "Each box shows the distribution of review word counts at each rating level. "
    "Hover over any box to see the median and spread."
)

reviews_len = reviews.copy()
reviews_len = reviews_len[reviews_len['rating'].notna()].copy()
reviews_len['word_count'] = reviews_len['tokens'].apply(len)
reviews_len['rating_int'] = reviews_len['rating'].astype(int)
reviews_len = reviews_len[reviews_len['word_count'] <= reviews_len['word_count'].quantile(0.97)]

box = alt.Chart(reviews_len).mark_boxplot(
    extent='min-max', size=28,
    median={'color': COLORS['primary'], 'strokeWidth': 2},
    box={'color': COLORS['blue'], 'opacity': 0.7},
    outliers={'opacity': 0},
).encode(
    x=alt.X('rating_int:O', title='User Rating'),
    y=alt.Y('word_count:Q', title='Review Length (words)',
            scale=alt.Scale(zero=False)),
    tooltip=[
        alt.Tooltip('rating_int:O', title='Rating'),
        alt.Tooltip('median(word_count):Q', title='Median words', format='.0f'),
    ]
).properties(height=380)

st.altair_chart(box, use_container_width=True)

st.markdown(
    "> Review length varies with rating — hover over the boxes to read the median word count "
    "at each level. The pattern suggests that viewers with strong opinions (highly positive "
    "or deeply disappointed) tend to write differently from those in the middle, "
    "but the direction and size of that difference is best read directly from the chart."
)

# ---------- Top movies sentiment ----------
st.markdown("---")
st.markdown("### How Do Well-Known Films Get Reviewed?")
st.markdown(
    "Among the 25 most-reviewed films in this dataset, how does average review sentiment "
    "compare to their TMDB rating? If sentiment and rating were perfectly aligned, "
    "all dots would fall along a diagonal. Hover to see each film's details."
)

@st.cache_data
def top_movies_sentiment(_reviews_s, _movies_df):
    movie_agg = _reviews_s.groupby('movie_id').agg(
        n_reviews=('content', 'count'),
        avg_sentiment=('sentiment', 'mean'),
    ).reset_index()
    merged_m = _movies_df[['id', 'title', 'vote_average', 'revenue']].merge(
        movie_agg, left_on='id', right_on='movie_id', how='inner'
    )
    top = merged_m.nlargest(25, 'n_reviews').copy()
    top['revenue_m'] = top['revenue'] / 1e6
    return top

reviews_sent = load_reviews_with_sentiment()
top_df = top_movies_sentiment(reviews_sent, movies)

scatter_top = alt.Chart(top_df).mark_circle(opacity=0.85).encode(
    x=alt.X('vote_average:Q', title='TMDB Rating',
            scale=alt.Scale(zero=False)),
    y=alt.Y('avg_sentiment:Q', title='Average Review Sentiment',
            scale=alt.Scale(zero=False)),
    size=alt.Size('n_reviews:Q', title='Number of Reviews',
                  scale=alt.Scale(range=[80, 600])),
    color=alt.Color('revenue_m:Q', title='Revenue ($M)',
                    scale=alt.Scale(scheme='tealblues'),
                    legend=alt.Legend(gradientLength=120)),
    tooltip=[
        alt.Tooltip('title:N', title='Movie'),
        alt.Tooltip('vote_average:Q', title='Rating', format='.1f'),
        alt.Tooltip('avg_sentiment:Q', title='Avg Sentiment', format='.2f'),
        alt.Tooltip('n_reviews:Q', title='Reviews'),
        alt.Tooltip('revenue_m:Q', title='Revenue ($M)', format='.0f'),
    ]
).interactive()

text_top = alt.Chart(top_df).mark_text(
    dy=-12, fontSize=10, fontWeight='bold'
).encode(
    x='vote_average:Q',
    y='avg_sentiment:Q',
    text='title:N',
)

st.altair_chart(
    (scatter_top + text_top).properties(height=480),
    use_container_width=True
)

st.markdown(
    "> Even among the most-reviewed films, sentiment and rating do not move in lockstep. "
    "Some high-revenue blockbusters attract positive sentiment despite middling ratings; "
    "others rate well but generate more measured review language. "
    "This reinforces the Chapter 03 finding: sentiment and rating capture different things."
)





chapter_footer(
    prev_label="Chapter 03 · Sentiment Analysis",
    prev_path="pages/3_Sentiment_Analysis.py",
    next_label="Chapter 05 · Network Analysis",
    next_path="pages/5_Network_Analysis.py",
)
