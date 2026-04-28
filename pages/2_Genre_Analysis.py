import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data import load_movies  # noqa: E402
from utils.style import apply_editorial_style, chapter_cover, chapter_footer, COLORS  # noqa: E402

st.set_page_config(page_title="Genre Analysis", layout="wide")
apply_editorial_style()
alt.data_transformers.disable_max_rows()

movies = load_movies()
valid = movies[(movies['budget'] > 0) & (movies['revenue'] > 0)].copy()
exploded = valid.explode('genre_list')
exploded = exploded[exploded['genre_list'].notna()]

chapter_cover(
    number="Chapter 02",
    title="Genre Analysis",
    deck="Which genres perform best, and how have trends changed over time?"
)

# ---------- Sidebar ----------
st.sidebar.header("Settings")
metric = st.sidebar.radio("Compare genres by", ["Average Revenue", "Average Rating"])
top_n = st.sidebar.slider("Number of genres", 5, 20, 12)

# ---------- Genre comparison ----------
st.markdown("### Genre Performance")
st.markdown("This section separates **performance** from **popularity of production**. "
            "Left: genres ranked by your chosen success metric. Right: genres ranked by "
            "number of movies produced. Hover for exact values.")

col1, col2 = st.columns(2)

with col1:
    if metric == "Average Revenue":
        genre_agg = (exploded.groupby('genre_list')['revenue']
                     .mean().reset_index())
        genre_agg['value'] = genre_agg['revenue'] / 1e6
        ylabel = "Avg Revenue (Million $)"
        value_fmt = '.1f'
    else:
        genre_agg = (exploded.groupby('genre_list')['vote_average']
                     .mean().reset_index())
        genre_agg['value'] = genre_agg['vote_average']
        ylabel = "Avg Rating"
        value_fmt = '.2f'

    genre_agg = genre_agg.nlargest(top_n, 'value').copy()
    genre_agg['rank'] = range(1, len(genre_agg) + 1)

    chart = alt.Chart(genre_agg).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X('value:Q', title=ylabel),
        y=alt.Y('genre_list:N', sort='-x', title=None),
        color=alt.condition(
            alt.datum.rank == 1,
            alt.value(COLORS['primary']),
            alt.value(COLORS['blue'])
        ),
        tooltip=[
            alt.Tooltip('genre_list:N', title='Genre'),
            alt.Tooltip('value:Q', title=ylabel, format=value_fmt),
        ]
    ).properties(height=420, title=f'Top {top_n} Genres by {metric}')
    st.altair_chart(chart, use_container_width=True)

with col2:
    genre_counts = (movies.explode('genre_list')['genre_list']
                    .dropna().value_counts().head(top_n).reset_index())
    genre_counts.columns = ['genre', 'count']
    genre_counts['rank'] = range(1, len(genre_counts) + 1)

    chart2 = alt.Chart(genre_counts).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X('count:Q', title='Number of Movies'),
        y=alt.Y('genre:N', sort='-x', title=None),
        color=alt.condition(
            alt.datum.rank == 1,
            alt.value(COLORS['primary']),
            alt.value(COLORS['blue'])
        ),
        tooltip=[
            alt.Tooltip('genre:N', title='Genre'),
            alt.Tooltip('count:Q', title='Movies'),
        ]
    ).properties(height=420, title=f'Top {top_n} Genres by Count')
    st.altair_chart(chart2, use_container_width=True)

if metric == "Average Revenue":
    st.markdown("> **Animation** and **Adventure** lead in average revenue — these are "
                "typically big-budget, family-friendly blockbusters. **Drama**, though "
                "the most common genre, earns significantly less per film.")
else:
    st.markdown("> **Documentary** and **History** receive the highest average ratings. "
                "Interestingly, the highest-rated genres are rarely the highest-grossing. "
                "Compare the two charts side by side: the genres at the top of the rating list — "
                "Documentary, History, War, Western — barely appear in the count chart. "
                "The industry's most critically acclaimed genres are also its least produced.")

# ---------- Revenue vs Rating bubble ----------
st.markdown("---")
st.markdown("### Revenue vs Rating by Genre")
st.markdown("Each bubble is one genre. Size reflects the number of movies. "
            "Only the largest genres are labeled to reduce clutter — hover any bubble "
            "to see details.")

