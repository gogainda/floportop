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
        <h2>Enter your movie details above</h2>
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
            <h1>{rating:.1f}<span class="rating-max">/10</span></h1>
            <p>Predicted Rating</p>
        </div>
        <div class="movies-loading">
            <p>Finding similar movies...</p>
        </div>
    </div>
    '''


def render_bento_complete(rating, movies):
    """Bento layout: rating on left, movies in 2x2 grid on right."""
    # Filter out movies with 0.0 rating, limit to 4
    valid_movies = [m for m in movies if m.get("vote_average", 0) > 0][:4]
    cards_html = "".join(render_movie_card(m) for m in valid_movies)
    rating_class = get_rating_class(rating)
    return f'''<div class="bento-container">
<div class="rating-card {rating_class}">
<h1>{rating:.1f}<span class="rating-max">/10</span></h1>
<p>Predicted Rating</p>
</div>
<div class="movies-panel">
<div class="movies-panel-header">
<span class="movies-panel-title">REFERENCE FILMS</span>
</div>
<div class="movies-grid">{cards_html}</div>
</div>
</div>'''


def render_prediction_page():
    """Render the prediction UI and results."""
    # Initialize session state
    if "rating" not in st.session_state:
        st.session_state.rating = None
    if "similar_movies" not in st.session_state:
        st.session_state.similar_movies = []
    if "show_result" not in st.session_state:
        st.session_state.show_result = False

    # Form
    with st.form("movie_form"):
        overview = st.text_area(
            "Plot Overview",
            placeholder="Describe the movie plot...",
            height=120
        )

        col1, col2 = st.columns(2)
        with col1:
            budget = st.number_input("Budget (USD)", 0, 500_000_000, 0)
        with col2:
            year = st.number_input("Release Year", 1900, 2030, 2024)

        col3, col4 = st.columns(2)
        with col3:
            runtime = st.number_input("Runtime (minutes)", 1, 500, 120)
        with col4:
            genres = st.multiselect("Genre", AVAILABLE_GENRES, ["Drama"])

        is_adult = st.checkbox("Adult Content (18+)")
        submitted = st.form_submit_button("Predict Rating", use_container_width=True)

    results_container = st.empty()

    if st.session_state.show_result and st.session_state.rating is not None:
        if st.session_state.similar_movies:
            results_container.markdown(
                render_bento_complete(st.session_state.rating, st.session_state.similar_movies),
                unsafe_allow_html=True,
            )
        else:
            results_container.markdown(
                render_bento_with_loading_movies(st.session_state.rating),
                unsafe_allow_html=True,
            )
    else:
        results_container.markdown(render_full_bar_placeholder(), unsafe_allow_html=True)

    if submitted:
        if not overview.strip():
            st.error("Plot overview is required!")
        elif not genres:
            st.error("Select at least one genre!")
        else:
            try:
                with st.spinner("Predicting rating..."):
                    result = predict_rating(year, runtime, genres, overview, budget, is_adult)
                rating = result["predicted_rating"]

                st.session_state.rating = rating
                st.session_state.show_result = True

                try:
                    similar_result = search_similar_films(overview, k=5)
                    st.session_state.similar_movies = similar_result.get("results", [])
                except Exception as e:
                    print(f"DEBUG: Similar films search failed: {e}")
                    st.session_state.similar_movies = []

                if st.session_state.similar_movies:
                    results_container.markdown(
                        render_bento_complete(rating, st.session_state.similar_movies),
                        unsafe_allow_html=True,
                    )
                else:
                    results_container.markdown(
                        render_bento_with_loading_movies(rating),
                        unsafe_allow_html=True,
                    )

            except requests.HTTPError as e:
                st.session_state.show_result = False
                st.session_state.similar_movies = []
                results_container.markdown(render_full_bar_placeholder(), unsafe_allow_html=True)
                st.error(f"API Error: {e}")
            except requests.RequestException as e:
                st.session_state.show_result = False
                st.session_state.similar_movies = []
                results_container.markdown(render_full_bar_placeholder(), unsafe_allow_html=True)
                st.error(f"Connection failed: {e}")
            except Exception as e:
                st.session_state.show_result = False
                st.session_state.similar_movies = []
                results_container.markdown(render_full_bar_placeholder(), unsafe_allow_html=True)
                st.error(f"Error: {e}")


def render_technical_page():
    """Render technical details: data sources to serving."""
    st.title("How The Model Is Built")
    st.caption("From data collection to training to production serving.")

    st.subheader("1) Data Sources")
    st.markdown(
        "- IMDb dataset: movie metadata and target ratings.\n"
        "- TMDB movies dataset: plot overviews, keywords, cast, directors, and financial context.\n"
        "- Optional Kaggle API pull for rebuilding similarity data locally."
    )

    st.subheader("2) Feature Engineering")
    st.markdown(
        "- Core metadata features: release year, runtime, genres, adult flag.\n"
        "- Text understanding: movie overview embedded with `all-MiniLM-L6-v2`.\n"
        "- Dimensionality reduction: embedding compressed via PCA (20 components).\n"
        "- Budget handling: `log1p` transform with decade-based median imputation when missing."
    )

    st.subheader("3) Prediction Model")
    st.markdown(
        "- Regression model trained on historical labeled movies.\n"
        "- Runtime API uses model artifact `models/model_v5.pkl`.\n"
        "- The `/predict` endpoint returns the estimated IMDb-style score."
    )

    st.subheader("4) Similarity Engine")
    st.markdown(
        "- Search corpus includes enriched movie text built from overview, genres, cast, directors, and keywords.\n"
        "- Embeddings are generated with `BAAI/bge-base-en-v1.5`.\n"
        "- ANN search runs with FAISS index (`models/index.faiss`) and returns nearest titles."
    )

    st.subheader("5) Serving Architecture")
    st.markdown(
        "- FastAPI serves prediction and similarity endpoints on port `8080`.\n"
        "- Streamlit UI runs on port `8501` and calls API over internal HTTP.\n"
        "- Container startup script launches both services in one process group.\n"
        "- Docker image bakes dependencies and model assets for predictable startup."
    )

    st.subheader("6) Production Deployment")
    st.markdown(
        "- Image is built with Docker and shipped to Cloud Run.\n"
        "- Cloud Run exposes Streamlit publicly while API remains internal to the container.\n"
        "- Health endpoint (`/`) is used for readiness and status checks."
    )


# ============================================
# Main App
# ============================================

def main():
    # Header pill
    st.markdown('''<div class="header-pill">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
        </svg>
        Flop or Top
    </div>''', unsafe_allow_html=True)

    # API status indicator in sidebar
    api_online = check_api_health()
    if api_online:
        st.sidebar.success("API Online")
    else:
        st.sidebar.warning("API may be cold starting...")
        st.sidebar.caption(f"URL: {API_URL}")
    page = st.sidebar.radio("Page", ["Predict", "How It's Built"], index=0)
    if page == "Predict":
        render_prediction_page()
    else:
        render_technical_page()


if __name__ == "__main__":
    main()
