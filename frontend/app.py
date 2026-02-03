"""
Streamlit frontend for movie rating prediction.
Integrates with the FastAPI backend via HTTP.
"""
import os
import streamlit as st
import requests

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8080")

AVAILABLE_GENRES = [
    "Drama", "Comedy", "Documentary", "Romance", "Action", "Crime",
    "Thriller", "Horror", "Adventure", "Mystery", "Family", "Biography",
    "Fantasy", "History", "Music", "Sci-Fi", "Musical", "War",
    "Animation", "Western", "Sport", "Adult"
]


def check_api_health():
    """Check if the API is available."""
    try:
        resp = requests.get(f"{API_URL}/", timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def predict_rating(year, runtime, genres, overview, budget, is_adult):
    """Call the API to predict movie rating."""
    params = {
        "startYear": year,
        "runtimeMinutes": runtime,
        "genres": ",".join(genres),
        "overview": overview,
        "isAdult": 1 if is_adult else 0,
    }
    if budget and budget > 0:
        params["budget"] = budget

    resp = requests.get(f"{API_URL}/predict", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def search_similar_films(query, k=10):
    """Call the API to find similar films."""
    params = {"query": query, "k": k}
    resp = requests.get(f"{API_URL}/similar-film", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    st.set_page_config(page_title="Floportop - Movie Rating Predictor", page_icon="🎬")
    st.title("🎬 Floportop")
    st.caption("Predict movie ratings and find similar films")

    # API status indicator
    api_online = check_api_health()
    if api_online:
        st.sidebar.success("✅ API Online")
    else:
        st.sidebar.error(f"❌ API Offline ({API_URL})")
        st.error("Cannot connect to the API. Please ensure the backend is running.")
        return

    tab1, tab2 = st.tabs(["🎯 Predict Rating", "🔍 Find Similar Films"])

    # Tab 1: Rating Prediction
    with tab1:
        st.header("Will This Movie Be Good?")

        with st.form("movie_form"):
            col1, col2 = st.columns(2)
            with col1:
                year = st.number_input("Release Year", 1900, 2030, 2024)
                runtime = st.number_input("Runtime (minutes)", 1, 500, 120)
            with col2:
                budget = st.number_input("Budget (USD, optional)", 0, 500_000_000, 0)
                is_adult = st.checkbox("Adult Content (18+)")

            genres = st.multiselect("Genres", AVAILABLE_GENRES, ["Drama"])
            overview = st.text_area(
                "Plot Overview",
                placeholder="Describe the movie plot...",
                height=100
            )
            submitted = st.form_submit_button("Predict Rating", use_container_width=True)

        if submitted:
            if not overview.strip():
                st.error("Plot overview is required!")
            elif not genres:
                st.error("Select at least one genre!")
            else:
                with st.spinner("Predicting..."):
                    try:
                        result = predict_rating(year, runtime, genres, overview, budget, is_adult)
                        rating = result["predicted_rating"]

                        # Display result with color coding
                        if rating >= 7:
                            st.success(f"### Predicted Rating: **{rating:.1f}**/10 🌟")
                        elif rating >= 5:
                            st.warning(f"### Predicted Rating: **{rating:.1f}**/10")
                        else:
                            st.error(f"### Predicted Rating: **{rating:.1f}**/10")

                    except requests.HTTPError as e:
                        st.error(f"API Error: {e.response.text}")
                    except requests.RequestException as e:
                        st.error(f"Connection failed: {e}")

    # Tab 2: Similar Films Search
    with tab2:
        st.header("Find Similar Films")
        st.caption("Search by title, plot description, genre, actor, or any combination")

        query = st.text_input(
            "Search Query",
            placeholder="e.g., 'dark sci-fi thriller with AI' or 'movies like Inception'"
        )
        num_results = st.slider("Number of results", 1, 20, 10)

        if st.button("Search", use_container_width=True) and query.strip():
            with st.spinner("Searching..."):
                try:
                    result = search_similar_films(query, num_results)

                    if result["results"]:
                        st.write(f"Found {result['count']} similar films:")

                        for i, movie in enumerate(result["results"], 1):
                            with st.expander(
                                f"**{i}. {movie['title']}** - ⭐ {movie['vote_average']:.1f}"
                            ):
                                st.write(f"**Genres:** {movie['genres']}")
                                st.write(f"**Directors:** {movie['directors']}")
                                st.write(f"**Cast:** {movie['cast']}")
                                st.write(f"**Overview:** {movie['overview']}")
                                st.caption(f"IMDB: {movie['imdb_id']} | Similarity: {movie['score']:.3f}")
                    else:
                        st.info("No results found. Try a different query.")

                except requests.HTTPError as e:
                    error_detail = e.response.json().get("detail", str(e))
                    st.error(f"Search failed: {error_detail}")
                except requests.RequestException as e:
                    st.error(f"Connection failed: {e}")


if __name__ == "__main__":
    main()
