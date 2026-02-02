import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from floportop import predict_movie

AVAILABLE_GENRES = [
    "Drama", "Comedy", "Documentary", "Romance", "Action", "Crime",
    "Thriller", "Horror", "Adventure", "Mystery", "Family", "Biography",
    "Fantasy", "History", "Music", "Sci-Fi", "Musical", "War",
    "Animation", "Western", "Sport", "Adult"
]


def main():
    st.title("Will This Movie Be Good?")

    with st.form("movie_form"):
        year = st.number_input("Release Year", 1900, 2030, 2024)
        runtime = st.number_input("Runtime (minutes)", 1, 500, 120)
        genres = st.multiselect("Genres", AVAILABLE_GENRES, ["Drama"])
        overview = st.text_area("Plot Overview", placeholder="Describe the movie...")
        budget = st.number_input("Budget (USD, optional)", 0, 500_000_000, 0)
        is_adult = st.checkbox("Adult Content (18+)")
        submitted = st.form_submit_button("Predict Rating")

    if submitted:
        if not overview.strip():
            st.error("Plot overview is required!")
            return
        if not genres:
            st.error("Select at least one genre!")
            return

        movie_data = {
            "startYear": int(year),
            "runtimeMinutes": int(runtime),
            "isAdult": 1 if is_adult else 0,
            "genres": ",".join(genres)
        }

        with st.spinner("Predicting..."):
            try:
                rating = predict_movie(movie_data, overview, budget if budget > 0 else None)
                st.success(f"Predicted IMDb Rating: **{rating:.1f}**/10")
            except Exception as e:
                st.error(f"Prediction failed: {e}")


if __name__ == "__main__":
    main()
