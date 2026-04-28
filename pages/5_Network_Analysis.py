import json
import sys
import tempfile
from collections import Counter
from itertools import combinations
from pathlib import Path

import altair as alt
import community.community_louvain as community_louvain
import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data import load_movies, load_credits  # noqa: E402
from utils.style import apply_editorial_style, chapter_cover, chapter_footer, COLORS  # noqa: E402

st.set_page_config(page_title="Network Analysis", layout="wide")
apply_editorial_style()
alt.data_transformers.disable_max_rows()


COMMUNITY_PALETTE = [
    "#457B9D", "#E63946", "#2A9D8F", "#F4A261", "#9B5DE5",
    "#F15BB5", "#FEE440", "#00BBF9", "#00F5D4", "#1D3557",
]


@st.cache_data
def build_network():
    movies = load_movies()
    credits = load_credits()
    valid = movies[(movies['budget'] > 0) & (movies['revenue'] > 0)]
    id_to_rev = dict(zip(valid['id'], valid['revenue']))

    edges = Counter()
    actor_movies = {}
    actor_revenue = {}

    for _, row in credits.iterrows():
        cast = json.loads(row['cast'])
        top_actors = [a['name'] for a in cast[:5]]
        mid = row['movie_id']
        rev = id_to_rev.get(mid)
        for a in top_actors:
            actor_movies[a] = actor_movies.get(a, 0) + 1
            if rev:
                actor_revenue.setdefault(a, []).append(rev)
        for pair in combinations(top_actors, 2):
            edges[tuple(sorted(pair))] += 1

    frequent = {a for a, c in actor_movies.items() if c >= 5}
    G = nx.Graph()
    for (a1, a2), w in edges.items():
        if a1 in frequent and a2 in frequent:
            G.add_edge(a1, a2, weight=w)
    G.remove_nodes_from(list(nx.isolates(G)))

    partition = community_louvain.best_partition(G, random_state=42)
    degree = dict(G.degree())
    centrality = nx.degree_centrality(G)
    actor_avg_rev = {
        a: float(np.mean(revs))
        for a, revs in actor_revenue.items()
        if a in G.nodes()
    }
    return G, partition, degree, centrality, actor_movies, actor_avg_rev


def build_pyvis_html(subG, partition, degree, actor_movies, actor_avg_rev, highlight_top_revenue=True):
    net = Network(
        height="620px", width="100%",
        bgcolor="#ffffff", font_color="#222222",
        notebook=False, cdn_resources='in_line',
    )

    net.barnes_hut(
        gravity=-8000,
        central_gravity=0.3,
        spring_length=200,
        spring_strength=0.02,
        damping=0.5,
    )

    visible_revenues = [actor_avg_rev.get(n, 0) for n in subG.nodes() if actor_avg_rev.get(n, 0) > 0]
    revenue_cutoff = float(np.quantile(visible_revenues, 0.8)) if visible_revenues else float("inf")

    for node in subG.nodes():
        comm_id = partition.get(node, 0)
        color = COMMUNITY_PALETTE[comm_id % len(COMMUNITY_PALETTE)]
        deg = degree.get(node, 1)
        n_movies = actor_movies.get(node, 0)
        avg_rev_m = actor_avg_rev.get(node, 0) / 1e6

        is_high_revenue = actor_avg_rev.get(node, 0) >= revenue_cutoff
        node_fill = "#F4C430" if (highlight_top_revenue and is_high_revenue) else color
        node_border = "#A61E2E" if (highlight_top_revenue and is_high_revenue) else color
        border_width = 4 if (highlight_top_revenue and is_high_revenue) else 1

        title = (
            f"{node}\n"
            f"Collaborators: {deg}\n"
            f"Movies: {n_movies}\n"
            f"Avg Revenue: ${avg_rev_m:.1f}M\n"
            f"Community: {comm_id}\n"
            f"Top 20% revenue actor: {'Yes' if is_high_revenue else 'No'}"
        )

        net.add_node(
            node,
            label=node if deg >= 15 or is_high_revenue else "",
            title=title,
            color={"background": node_fill, "border": node_border},
            size=max(12, min(50, deg * 0.9)),
            borderWidth=border_width,
            font={'size': 14, 'face': 'sans-serif'},
        )

    for u, v, data in subG.edges(data=True):
        weight = data.get('weight', 1)
        net.add_edge(
            u, v,
            value=weight,
            title=f"{weight} co-appearance(s)",
            color={'color': '#d9d9d9', 'opacity': 0.18},
        )

    net.set_options("""
    {
      "interaction": {
        "hover": true,
        "tooltipDelay": 150,
        "navigationButtons": true,
        "keyboard": true
      },
      "physics": {
        "stabilization": {"iterations": 400, "fit": true},
        "barnesHut": {
          "gravitationalConstant": -8000,
          "springLength": 200,
          "springConstant": 0.02,
          "damping": 0.5
        },
        "minVelocity": 0.75
      }
    }
    """)

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.html', delete=False, encoding='utf-8'
    ) as f:
        net.save_graph(f.name)
        f.seek(0)
        with open(f.name, 'r', encoding='utf-8') as rf:
            html = rf.read()
    return html


