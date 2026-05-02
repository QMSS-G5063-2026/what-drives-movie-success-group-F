import json
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import pycountry
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data import load_movies  # noqa: E402
from utils.style import apply_editorial_style, chapter_cover, chapter_footer, COLORS  # noqa: E402

st.set_page_config(page_title="Geo Analysis", layout="wide")
apply_editorial_style()
alt.data_transformers.disable_max_rows()


@st.cache_data
def load_geo_data():
    movies = load_movies()

    all_rows = []
    for _, row in movies.iterrows():
        for c in json.loads(row['production_countries']):
            all_rows.append({
                'iso': c['iso_3166_1'],
                'country': c['name'],
                'movie_id': row['id'],
                'revenue': row['revenue'],
                'vote_average': row['vote_average'],
                'genre_list': row['genre_list'],
            })
    country_df = pd.DataFrame(all_rows)

    country_agg = country_df.groupby(['iso', 'country']).agg(
        movie_count=('movie_id', 'nunique'),
        avg_revenue=('revenue',
                     lambda x: x[x > 0].mean() if (x > 0).any() else 0),
        avg_rating=('vote_average', 'mean'),
    ).reset_index()

    genre_rows = country_df[['iso', 'genre_list']].explode('genre_list')
    genre_rows = genre_rows[genre_rows['genre_list'].notna()]
    top_genre_per_iso = (genre_rows.groupby(['iso', 'genre_list'])
                         .size().reset_index(name='n')
                         .sort_values(['iso', 'n'], ascending=[True, False])
                         .drop_duplicates('iso')
                         .rename(columns={'genre_list': 'top_genre'})
                         [['iso', 'top_genre']])
    country_agg = country_agg.merge(top_genre_per_iso, on='iso', how='left')
    country_agg['top_genre'] = country_agg['top_genre'].fillna('Unknown')
    country_agg['avg_revenue_m'] = country_agg['avg_revenue'] / 1e6

    def iso2_to_iso3(code):
        try:
            return pycountry.countries.get(alpha_2=code).alpha_3
        except Exception:
            return None

    def iso3_to_numeric(code):
        # world-atlas uses integer numeric ISO-3166-1 codes as the topojson 'id'
        try:
            return int(pycountry.countries.get(alpha_3=code).numeric)
        except Exception:
            return None

    country_agg['iso3'] = country_agg['iso'].apply(iso2_to_iso3)
    country_agg = country_agg.dropna(subset=['iso3'])
    country_agg['numeric_id'] = country_agg['iso3'].apply(iso3_to_numeric)
    country_agg = country_agg.dropna(subset=['numeric_id'])
    country_agg['numeric_id'] = country_agg['numeric_id'].astype(int)
    country_agg['log_movie_count'] = np.log10(country_agg['movie_count'])
    return country_agg


country_agg = load_geo_data()

chapter_cover(
    number="Chapter 06",
    title="Geographic Analysis",
    deck="How is movie production distributed around the world?"
)

# ---------- Metrics ----------
us_row = country_agg[country_agg['iso'] == 'US']
us_count = int(us_row['movie_count'].iloc[0]) if not us_row.empty else 0

col_s1, col_s2, col_s3 = st.columns(3)
col_s1.metric("Countries Represented", f"{len(country_agg):,}")
col_s2.metric("US Movies", f"{us_count:,}")
non_us = len(country_agg) - (1 if 'US' in country_agg['iso'].values else 0)
col_s3.metric("Non-US Countries", f"{non_us:,}")

st.markdown("")
st.info("This map should be read as the geographic footprint of the **TMDB 5000 dataset**, "
        "not as a complete census of global film production. Because the dataset is "
        "Hollywood-centered, the United States is heavily overrepresented.")

# ---------- Altair choropleth (no Folium, no external tile logos) ----------
st.markdown("### World Map")
st.markdown("Hover over any country to see its details. Switch the color metric to reveal "
            "different patterns. Movie counts are shown on a **log scale** because the US "
            "produces an order of magnitude more movies than any other country.")

map_metric = st.selectbox(
    "Color map by",
    ["Movie Count (log scale)", "Average Revenue ($M)", "Average Rating"]
)

# world-atlas TopoJSON — numeric ISO-3166-1 ids, no tile server dependency
WORLD_TOPO = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

