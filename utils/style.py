"""Vintage cinema theme + shared Altair theme."""
import altair as alt
import streamlit as st

COLORS = {
    "primary": "#A02030",       # deep cinema red
    "primary_dark": "#6E0F1A",
    "blue": "#3D5A6C",          # muted slate
    "green": "#5C8374",         # muted sage
    "dark": "#1A1A1A",
    "ink": "#2A2A2A",
    "muted": "#6B6B6B",
    "rule": "#E0DBD1",
    "cream": "#F4EFE6",
    "cream_dark": "#E8E1D3",
    "card_bg": "#FFFFFF",
    "gold": "#C8A04A",
}


_CINEMA_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Source+Serif+4:ital,wght@0,400;0,500;0,600;1,400&family=Source+Sans+3:wght@400;500;600;700&display=swap');

.stApp { background: #F4EFE6 !important; color: #1A1A1A !important; }
.main .block-container { max-width: 1100px; padding-top: 0 !important; padding-bottom: 5rem; margin-top: 0 !important; }

.film-strip {
    position: relative;
    height: 60px;
    margin: 0 -100vw 2.5rem -100vw;
    padding: 0 100vw;
    background: #1A1A1A;
    border-top: 2px solid #0a0a0a;
    border-bottom: 2px solid #0a0a0a;
    box-shadow: 0 4px 8px rgba(0,0,0,0.08);
}
.film-strip::before, .film-strip::after {
    content: "";
    position: absolute;
    left: 0; right: 0;
    height: 18px;
    background-image: radial-gradient(circle, #F4EFE6 0%, #F4EFE6 30%, transparent 32%);
    background-size: 32px 18px;
    background-repeat: repeat-x;
    background-position: center;
}
.film-strip::before { top: 4px; }
.film-strip::after { bottom: 4px; }

.film-strip-label {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    color: #F4EFE6;
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.05rem;
    font-weight: 400;
    font-style: italic;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    background: #1A1A1A;
    padding: 4px 28px;
    z-index: 5;
    white-space: nowrap;
    border-left: 1px solid #C8A04A;
    border-right: 1px solid #C8A04A;
}

html, body { font-family: "Source Sans 3", system-ui, sans-serif; color: #1A1A1A; }
p, li, .stMarkdown p {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.04rem;
    line-height: 1.72;
    color: #2A2A2A;
}

.stApp h1, .stApp h2, .stApp h3, .stApp h4, .main h1, .main h2, .main h3 {
    font-family: 'DM Serif Display', Georgia, serif !important;
    color: #1A1A1A !important;
    letter-spacing: 0 !important;
    font-weight: 400 !important;
}
.stApp h1 { font-size: 2.6rem !important; line-height: 1.18 !important; margin-bottom: 0.4rem !important; }
.stApp h2 { font-size: 1.8rem !important; line-height: 1.28 !important; margin-top: 2.4rem !important; margin-bottom: 0.6rem !important; }
.stApp h3 { font-size: 1.4rem !important; line-height: 1.32 !important; margin-top: 2rem !important; margin-bottom: 0.5rem !important; }

.stCaption, [data-testid="stCaptionContainer"] {
    font-family: "Source Serif 4", Georgia, serif !important;
    font-style: italic !important;
    font-size: 1.08rem !important;
    color: #5A5A5A !important;
    line-height: 1.5 !important;
}

[data-testid="stMarkdownContainer"] blockquote {
    border-left: 4px solid #A02030;
    background: rgba(160, 32, 48, 0.04);
    margin: 2rem 0;
    padding: 1rem 1.4rem 1rem 1.6rem;
    font-family: "Source Serif 4", Georgia, serif;
    font-size: 1.16rem;
    font-style: italic;
    line-height: 1.55;
    color: #1A1A1A;
    border-radius: 0 4px 4px 0;
}
[data-testid="stMarkdownContainer"] blockquote strong {
    font-style: normal;
    font-weight: 600;
    color: #6E0F1A;
}
[data-testid="stMarkdownContainer"] blockquote p {
    margin: 0;
    font-size: inherit;
    line-height: inherit;
    font-family: inherit;
    color: inherit;
}

hr {
    border: none !important;
    border-top: 1px solid #D4CBB8 !important;
    margin: 2.8rem 0 !important;
}

[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E0DBD1;
    border-radius: 2px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
[data-testid="stMetricLabel"] {
    font-family: "Source Sans 3", sans-serif !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: #6B6B6B !important;
    font-weight: 700 !important;
}
[data-testid="stMetricValue"] {
    font-family: "DM Serif Display", Georgia, serif !important;
    font-weight: 400 !important;
    color: #1A1A1A !important;
    font-size: 2rem !important;
}

[data-testid="stSidebar"] {
    background: #E8E1D3;
    border-right: 1px solid #D4CBB8;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
    font-family: "DM Serif Display", Georgia, serif !important;
    color: #1A1A1A !important;
    font-size: 1.15rem !important;
    margin-top: 1rem !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
    font-family: "Source Sans 3", sans-serif !important;
    font-size: 0.9rem !important;
    color: #2A2A2A !important;
}

[data-testid="stPageLink"] a {
    font-family: "Source Sans 3", sans-serif;
    font-weight: 600;
    color: #1A1A1A;
    text-decoration: none;
}
[data-testid="stPageLink"] a:hover { color: #A02030; }

[data-testid="stDataFrame"] {
    border: 1px solid #E0DBD1;
    border-radius: 2px;
}

[data-testid="stAlert"] {
    border-radius: 2px;
    border-left-width: 3px;
    font-family: "Source Sans 3", sans-serif;
    font-size: 0.95rem;
    background: #FFFFFF;
}

.chapter-cover { margin: 0 0 2rem 0; padding: 0 0 1.5rem 0; position: relative; }
.chapter-cover::after { display: none; }
.chapter-eyebrow {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: #A02030;
    margin-bottom: 1.2rem;
}
.chapter-title {
    font-family: 'DM Serif Display', Georgia, serif !important;
    font-size: 3.4rem !important;
    font-weight: 400 !important;
    line-height: 1.1 !important;
    color: #1A1A1A !important;
    margin: 0 0 1.4rem 0 !important;
    letter-spacing: 0 !important;
}
.chapter-deck {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.28rem;
    font-style: italic;
    line-height: 1.5;
    color: #4A4A4A;
    max-width: 720px;
    margin: 0;
}

.hero { text-align: left; padding: 1rem 0 3rem 0; margin-bottom: 3rem; position: relative; }
.hero::after {
    content: "";
    display: block;
    height: 16px;
    margin-top: 2.5rem;
    background-image: radial-gradient(circle, #A02030 0%, #A02030 32%, transparent 34%);
    background-size: 22px 16px;
    background-repeat: repeat-x;
    background-position: 0 center;
    max-width: 240px;
}
.hero-eyebrow {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: #A02030;
    margin-bottom: 1.5rem;
}
.hero-title {
    font-family: 'DM Serif Display', Georgia, serif !important;
    font-size: 4.2rem !important;
    font-weight: 400 !important;
    line-height: 1.05 !important;
    color: #1A1A1A !important;
    margin: 0 0 1.5rem 0 !important;
    letter-spacing: 0 !important;
}
.hero-deck {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.35rem;
    font-style: italic;
    line-height: 1.5;
    color: #3A3A3A;
    max-width: 760px;
    margin: 0 0 2rem 0;
}
.hero-byline {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.82rem;
    color: #6B6B6B;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-top: 2rem;
}
.hero-ornament {
    text-align: left;
    color: #A02030;
    font-size: 1rem;
    letter-spacing: 0.6em;
    margin: 0.6rem 0 1.4rem 0;
}

.lead-paragraph {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.18rem;
    line-height: 1.65;
    color: #2A2A2A;
    margin: 1rem 0 2rem 0;
}

.toc-number {
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 1.8rem;
    font-weight: 400;
    color: #A02030;
    line-height: 1;
}
.toc-chapter-desc {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1rem;
    color: #4A4A4A;
    line-height: 1.55;
    margin: 0.3rem 0 0 0;
    font-style: italic;
}

.chapter-footer { margin-top: 4rem; padding-top: 2rem; position: relative; }
.chapter-footer::before { display: none; }

h1 a, h2 a, h3 a, h4 a { display: none !important; }
[data-testid="stHorizontalBlock"] { gap: 1rem; }
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
}

.vega-embed, .vega-embed canvas, .vega-embed svg { background: transparent !important; }

[data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; }
[data-testid="stMain"] { padding-top: 0 !important; }
.stApp > header { display: none !important; }

/* Force-remove all top padding/margin from Streamlit's main container.
   Uses high-specificity selectors + !important to beat inline styles. */
section.main > div.block-container,
[data-testid="stMain"] > div,
[data-testid="stMain"] .block-container,
.stApp [data-testid="stMain"] .block-container,
.stApp section.main .block-container {
    padding-top: 1rem !important;
    margin-top: 0 !important;
}
[data-testid="stAppViewContainer"] {
    padding-top: 0 !important;
}

.wordcloud-card {
    background: #FFFFFF;
    border: 1px solid #E0DBD1;
    border-radius: 4px;
    padding: 1.2rem;
    margin: 0.5rem 0 2rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.wordcloud-card img {
    display: block;
    width: 100%;
    height: auto;
    border-radius: 2px;
}
</style>
"""


_FILM_STRIP_HTML = ''


# ---- Altair theme: cinema typography + transparent background ----
def _cinema_altair_theme():
    return {
        "config": {
            "background": "transparent",
            "view": {"stroke": "transparent"},
            "title": {
                "font": "DM Serif Display, Georgia, serif",
                "fontSize": 16,
                "fontWeight": 400,
                "color": "#1A1A1A",
                "anchor": "start",
                "offset": 12,
            },
            "axis": {
                "labelFont": "Source Sans 3, sans-serif",
                "titleFont": "Source Sans 3, sans-serif",
                "labelFontSize": 11,
                "titleFontSize": 12,
                "labelColor": "#4A4A4A",
                "titleColor": "#2A2A2A",
                "domainColor": "#D4CBB8",
                "gridColor": "#E0DBD1",
                "tickColor": "#D4CBB8",
            },
            "legend": {
                "labelFont": "Source Sans 3, sans-serif",
                "titleFont": "Source Sans 3, sans-serif",
                "labelFontSize": 11,
                "titleFontSize": 11,
                "labelColor": "#2A2A2A",
                "titleColor": "#2A2A2A",
            },
            "header": {
                "labelFont": "Source Sans 3, sans-serif",
                "titleFont": "DM Serif Display, Georgia, serif",
            },
        }
    }


# Register and enable once on import
try:
    alt.themes.register("cinema", _cinema_altair_theme)
    alt.themes.enable("cinema")
except Exception:
    pass


def apply_cinema_style():
    st.markdown(_CINEMA_CSS, unsafe_allow_html=True)
    st.markdown(_FILM_STRIP_HTML, unsafe_allow_html=True)


def apply_editorial_style():
    apply_cinema_style()


def chapter_cover(number, title, deck):
    html = (
        '<div class="chapter-cover">'
        '<div class="chapter-eyebrow">' + number + '</div>'
        '<h1 class="chapter-title">' + title + '</h1>'
        '<p class="chapter-deck">' + deck + '</p>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def chapter_footer(prev_label=None, prev_path=None, next_label=None, next_path=None):
    st.markdown('<div class="chapter-footer"></div>', unsafe_allow_html=True)
    col1, _, col2 = st.columns([1, 0.2, 1])
    with col1:
        if prev_path:
            st.page_link(prev_path, label="\u2190 " + (prev_label or ""))
    with col2:
        if next_path:
            st.page_link(next_path, label=(next_label or "") + " \u2192")