G, partition, degree, centrality, actor_movies, actor_avg_rev = build_network()

chapter_cover(
    number="Chapter 05",
    title="Actor Collaboration Network",
    deck="How are actors connected through collaborations, and does centrality relate to performance?"
)

# ---------- Metrics ----------
col_s1, col_s2, col_s3 = st.columns(3)
col_s1.metric("Actors (5+ movies)", f"{G.number_of_nodes():,}")
col_s2.metric("Collaboration Links", f"{G.number_of_edges():,}")
col_s3.metric("Communities Detected", len(set(partition.values())))

st.markdown("")

# ---------- Sidebar ----------
st.sidebar.header("Settings")
top_n = st.sidebar.slider("Actors in network graph", 30, 150, 80)
highlight_top_revenue = st.sidebar.checkbox("Highlight top 20% revenue actors", value=True)

search_actor = st.sidebar.text_input(
    "Highlight an actor (optional)",
    help="Type part of an actor's name to find them in the graph"
).strip().lower()

# ---------- Interactive pyvis network ----------
st.markdown("### Network Visualization")
st.markdown(
    f"The **{top_n} most-connected actors** are shown below. "
    "Each node is an actor; node size reflects how many collaborators they have. "
    "Colors represent communities detected by the **Louvain algorithm**. "
    "When enabled, **gold nodes with red borders** mark actors in the top 20% of average movie revenue among the visible network. "
    "**Hover** over any node to see details, **drag** nodes to rearrange, "
    "**scroll** to zoom, and use the on-screen buttons to pan."
)

top_nodes_list = sorted(degree, key=degree.get, reverse=True)[:top_n]

if search_actor:
    matches = [n for n in G.nodes() if search_actor in n.lower()]
    if matches:
        expanded = set(top_nodes_list)
        for m in matches:
            expanded.add(m)
            expanded.update(G.neighbors(m))
        top_nodes_list = list(expanded)
        st.info(f"Matched **{len(matches)}** actor(s): "
                f"{', '.join(matches[:5])}"
                f"{'...' if len(matches) > 5 else ''}. "
                f"Graph expanded to include their neighbors.")
    else:
        st.warning(f"No actor matching '{search_actor}' found in the network.")

subG = G.subgraph(top_nodes_list)

if highlight_top_revenue:
    st.markdown(
        """
        <div style="font-size:0.95rem; margin:0.5rem 0 0.75rem 0;">
            <span style="display:inline-block;width:14px;height:14px;background:#F4C430;border:3px solid #A61E2E;border-radius:50%;vertical-align:middle;margin-right:8px;"></span>
            Top 20% average-revenue actors among the visible network
        </div>
        """,
        unsafe_allow_html=True
    )

network_html = build_pyvis_html(subG, partition, degree, actor_movies, actor_avg_rev, highlight_top_revenue)
components.html(network_html, height=640, scrolling=False)

