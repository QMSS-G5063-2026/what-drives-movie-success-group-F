"""Shared data loaders. Cached once and reused across all pages."""
import json
import re

import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def load_movies():
    movies = pd.read_csv("data/tmdb_5000_movies.csv")
    movies["genre_list"] = movies["genres"].apply(lambda g: [x["name"] for x in json.loads(g)])
    movies["release_date"] = pd.to_datetime(movies["release_date"], errors="coerce")
    movies["year"] = movies["release_date"].dt.year
    return movies


@st.cache_data
def load_credits():
    return pd.read_csv("data/tmdb_5000_credits.csv")


def _clean_review_text(t):
    if pd.isna(t):
        return ""
    t = re.sub(r"<[^>]+>", " ", str(t))
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)   # strip URLs so domain fragments (com/org/etc.) don't leak into tokens
    t = re.sub(r"[\*_]+", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


@st.cache_data
def load_reviews_with_sentiment():
    """Reviews with cleaned text + VADER compound scores attached."""
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    reviews = pd.read_csv("data/tmdb_reviews.csv")
    reviews["clean"] = reviews["content"].apply(_clean_review_text)

    analyzer = SentimentIntensityAnalyzer()
    reviews["sentiment"] = reviews["clean"].apply(
        lambda t: analyzer.polarity_scores(t)["compound"]
    )
    return reviews


STOPWORDS = set("""the a an is are was were be been being have has had do does did
    will would shall should may might can could of in to for on with at by from as
    into through during before after above below between out off over under again
    further then once here there when where why how all each every both few more
    most other some such no nor not only own same so than too very and but or if
    while i me my we us our you your he him his she her it its they them their
    this that these those what which who whom whose
    movie film movies films just like really one get also much even well see know
    way make made say said about because still though however although been
    don doesn didn wasn weren isn aren couldn wouldn shouldn t s re ve ll d m
    com org net html www http https
    rating ratings rated review reviews reviewer reviewers
    decent
    """.split())


def tokenize(text):
    """Lowercase word tokens, stopwords removed, length > 2."""
    if pd.isna(text):
        return []
    return [w for w in re.findall(r"[a-z]+", str(text).lower())
            if w not in STOPWORDS and len(w) > 2]


@st.cache_data
def load_reviews_with_tokens():
    """Reviews with tokenized word lists (for text analysis page)."""
    reviews = pd.read_csv("data/tmdb_reviews.csv")
    reviews["clean"] = reviews["content"].apply(_clean_review_text)
    reviews["tokens"] = reviews["clean"].apply(tokenize)
    return reviews
