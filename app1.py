import streamlit as st
import pandas as pd
import requests
import numpy as np
import pickle
import time
from train import user_based,improved_recommendations, hybrid

TMDB_API_KEY = "d7adaa848f504bc4b602533f7ea5789d"
@st.cache_resource
def load_data():
    try:
        movies = pd.read_csv("processed/processed_metadata.csv")
        ratings = pd.read_csv("processed/processed_ratings.csv")
        cosine_sim = np.load("cosine_sim.npy")
        with open("svd.pkl", "rb") as f:
            svd_model = pickle.load(f)
        return movies, ratings, cosine_sim, svd_model
    except FileNotFoundError as e:
        st.error(f"Error loading data: {e}")
        st.stop()

movies, ratings, cosine_sim, svd_model = load_data()

def get_movie_poster_url(title, movies_df, api_key=TMDB_API_KEY):
    movie_row = movies_df[movies_df['title'] == title]
    if not movie_row.empty:
        tmdb_id = int(movie_row['id'].iloc[0])
        base_url = "https://api.themoviedb.org/3/movie/{}"
        params = {"api_key": api_key}
        try:
            response = requests.get(base_url.format(tmdb_id), params=params)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w300{poster_path}"  
            else:
                return None
        except requests.exceptions.RequestException:
            return None
    else:
        return None


st.title("🎬 Movie Recommendation System")
st.markdown("<p>Discover movies you'll love! Powered by collaborative and content-based filtering.</p>", unsafe_allow_html=True)
st.markdown("<div class='container'>", unsafe_allow_html=True)
st.header("Recommendation Settings")
method = st.selectbox("Method", ["Content", "Collaborative", "Hybrid"])
user_id = st.number_input("User ID", min_value=1, max_value=ratings['userId'].max(), value=1, step=1) if method in ["Collaborative", "Hybrid"] else None
title = st.text_input("Movie Title") if method in ["Content", "Hybrid"] else None
if st.button("Recommend", key='recommend_button'):
    progress_bar = st.progress(0)
    try:
        for i in range(100):
            time.sleep(0.5)
            progress_bar.progress(i + 1)
        if method == "Content" and title:
            recs = improved_recommendations(title)
        elif method == "Collaborative" and user_id is not None and svd_model is not None:
            recs = user_based(user_id, svd_model)
        elif method == "Hybrid" and user_id is not None and title:
            recs = hybrid(user_id, title)
        else:
            st.error("Please provide the required inputs for the selected method.")
            recs = None
        progress_bar.progress(100)
        if recs is not None:
            st.header("✨ Recommendations")
            st.markdown("<div class='recommendations-grid'>", unsafe_allow_html=True)
            if isinstance(recs, pd.Series):
                recs = recs.to_list()
            elif not isinstance(recs, list):
                recs = list(recs)
            for movie_title in recs:
                poster_url = get_movie_poster_url(movie_title, movies)
                if poster_url:
                    st.markdown(f"""
                        <div class='recommendation-item'>
                            <img src="{poster_url}" alt="{movie_title}" class='fade-in'>
                            <p>{movie_title}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write(f"No poster found for {movie_title}")
            st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"An error: {e}")
st.markdown("</div>", unsafe_allow_html=True)