st.markdown("> The network reveals **clear clusters** of actors who frequently collaborate. "
            "The revenue highlight adds a second layer to the story: the highest-revenue actors "
            "are not always the largest or most central nodes, which visually supports the idea that "
            "collaboration centrality and commercial success are related only weakly. "
            "Enable the highlight and look closely — **gold nodes are scattered across multiple communities "
            "and different node sizes**, suggesting that high box-office actors do not form their own "
            "collaboration cluster.")

# ---------- Community breakdown ----------
st.markdown("---")
st.markdown("### Community Breakdown")
st.markdown("The Louvain algorithm groups actors by collaboration frequency. "
            "Larger communities usually correspond to broader Hollywood networks; "
            "smaller ones often reflect specific genres or production companies. "
            "**Hover a bar** to see the community's most central actors.")

comm_data = []
for comm_id in sorted(set(partition.values())):
    members = [n for n, c in partition.items() if c == comm_id]
    top3 = sorted(members, key=lambda x: degree.get(x, 0), reverse=True)[:3]
    comm_data.append({
        'Community': int(comm_id),
        'Size': len(members),
        'Top Actors': ', '.join(top3),
    })
comm_df = pd.DataFrame(comm_data).sort_values('Size', ascending=False)

bar_df = comm_df.head(12).copy()
bar_df['Community'] = bar_df['Community'].astype(str)
chart = alt.Chart(bar_df).mark_bar(
    color=COLORS.get('blue', '#457B9D'), cornerRadiusEnd=4
).encode(
    x=alt.X('Size:Q', title='Number of Actors'),
    y=alt.Y('Community:N', sort='-x', title='Community ID'),
    tooltip=[
        alt.Tooltip('Community:N', title='Community'),
        alt.Tooltip('Size:Q', title='Size'),
        alt.Tooltip('Top Actors:N', title='Top Actors'),
    ]
).properties(height=400, title='Largest Communities')
st.altair_chart(chart, use_container_width=True)

st.markdown("**All communities, ranked by size:**")
st.dataframe(comm_df, use_container_width=True, hide_index=True)

st.markdown("> The largest communities are broad Hollywood collaboration groups rather than isolated single-genre clusters. "
            "This helps explain why high-revenue actors can appear across different parts of the network instead of concentrating in one group.")

# ---------- Most connected actors ----------
st.markdown("---")
st.markdown("### Most Connected Actors")
st.markdown("Sorted by **degree centrality** — the fraction of other actors they have "
            "collaborated with directly.")

top_k = st.slider("Show top", 10, 30, 15)
top_actors = sorted(centrality, key=centrality.get, reverse=True)[:top_k]
table_data = pd.DataFrame({
    'Actor': top_actors,
    'Centrality': [round(centrality[a], 3) for a in top_actors],
    'Movies': [actor_movies[a] for a in top_actors],
    'Avg Revenue ($M)': [
        round(actor_avg_rev.get(a, 0) / 1e6, 1) for a in top_actors
    ],
    'Community': [partition[a] for a in top_actors],
})
st.dataframe(table_data, use_container_width=True, hide_index=True)

st.markdown("> The most connected actors are frequent collaborators, but their average revenues vary widely. "
            "This sets up the next question: whether being central in the collaboration network actually predicts commercial performance.")

# ---------- Centrality vs Revenue ----------
st.markdown("---")
st.markdown("### Does Centrality Predict Revenue?")
st.markdown("Each dot is an actor. **Hover to see their name**, centrality, and the average "
            "revenue of movies they appear in. The red line is the linear trend.")

rows = []
for a in G.nodes():
    if a in actor_avg_rev:
        rows.append({
            'actor': a,
            'centrality': centrality[a],
            'avg_revenue_m': actor_avg_rev[a] / 1e6,
            'movies': actor_movies.get(a, 1),
        })
cent_df = pd.DataFrame(rows)

