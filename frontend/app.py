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


def render_rating_card(state="placeholder", rating=None):
    """Render the rating card in different states."""
    if state == "placeholder":
        return """
        <div class="rating-card placeholder">
            <h2>Flop or Top? Let's see...</h2>
        </div>
        """
    elif state == "loading":
        return """
        <div class="rating-card loading">
            <h2>Analyzing your movie...</h2>
        </div>
        """
    elif state == "result" and rating is not None:
        return f"""
        <div class="rating-card result">
            <h1>{rating:.1f}/10</h1>
            <p>Predicted IMDb Rating</p>
        </div>
        """
    elif state == "error":
        return """
        <div class="rating-card placeholder">
            <h2>Oops! Try again...</h2>
        </div>
        """
    return ""


# ============================================
# Main App
# ============================================

def main():
    st.title("🎬 Floportop")
    st.caption("Predict movie ratings and find similar films")

    # API status indicator in sidebar
    api_online = check_api_health()
    if api_online:
        st.sidebar.success("✅ API Online")
    else:
        st.sidebar.warning("⚠️ API may be cold starting...")
        st.sidebar.caption(f"URL: {API_URL}")

    # Initialize session state
    if "rating" not in st.session_state:
        st.session_state.rating = None
    if "show_result" not in st.session_state:
        st.session_state.show_result = False

    # Form
    with st.form("movie_form"):
        # Row 1: Year, Runtime, Budget
        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.number_input("Release Year", 1900, 2030, 2024)
        with col2:
            runtime = st.number_input("Runtime (min)", 1, 500, 120)
        with col3:
            budget = st.number_input("Budget (USD)", 0, 500_000_000, 0)

        # Row 2: Genres
        genres = st.multiselect("Genres", AVAILABLE_GENRES, ["Drama"])

        # Row 3: Plot Overview
        overview = st.text_area(
            "Plot Overview",
            placeholder="Describe the movie plot...",
            height=100
        )

        # Options
        is_adult = st.checkbox("Adult Content (18+)")

        submitted = st.form_submit_button("Predict Rating", use_container_width=True)

    # Rating card - below the form
    rating_container = st.empty()

    # Show current state
    if st.session_state.show_result and st.session_state.rating is not None:
        rating_container.markdown(
            render_rating_card("result", st.session_state.rating),
            unsafe_allow_html=True,
        )
    else:
        rating_container.markdown(
            render_rating_card("placeholder"),
            unsafe_allow_html=True,
        )

    # Similar movies container
    similar_container = st.container()

    if submitted:
        if not overview.strip():
            st.error("Plot overview is required!")
        elif not genres:
            st.error("Select at least one genre!")
        else:
            # Show loading state
            rating_container.markdown(
                render_rating_card("loading"),
                unsafe_allow_html=True,
            )

            try:
                result = predict_rating(year, runtime, genres, overview, budget, is_adult)
                rating = result["predicted_rating"]

                # Store in session state and show result
                st.session_state.rating = rating
                st.session_state.show_result = True

                rating_container.markdown(
                    render_rating_card("result", rating),
                    unsafe_allow_html=True,
                )

            except requests.HTTPError as e:
                rating_container.markdown(
                    render_rating_card("error"),
                    unsafe_allow_html=True,
                )
                st.error(f"API Error: {e.response.text}")
                return
            except requests.RequestException as e:
                rating_container.markdown(
                    render_rating_card("error"),
                    unsafe_allow_html=True,
                )
                st.error(f"Connection failed: {e}")
                return

            # Similar movies - automatically after rating
            with similar_container:
                with st.spinner("Finding similar movies..."):
                    try:
                        result = search_similar_films(overview, k=5)

                        if result["results"]:
                            st.subheader("Similar Movies")
                            for movie in result["results"]:
                                title = movie.get("title", "Unknown")
                                vote = movie.get("vote_average", 0)
                                movie_overview = movie.get("overview", "")
                                display_overview = ""
                                if movie_overview:
                                    display_overview = movie_overview[:200] + "..." if len(movie_overview) > 200 else movie_overview

                                st.markdown(
                                    f"""
                                    <div class="movie-card">
                                        <strong>{title}</strong> — ⭐ {vote:.1f}
                                        <br><small style="color: #666;">{display_overview}</small>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                    except requests.HTTPError as e:
                        error_detail = e.response.json().get("detail", str(e))
                        st.warning(f"Similar movies unavailable: {error_detail}")
                    except requests.RequestException as e:
                        st.warning(f"Could not find similar movies: {e}")


if __name__ == "__main__":
    main()
