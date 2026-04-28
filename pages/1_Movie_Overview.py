import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data import load_movies  # noqa: E402
from utils.style import apply_editorial_style, chapter_cover, chapter_footer, COLORS  # noqa: E402

st.set_page_config(page_title="Movie Overview", layout="wide")
apply_editorial_style()
alt.data_transformers.disable_max_rows()

movies = load_movies()

chapter_cover(
    number="Chapter 01",
    title="Movie Overview",
    deck="How do budget, runtime, and release year relate to movie success?"
)
st.markdown(
    "Before we examine genres, audience reactions, or the social network of actors, "
    "we begin with the most basic ingredients of a film: how much it costs, how long it runs, "
    "and when it was released. This first chapter sets the baseline against which every later "
    "finding will be compared."
)


# ---------- Sidebar ----------
st.sidebar.header("Filters")

all_genres = sorted(set(g for gl in movies['genre_list'] for g in gl))
selected_genres = st.sidebar.multiselect("Genres", all_genres, default=all_genres)

year_min_valid = int(movies['year'].dropna().min())
year_max_valid = int(movies['year'].dropna().max())
year_range = st.sidebar.slider(
    "Year Range", year_min_valid, year_max_valid,
    (max(1990, year_min_valid), year_max_valid)
)
budget_filter = st.sidebar.checkbox("Only movies with budget & revenue data", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Budget vs Revenue chart**")
profit_highlight = st.sidebar.radio(
    "Highlight",
    ["All movies", "Profitable (made money)", "Lost money"],
    help="Profitable = revenue > budget. Below the diagonal = lost money."
)

filtered = movies[
    (movies['genre_list'].apply(lambda x: any(g in x for g in selected_genres))) &
    (movies['year'].between(year_range[0], year_range[1]))
].copy()
if budget_filter:
    filtered = filtered[(filtered['budget'] > 0) & (filtered['revenue'] > 0)]

st.info(f"Showing **{len(filtered):,}** movies matching your filters")

# ---------- Budget vs Revenue ----------
st.markdown("### Budget vs Revenue")
st.markdown("Each dot is a movie. Points above the dashed diagonal made money; "
            "points below lost money. Both axes use a **log scale** so blockbusters "
            "do not compress the rest of the dataset. Color indicates rating. "
            "Hover to see titles — scroll to zoom, drag to pan.")

chart_data = filtered[['title', 'budget', 'revenue', 'vote_average', 'year']].copy()
chart_data['budget_m'] = chart_data['budget'] / 1e6
chart_data['revenue_m'] = chart_data['revenue'] / 1e6
chart_data = chart_data.replace([np.inf, -np.inf], np.nan).dropna(
    subset=['budget_m', 'revenue_m']
)
chart_data = chart_data[(chart_data['budget_m'] > 0) & (chart_data['revenue_m'] > 0)].copy()
chart_data['profitable'] = chart_data['revenue_m'] > chart_data['budget_m']


if chart_data.empty:
    st.warning("No valid budget/revenue records after filtering. "
               "Widen the year or genre filters to see data.")
else:
    min_val = float(max(0.1, min(chart_data['budget_m'].min(), chart_data['revenue_m'].min())))
    max_val = float(max(chart_data['budget_m'].max(), chart_data['revenue_m'].max()))
    line_df = pd.DataFrame({'x': [min_val, max_val], 'y': [min_val, max_val]})
    diagonal = alt.Chart(line_df).mark_line(
        strokeDash=[5, 5], color='grey', opacity=0.5
    ).encode(x='x:Q', y='y:Q')

    if profit_highlight == "All movies":
        scatter = alt.Chart(chart_data).mark_circle(opacity=0.6).encode(
            x=alt.X('budget_m:Q', title='Budget (Million $, log scale)',
                    scale=alt.Scale(type='log')),
            y=alt.Y('revenue_m:Q', title='Revenue (Million $, log scale)',
                    scale=alt.Scale(type='log')),
            color=alt.Color('vote_average:Q',
                            scale=alt.Scale(domain=[2, 9],
                                            range=['#D4A5A5', '#8B3545', '#2C3E50']),
                            legend=alt.Legend(title='Rating',
                                              gradientLength=200,
                                              gradientThickness=14,
                                              labelFontSize=11,
                                              titleFontSize=12),
                            title='Rating'),
            size=alt.value(45),
            tooltip=[
                alt.Tooltip('title:N', title='Movie'),
                alt.Tooltip('budget_m:Q', title='Budget ($M)', format='.1f'),
                alt.Tooltip('revenue_m:Q', title='Revenue ($M)', format='.1f'),
                alt.Tooltip('vote_average:Q', title='Rating', format='.1f'),
                alt.Tooltip('year:O', title='Year'),
            ]
        ).interactive()
    else:
        # Profitable highlight: profitable=True keeps rating color, others muted
        target_profitable = (profit_highlight == "Profitable (made money)")
        chart_data['highlight'] = chart_data['profitable'] == target_profitable

        bg = alt.Chart(chart_data[~chart_data['highlight']]).mark_circle(
            opacity=0.18, color='#BFB8AC', size=35
        ).encode(
            x=alt.X('budget_m:Q', title='Budget (Million $, log scale)',
                    scale=alt.Scale(type='log')),
            y=alt.Y('revenue_m:Q', title='Revenue (Million $, log scale)',
                    scale=alt.Scale(type='log')),
            tooltip=[
                alt.Tooltip('title:N', title='Movie'),
                alt.Tooltip('budget_m:Q', title='Budget ($M)', format='.1f'),
                alt.Tooltip('revenue_m:Q', title='Revenue ($M)', format='.1f'),
                alt.Tooltip('vote_average:Q', title='Rating', format='.1f'),
            ]
        )

        fg = alt.Chart(chart_data[chart_data['highlight']]).mark_circle(opacity=0.75).encode(
            x=alt.X('budget_m:Q'),
            y=alt.Y('revenue_m:Q'),
            color=alt.Color('vote_average:Q',
                            scale=alt.Scale(domain=[2, 9],
                                            range=['#D4A5A5', '#8B3545', '#2C3E50']),
                            legend=alt.Legend(title='Rating',
                                              gradientLength=200,
                                              gradientThickness=14,
                                              labelFontSize=11,
                                              titleFontSize=12),
                            title='Rating'),
            size=alt.value(55),
            tooltip=[
                alt.Tooltip('title:N', title='Movie'),
                alt.Tooltip('budget_m:Q', title='Budget ($M)', format='.1f'),
                alt.Tooltip('revenue_m:Q', title='Revenue ($M)', format='.1f'),
                alt.Tooltip('vote_average:Q', title='Rating', format='.1f'),
                alt.Tooltip('year:O', title='Year'),
            ]
        )

        scatter = (bg + fg).resolve_scale(color='shared').interactive()

    st.altair_chart((diagonal + scatter).properties(height=450),
                    use_container_width=True)

if profit_highlight == "All movies":
    st.markdown("> Higher budgets generally yield higher revenues, but the spread is wide. "
                "Rating (color) is largely independent of budget — an expensive film is "
                "not necessarily well-reviewed. This gives the project its main premise: "
                "commercial success and audience evaluation need to be examined separately.")
elif profit_highlight == "Profitable (made money)":
    n_profit = int(chart_data['profitable'].sum())
    n_total = len(chart_data)
    pct = (n_profit / n_total * 100) if n_total else 0
    st.markdown(f"> **{n_profit:,} of {n_total:,} films** in this view turned a profit "
                f"(**{pct:.0f}%**). Notice that profitable films span the full range of "
                f"ratings — a higher-rated dot and a lower-rated dot "
                f"can both make money. **Profit is not a proxy for quality.**")
else:
    n_loss = int((~chart_data['profitable']).sum())
    n_total = len(chart_data)
    pct = (n_loss / n_total * 100) if n_total else 0
    st.markdown(f"> **{n_loss:,} of {n_total:,} films** in this view lost money "
                f"(**{pct:.0f}%**). Critically, some well-reviewed films still fall below "
                f"the break-even line. A high rating does not guarantee a return "
                f"on investment — another reminder that critical and commercial success "
                f"are independent dimensions.")

# ---------- Runtime ----------
st.markdown("---")
st.markdown("### Runtime and Success")
st.markdown("Does a movie's length affect how much it earns or how it is rated?")

v = filtered[(filtered['runtime'] > 30) & (filtered['runtime'] < 250) & (filtered['revenue'] > 0)].copy()
v['revenue_m'] = v['revenue'] / 1e6

col1, col2 = st.columns(2)
with col1:
    c1 = alt.Chart(v).mark_circle(opacity=0.45, color=COLORS['blue']).encode(
        x=alt.X('runtime:Q', title='Runtime (minutes)'),
        y=alt.Y('revenue_m:Q', title='Revenue (Million $, log scale)',
                scale=alt.Scale(type='log')),
        tooltip=[
            alt.Tooltip('title:N', title='Movie'),
            alt.Tooltip('runtime:Q', title='Runtime (min)'),
            alt.Tooltip('revenue_m:Q', title='Revenue ($M)', format='.1f'),
        ],
        size=alt.value(30)
    ).interactive().properties(height=350, title='Runtime vs Revenue')
    st.altair_chart(c1, use_container_width=True)

with col2:
    c2 = alt.Chart(v).mark_circle(opacity=0.45, color=COLORS['primary']).encode(
        x=alt.X('runtime:Q', title='Runtime (minutes)'),
        y=alt.Y('vote_average:Q', title='TMDB Rating',
                scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip('title:N', title='Movie'),
            alt.Tooltip('runtime:Q', title='Runtime (min)'),
            alt.Tooltip('vote_average:Q', title='Rating', format='.1f'),
        ],
        size=alt.value(30)
    ).interactive().properties(height=350, title='Runtime vs Rating')
    st.altair_chart(c2, use_container_width=True)

st.markdown("> The **90–150 minute** range covers the widest revenue spread, but runtime itself is not a strong predictor of revenue. "
            "Longer films receive slightly higher ratings on average, "
            "possibly reflecting prestige productions rather than length alone.")

# ---------- Rating distribution ----------
st.markdown("---")
st.markdown("### Rating Distribution")
st.markdown("How are ratings distributed across all movies? "
            "The dashed line marks the mean.")

ratings = filtered[filtered['vote_average'] > 0].copy()
mean_r = ratings['vote_average'].mean()

col3, col4 = st.columns([3, 1])
with col3:
    hist = alt.Chart(ratings).mark_bar(color=COLORS['blue'], opacity=0.85).encode(
        x=alt.X('vote_average:Q', bin=alt.Bin(maxbins=30),
                title='Vote Average'),
        y=alt.Y('count():Q', title='Number of Movies'),
        tooltip=[
            alt.Tooltip('vote_average:Q', bin=alt.Bin(maxbins=30),
                        title='Rating Bin'),
            alt.Tooltip('count():Q', title='Movies'),
        ]
    )
    rule = alt.Chart(pd.DataFrame({'x': [mean_r]})).mark_rule(
        color=COLORS['primary'], strokeDash=[5, 3], strokeWidth=2
    ).encode(x='x:Q')
    st.altair_chart((hist + rule).properties(height=320),
                    use_container_width=True)

with col4:
    st.markdown("")
    st.metric("Mean", f"{mean_r:.1f}")
    st.metric("Median", f"{ratings['vote_average'].median():.1f}")
    st.metric("Std Dev", f"{ratings['vote_average'].std():.1f}")

st.markdown("> Ratings cluster tightly around the middle of the scale, with most movies landing near the mean rather than at the extremes. "
            "This makes rating a more compressed measure than revenue, which varies across several orders of magnitude.")

# ---------- Time series ----------
st.markdown("---")
st.markdown("### Trends Over Time")
st.markdown("Movie production volume (bars) and average revenue per movie (line) "
            "by release year.")

yearly = (filtered.dropna(subset=['year'])
          .groupby('year')
          .agg(count=('id', 'size'),
               avg_revenue=('revenue',
                            lambda x: x[x > 0].mean() if (x > 0).any() else np.nan))
          .reset_index())
yearly['year'] = yearly['year'].astype(int)
yearly['avg_revenue_m'] = yearly['avg_revenue'] / 1e6

if not yearly.empty:
    years_sorted = sorted(yearly['year'].unique().tolist())
    tick_years = years_sorted[::max(1, len(years_sorted) // 15)]

    bars = alt.Chart(yearly).mark_bar(color=COLORS['blue'], opacity=0.35).encode(
        x=alt.X('year:O', title='Year',
                axis=alt.Axis(labelAngle=-45, values=tick_years)),
        y=alt.Y('count:Q', title='Number of Movies'),
        tooltip=[
            alt.Tooltip('year:O', title='Year'),
            alt.Tooltip('count:Q', title='Movies'),
        ]
    )

    line = alt.Chart(yearly.dropna(subset=['avg_revenue_m'])).mark_line(
        color=COLORS['primary'], strokeWidth=2.5, point=True
    ).encode(
        x=alt.X('year:O'),
        y=alt.Y('avg_revenue_m:Q', title='Average Revenue (Million $)'),
        tooltip=[
            alt.Tooltip('year:O', title='Year'),
            alt.Tooltip('avg_revenue_m:Q', title='Avg Revenue ($M)', format='.1f'),
        ]
    )

    combined = alt.layer(bars, line).resolve_scale(y='independent').properties(
        height=400
    )
    st.altair_chart(combined, use_container_width=True)

    st.markdown("> Production has grown steadily since the 1990s, and average revenue "
                "per film trends upward — driven by the rise of franchise blockbusters.")
else:
    st.warning("No yearly data to display.")

chapter_footer(
    prev_label="Home",
    prev_path="Home.py",
    next_label="Chapter 02 · Genre Analysis",
    next_path="pages/2_Genre_Analysis.py",
)