if not cent_df.empty:
    cent_df['centrality'] = pd.to_numeric(cent_df['centrality'], errors='coerce')
    cent_df['avg_revenue_m'] = pd.to_numeric(cent_df['avg_revenue_m'], errors='coerce')
    cent_df['movies'] = pd.to_numeric(cent_df['movies'], errors='coerce')
    cent_df = cent_df.replace([np.inf, -np.inf], np.nan).dropna(
        subset=['centrality', 'avg_revenue_m', 'movies']
    )

if not cent_df.empty and len(cent_df) >= 2:
    corr = cent_df[['centrality', 'avg_revenue_m']].corr().iloc[0, 1]
    corr_label = f"{corr:.2f}" if pd.notna(corr) else "N/A"

    revenue_threshold = cent_df['avg_revenue_m'].quantile(0.8)
    cent_df['Revenue Group'] = np.where(
        cent_df['avg_revenue_m'] >= revenue_threshold,
        'Top 20% revenue',
        'Other actors'
    )

    scatter = alt.Chart(cent_df).mark_circle(
        opacity=0.68,
        strokeWidth=0
    ).encode(
        x=alt.X('centrality:Q', title='Degree Centrality'),
        y=alt.Y('avg_revenue_m:Q', title='Average Revenue (Million $)'),
        color=alt.Color(
            'Revenue Group:N',
            scale=alt.Scale(
                domain=['Top 20% revenue', 'Other actors'],
                range=['#A61E2E', COLORS.get('blue', '#457B9D')]
            ),
            legend=alt.Legend(
                title='Actor group',
                orient='right',
                labelLimit=180,
            )
        ),
        size=alt.Size(
            'movies:Q',
            title='Movie count',
            scale=alt.Scale(range=[35, 320]),
            legend=alt.Legend(
                orient='right',
                values=[10, 25, 50],
                labelLimit=80,
            )
        ),
        tooltip=[
            alt.Tooltip('actor:N', title='Actor'),
            alt.Tooltip('centrality:Q', title='Centrality', format='.3f'),
            alt.Tooltip('avg_revenue_m:Q', title='Avg Revenue ($M)',
                        format='.1f'),
            alt.Tooltip('movies:Q', title='Movies'),
        ]
    ).interactive()

    chart_layers = scatter
    if cent_df['centrality'].nunique() > 1 and cent_df['avg_revenue_m'].nunique() > 1:
        slope, intercept = np.polyfit(
            cent_df['centrality'].to_numpy(),
            cent_df['avg_revenue_m'].to_numpy(),
            1
        )
        x_min = cent_df['centrality'].min()
        x_max = cent_df['centrality'].max()
        line_df = pd.DataFrame({
            'centrality': [x_min, x_max],
            'avg_revenue_m': [slope * x_min + intercept, slope * x_max + intercept],
        })
        trend_line = alt.Chart(line_df).mark_line(
            color=COLORS.get('primary', '#A02030'), strokeWidth=2.5
        ).encode(
            x='centrality:Q',
            y='avg_revenue_m:Q'
        )
        chart_layers = scatter + trend_line

    st.altair_chart(
        chart_layers.properties(
            height=580,
            title=f'Centrality vs Average Revenue  (r = {corr_label})'
        ).configure_legend(
            labelFontSize=12,
            titleFontSize=13,
            symbolSize=130,
            padding=8,
            columns=1,
        ).configure_view(
            stroke=None
        ),
        use_container_width=True
    )

    st.markdown(f"""
> There is a **weak positive correlation** (r = {corr_label}) between centrality and revenue.
Actors with broader collaboration networks tend to appear in slightly higher-grossing films,
but centrality alone does not determine commercial success — many highly central actors
appear in modestly-budgeted films, and some blockbuster stars have narrow collaboration circles.
""")
else:
    st.info("No centrality data available.")


chapter_footer(
    prev_label="Chapter 04 · Text Analysis",
    prev_path="pages/4_Text_Analysis.py",
    next_label="Chapter 06 · Geo Analysis",
    next_path="pages/6_Geo_Analysis.py",
)