genre_both = exploded.groupby('genre_list').agg(
    avg_revenue=('revenue', 'mean'),
    avg_rating=('vote_average', 'mean'),
    count=('id', 'size')
).reset_index()
genre_both = genre_both[genre_both['count'] >= 20]
genre_both['avg_revenue_m'] = genre_both['avg_revenue'] / 1e6

label_threshold = genre_both.nlargest(10, 'count')

bubble = alt.Chart(genre_both).mark_circle(
    opacity=0.7, stroke='white', strokeWidth=0.5
).encode(
    x=alt.X('avg_revenue_m:Q', title='Average Revenue (Million $)'),
    y=alt.Y('avg_rating:Q', title='Average Rating',
            scale=alt.Scale(zero=False)),
    size=alt.Size('count:Q', title='Number of Movies',
                  scale=alt.Scale(range=[100, 2000])),
    color=alt.value(COLORS['blue']),
    tooltip=[
        alt.Tooltip('genre_list:N', title='Genre'),
        alt.Tooltip('avg_revenue_m:Q', title='Avg Revenue ($M)', format='.0f'),
        alt.Tooltip('avg_rating:Q', title='Avg Rating', format='.2f'),
        alt.Tooltip('count:Q', title='Movies'),
    ]
)

text = alt.Chart(label_threshold).mark_text(
    dy=-14, fontSize=11, fontWeight='bold'
).encode(
    x='avg_revenue_m:Q', y='avg_rating:Q', text='genre_list:N'
)

st.altair_chart((bubble + text).properties(height=470),
                use_container_width=True)

st.markdown("> The **top-right corner** (high revenue + high rating) is nearly empty. "
            "This is one of the clearest findings in the project: genres that earn the most are rarely the ones with the best reviews — "
            "commercial and critical success operate on different axes. "
            "**Hover the unlabeled bubbles in the upper-left** to find Documentary and History — "
            "the genres that rate highest but produce the fewest films.")

# ---------- Genre trends over time ----------
st.markdown("---")
st.markdown("### Genre Trends Over Time")
st.markdown("**Click a genre in the legend** to highlight just that line. "
            "Click again to restore all.")

all_genres = sorted(exploded['genre_list'].dropna().unique())
default_selection = ['Drama', 'Comedy', 'Action', 'Thriller', 'Romance']
default_selection = [g for g in default_selection if g in all_genres]

selected = st.multiselect(
    "Select genres to compare",
    all_genres,
    default=default_selection
)

if len(selected) > 8:
    st.warning("Showing more than 8 genres at once can make the chart hard to read. "
               "Consider selecting fewer.")

if selected:
    trend_data = movies[movies['year'].between(1980, 2016)].copy()
    trend_exploded = trend_data.explode('genre_list')
    trend_exploded = trend_exploded[trend_exploded['genre_list'].isin(selected)].copy()
    trend_exploded['period'] = (trend_exploded['year'] // 5 * 5).astype('Int64')
    trend_agg = (trend_exploded.dropna(subset=['period'])
                 .groupby(['period', 'genre_list']).size()
                 .reset_index(name='count'))
    trend_agg['period'] = trend_agg['period'].astype(int)

    legend_selection = alt.selection_point(fields=['genre_list'], bind='legend')

    line_chart = alt.Chart(trend_agg).mark_line(
        point=True, strokeWidth=2.5
    ).encode(
        x=alt.X('period:O', title='5-Year Period'),
        y=alt.Y('count:Q', title='Number of Movies'),
        color=alt.Color('genre_list:N', title='Genre'),
        opacity=alt.condition(legend_selection, alt.value(1), alt.value(0.15)),
        tooltip=[
            alt.Tooltip('genre_list:N', title='Genre'),
            alt.Tooltip('period:O', title='Period'),
            alt.Tooltip('count:Q', title='Movies'),
        ]
    ).add_params(legend_selection).properties(height=420)

    st.altair_chart(line_chart, use_container_width=True)

    if selected == default_selection:
        st.markdown("> **Drama** has been dominant throughout, but **Action** and **Thriller** "
                    "have grown rapidly since the 1990s — the era of Hollywood franchises. "
                    "**Romance** has stayed roughly flat.")
    else:
        st.markdown("> Use the genre selector to compare how different genres rise, fall, "
                    "or stay stable over time.")
else:
    st.info("Select at least one genre above to see trends.")

chapter_footer(
    prev_label="Chapter 01 · Movie Overview",
    prev_path="pages/1_Movie_Overview.py",
    next_label="Chapter 03 · Sentiment Analysis",
    next_path="pages/3_Sentiment_Analysis.py",
)
