"""
Streamlit frontend for movie rating prediction.
Integrates with the FastAPI backend via HTTP.
"""
import os
from pathlib import Path

import streamlit as st
import requests

# API URL: environment variable or default to GCS deployment
API_URL = os.environ.get("API_URL", "https://floportop-v2-233992317574.europe-west1.run.app")

# Must be the first Streamlit command
st.set_page_config(
    page_title="Floportop - Movie Rating Predictor",
    page_icon="logo.svg",
    layout="wide",
)

# Load custom CSS
css_file = Path(__file__).parent / "styles.css"
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)

AVAILABLE_GENRES = [
    "Drama", "Comedy", "Documentary", "Romance", "Action", "Crime",
    "Thriller", "Horror", "Adventure", "Mystery", "Family", "Biography",
    "Fantasy", "History", "Music", "Sci-Fi", "Musical", "War",
    "Animation", "Western", "Sport", "Adult"
]


# ============================================
# Helper Functions
# ============================================

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

    resp = requests.get(f"{API_URL}/predict", params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def search_similar_films(query, k=5):
    """Call the API to find similar films."""
    params = {"query": query, "k": k}
    resp = requests.get(f"{API_URL}/similar-film", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_rating_class(rating):
    """Return CSS class based on rating value."""
    if rating >= 7.0:
        return "high"
    elif rating >= 5.0:
        return "medium"
    return "low"


def render_movie_card(movie):
    """Render a compact movie card for bento grid."""
    title = movie.get("title", "Unknown")
    imdb_id = movie.get("imdb_id", "")
    genres_raw = movie.get("genres", "")
    rating = movie.get("vote_average", 0)

    # Clean up genres - handle list, string, or empty
    if isinstance(genres_raw, list):
        genres = ", ".join(genres_raw) if genres_raw else ""
    elif isinstance(genres_raw, str):
        # Remove brackets if it's a string representation of a list
        genres = genres_raw.strip("[]'\"").replace("', '", ", ").replace("','", ", ")
    else:
        genres = ""

    rating_class = get_rating_class(rating)

    # Make title clickable if we have IMDb ID
    if imdb_id:
        title_html = f'<a href="https://www.imdb.com/title/{imdb_id}/" target="_blank" class="movie-title-link">{title}</a>'
        imdb_link_html = f'<a href="https://www.imdb.com/title/{imdb_id}/" target="_blank" class="imdb-link">IMDb</a>'
    else:
        title_html = f'<span class="movie-title">{title}</span>'
        imdb_link_html = ""

    # Only show genres if we have them
    genres_html = f'<span class="movie-genres">{genres}</span>' if genres else ""

    return f'''<div class="movie-card">
<div class="movie-card-header">
{title_html}
<span class="rating-badge {rating_class}">{rating:.1f}</span>
</div>
{genres_html}
{imdb_link_html}
</div>'''


def render_full_bar_placeholder():
    """Full-width bar - initial state."""
    return '''
    <div class="full-bar">
        <h2>Flop or Top? Let's find out...</h2>
    </div>
    '''


def render_full_bar_loading():
    """Full-width bar - loading state."""
    return '''
    <div class="full-bar loading">
        <h2>Analyzing your movie...</h2>
    </div>
    '''


def render_bento_with_loading_movies(rating):
    """Bento layout: rating ready, movies still loading."""
    rating_class = get_rating_class(rating)
    return f'''
    <div class="bento-container">
        <div class="rating-card {rating_class}">
            <h1>{rating:.1f}/10</h1>
            <p>Predicted Rating</p>
        </div>
        <div class="movies-loading">
            <p>Finding similar movies...</p>
        </div>
    </div>
    '''


def render_bento_complete(rating, movies):
    """Bento layout: rating and movies both ready."""
    # Filter out movies with 0.0 rating
    valid_movies = [m for m in movies if m.get("vote_average", 0) > 0]
    cards_html = "".join(render_movie_card(m) for m in valid_movies)
    rating_class = get_rating_class(rating)
    return f'''<div class="bento-container">
<div class="rating-card {rating_class}">
<h1>{rating:.1f}/10</h1>
<p>Predicted Rating</p>
</div>
<div class="similar-movies-grid">{cards_html}</div>
</div>'''


# ============================================
# Main App
# ============================================

def main():
    st.title("Floportop")
    st.caption("Predict movie ratings and find similar films")

    # API status indicator in sidebar
    api_online = check_api_health()
    if api_online:
        st.sidebar.success("API Online")
    else:
        st.sidebar.warning("API may be cold starting...")
        st.sidebar.caption(f"URL: {API_URL}")

    # Initialize session state
    if "rating" not in st.session_state:
        st.session_state.rating = None
    if "show_result" not in st.session_state:
        st.session_state.show_result = False

    # Form - more compact
    with st.form("movie_form"):
        # Row 1: Year, Runtime, Budget
        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.number_input("Year", 1900, 2030, 2024)
        with col2:
            runtime = st.number_input("Runtime (min)", 1, 500, 120)
        with col3:
            budget = st.number_input("Budget ($)", 0, 500_000_000, 0)

        # Row 2: Genres
        genres = st.multiselect("Genres", AVAILABLE_GENRES, ["Drama"])

        # Row 3: Plot Overview
        overview = st.text_area(
            "Plot Overview",
            placeholder="Describe the movie plot...",
            height=100
        )

        # Row 4: Adult content option
        is_adult = st.checkbox("Adult Content (18+)")

        submitted = st.form_submit_button("Predict Rating", use_container_width=True)

    # Results container
    results_container = st.empty()

    # Initial state: show full-width bar
    if not st.session_state.show_result:
        results_container.markdown(render_full_bar_placeholder(), unsafe_allow_html=True)

    if submitted:
        if not overview.strip():
            st.error("Plot overview is required!")
        elif not genres:
            st.error("Select at least one genre!")
        else:
            # Step 1: Full bar loading state
            results_container.markdown(render_full_bar_loading(), unsafe_allow_html=True)

            try:
                # Get rating prediction
                result = predict_rating(year, runtime, genres, overview, budget, is_adult)
                rating = result["predicted_rating"]

                # Store in session state
                st.session_state.rating = rating
                st.session_state.show_result = True

                # Step 2: Show bento with rating + movies loading
                results_container.markdown(
                    render_bento_with_loading_movies(rating),
                    unsafe_allow_html=True,
                )

            except requests.HTTPError as e:
                results_container.markdown(render_full_bar_placeholder(), unsafe_allow_html=True)
                st.error(f"API Error: {e.response.text}")
                return
            except requests.RequestException as e:
                results_container.markdown(render_full_bar_placeholder(), unsafe_allow_html=True)
                st.error(f"Connection failed: {e}")
                return

            # Step 3: Fetch similar movies
            try:
                similar_result = search_similar_films(overview, k=5)

                if similar_result["results"]:
                    # Step 4: Show complete bento with movies
                    results_container.markdown(
                        render_bento_complete(rating, similar_result["results"]),
                        unsafe_allow_html=True,
                    )

            except requests.HTTPError as e:
                error_detail = e.response.json().get("detail", str(e))
                st.caption(f"Similar movies unavailable: {error_detail}")
            except requests.RequestException as e:
                st.caption(f"Could not find similar movies: {e}")


if __name__ == "__main__":
    main()