if "Count" in map_metric:
    map_data = country_agg[
        ['numeric_id', 'country', 'log_movie_count', 'movie_count']
    ].copy()
    color_field = 'log_movie_count'
    color_enc = alt.Color(
        'log_movie_count:Q',
        title='Movie Count (log₁₀)',
        scale=alt.Scale(scheme='bluepurple', domainMin=0),
        legend=alt.Legend(gradientLength=220, gradientThickness=14,
                          labelFontSize=11, titleFontSize=12),
    )
    tooltip_fields = ['country', 'movie_count', 'log_movie_count']
    tooltip_specs = [
        alt.Tooltip('country:N', title='Country'),
        alt.Tooltip('movie_count:Q', title='Movies', format=','),
        alt.Tooltip('log_movie_count:Q', title='log₁₀(count)', format='.2f'),
    ]

elif "Revenue" in map_metric:
    map_data = (country_agg[country_agg['movie_count'] >= 5]
                [['numeric_id', 'country', 'avg_revenue_m', 'movie_count']].copy())
    color_field = 'avg_revenue_m'
    color_enc = alt.Color(
        'avg_revenue_m:Q',
        title='Avg Revenue ($M)',
        scale=alt.Scale(scheme='tealblues', domainMin=0),
        legend=alt.Legend(gradientLength=220, gradientThickness=14,
                          labelFontSize=11, titleFontSize=12),
    )
    tooltip_fields = ['country', 'avg_revenue_m', 'movie_count']
    tooltip_specs = [
        alt.Tooltip('country:N', title='Country'),
        alt.Tooltip('avg_revenue_m:Q', title='Avg Revenue ($M)', format='.1f'),
        alt.Tooltip('movie_count:Q', title='Movies', format=','),
    ]

else:
    map_data = (country_agg[country_agg['movie_count'] >= 5]
                [['numeric_id', 'country', 'avg_rating', 'movie_count']].copy())
    color_field = 'avg_rating'
    color_enc = alt.Color(
        'avg_rating:Q',
        title='Avg Rating',
        scale=alt.Scale(scheme='greens', domainMin=4, domainMax=8),
        legend=alt.Legend(gradientLength=220, gradientThickness=14,
                          labelFontSize=11, titleFontSize=12),
    )
    tooltip_fields = ['country', 'avg_rating', 'movie_count']
    tooltip_specs = [
        alt.Tooltip('country:N', title='Country'),
        alt.Tooltip('avg_rating:Q', title='Avg Rating', format='.2f'),
        alt.Tooltip('movie_count:Q', title='Movies', format=','),
    ]

# Base layer: all countries in muted cream (matches site background)
base = alt.Chart(
    alt.topo_feature(WORLD_TOPO, 'countries')
).mark_geoshape(
    fill='#E8E1D3',
    stroke='#C8BFB0',
    strokeWidth=0.4,
)

# Choropleth layer: join on numeric ISO id
choropleth = alt.Chart(
    alt.topo_feature(WORLD_TOPO, 'countries')
).mark_geoshape(
    stroke='#B8AFA0',
    strokeWidth=0.35,
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(
        data=map_data,
        key='numeric_id',
        fields=tooltip_fields,
    )
).encode(
    color=alt.condition(
        f'isValid(datum["{color_field}"])',
        color_enc,
        alt.value('#D4CBB8'),   # muted grey for no-data countries
    ),
    tooltip=tooltip_specs,
)

world_map = (
    (base + choropleth)
    .project('naturalEarth1')
    .properties(width='container', height=440)
    .configure_view(stroke=None)
)

st.altair_chart(world_map, use_container_width=True)

st.caption(
    "Countries in grey have no data (or fewer than 5 movies for Revenue/Rating views). "
    "Switch to **Average Revenue** to see New Zealand appear as the darkest country — "
    "a small number of large international productions (including the Lord of the Rings trilogy) "
    "push its average far above the US. "
    "Switch to **Average Rating** to see a reversal: high-production countries like the US, "
    "Canada, and Australia rate lower than smaller markets such as Sweden."
)

# ---------- Country rankings ----------
st.markdown("---")
st.markdown("### Country Rankings")
st.markdown("Hover over any bar to see the exact value.")

col1, col2 = st.columns(2)

with col1:
    top20 = country_agg.nlargest(20, 'movie_count')[
        ['country', 'movie_count']
    ].copy()
    chart1 = alt.Chart(top20).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X('movie_count:Q', title='Number of Movies'),
        y=alt.Y('country:N', sort='-x', title=None),
        color=alt.Color('movie_count:Q',
                        scale=alt.Scale(scheme='yelloworangered'),
                        legend=None),
        tooltip=[
            alt.Tooltip('country:N', title='Country'),
            alt.Tooltip('movie_count:Q', title='Movies'),
        ]
    ).properties(height=500, title='Top 20 Countries by Movie Count')
    st.altair_chart(chart1, use_container_width=True)

with col2:
    rev_df = (country_agg[country_agg['movie_count'] >= 5]
              .nlargest(15, 'avg_revenue_m')
              [['country', 'avg_revenue_m', 'movie_count']].copy())
    chart2 = alt.Chart(rev_df).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X('avg_revenue_m:Q', title='Average Revenue (Million $)'),
        y=alt.Y('country:N', sort='-x', title=None),
        color=alt.Color('avg_revenue_m:Q',
                        scale=alt.Scale(scheme='tealblues'),
                        legend=None),
        tooltip=[
            alt.Tooltip('country:N', title='Country'),
            alt.Tooltip('avg_revenue_m:Q', title='Avg Revenue ($M)',
                        format='.1f'),
            alt.Tooltip('movie_count:Q', title='Movies'),
        ]
    ).properties(height=500, title='Top 15 Countries by Avg Revenue (5+ movies)')
    st.altair_chart(chart2, use_container_width=True)

st.markdown("> The dataset is strongly **Hollywood-centered**: the US dominates movie volume. "
            "Average revenue should be interpreted cautiously because smaller countries can appear "
            "unusually strong when a few international blockbusters drive the average.")

# ---------- Genre by country ----------
st.markdown("---")
st.markdown("### Dominant Genre by Country")
st.markdown("Each bar represents a country, colored by its most common genre. "
            "Hover to see the country's movie count, top genre, and average revenue.")

top15 = country_agg.nlargest(15, 'movie_count')[
    ['country', 'movie_count', 'top_genre', 'avg_revenue_m']
].copy()
top15['avg_revenue_m'] = top15['avg_revenue_m'].round(1)

genre_palette = {
    'Drama': '#457B9D',
    'Action': '#E63946',
    'Comedy': '#2A9D8F',
    'Thriller': '#9b59b6',
    'Horror': '#e67e22',
    'Romance': '#f39c12',
    'Adventure': '#1abc9c',
    'Crime': '#34495e',
    'Animation': '#ff6b9d',
    'Documentary': '#6c757d',
}

present_genres = sorted(top15['top_genre'].unique().tolist())
domain = [g for g in genre_palette.keys() if g in present_genres]
domain += [g for g in present_genres if g not in domain]
range_ = [genre_palette.get(g, '#95a5a6') for g in domain]

chart3 = alt.Chart(top15).mark_bar(cornerRadiusEnd=4).encode(
    x=alt.X('movie_count:Q', title='Number of Movies'),
    y=alt.Y('country:N', sort='-x', title=None),
    color=alt.Color(
        'top_genre:N',
        title='Top Genre',
        scale=alt.Scale(domain=domain, range=range_)
    ),
    tooltip=[
        alt.Tooltip('country:N', title='Country'),
        alt.Tooltip('movie_count:Q', title='Movies'),
        alt.Tooltip('top_genre:N', title='Top Genre'),
        alt.Tooltip('avg_revenue_m:Q', title='Avg Revenue ($M)'),
    ]
).properties(height=450, title='Top 15 Producing Countries by Dominant Genre')

st.altair_chart(chart3, use_container_width=True)

st.markdown("")
st.markdown("**Full breakdown of top 15 producing countries:**")
table_display = top15.copy()
table_display.columns = ['Country', 'Movies', 'Top Genre', 'Avg Revenue ($M)']
st.dataframe(table_display, use_container_width=True, hide_index=True)

st.markdown(f"""
> **Key Findings:**
> - The US dominates with **{us_count:,}** movies, confirming that this dataset is Hollywood-centered rather than a balanced global sample.
> - **Drama** is the top genre in nearly every country among the top producing countries shown above, reflecting drama's global universality as a storytelling form.
> - Countries with fewer films can show unusually high average revenues because a small number of international co-productions can strongly affect the mean.
""")

chapter_footer(
    prev_label="Chapter 05 · Network Analysis",
    prev_path="pages/5_Network_Analysis.py",
    next_label="Chapter 07 · Conclusions",
    next_path="pages/7_Conclusions.py",
)
