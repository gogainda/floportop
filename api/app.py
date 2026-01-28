"""
Floportop API - Movie Rating Prediction

Endpoints:
- GET /             : Health check
- GET /predict      : Predict movie rating
- GET /similar-film : Find similar movies by text query
"""

from fastapi import FastAPI, HTTPException
import numpy as np

# Import our package
import sys
from pathlib import Path

# Add parent directory to path so we can import floportop package
sys.path.insert(0, str(Path(__file__).parent.parent))

from floportop import predict_movie, load_model
from floportop.movie_search import ensure_index, get_model

app = FastAPI(
    title="Floportop API",
    description="Predict IMDb movie ratings using machine learning",
    version="2.0.0"
)

# Global cache for movie search
_movies_df = None
_search_index = None
_search_model = None

# Load prediction model on startup (caches it for faster predictions)
@app.on_event("startup")
def startup_event():
    try:
        load_model()
        print("✅ Prediction model loaded and ready")
    except Exception as e:
        print(f"⚠️ Prediction model failed to load: {e}")


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "online", "model_version": "v2"}


@app.get("/predict")
def predict(
    startYear: int,
    runtimeMinutes: int,
    numVotes: int,
    isAdult: int = 0,
    genres: str = "Drama"
):
    """
    Predict the rating for a movie.

    Parameters:
    - startYear: Release year (e.g., 2020)
    - runtimeMinutes: Movie length in minutes (e.g., 120)
    - numVotes: Number of IMDb votes (e.g., 50000)
    - isAdult: Adult content flag (0 or 1, default 0)
    - genres: Comma-separated genres (e.g., "Action,Adventure,Sci-Fi")

    Returns:
    - predicted_rating: Predicted IMDb rating (1-10 scale)
    """
    try:
        rating = predict_movie({
            "startYear": startYear,
            "runtimeMinutes": runtimeMinutes,
            "numVotes": numVotes,
            "isAdult": isAdult,
            "genres": genres
        })

        return {
            "predicted_rating": round(rating, 2),
            "input": {
                "startYear": startYear,
                "runtimeMinutes": runtimeMinutes,
                "numVotes": numVotes,
                "isAdult": isAdult,
                "genres": genres
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


def _ensure_search_index(rebuild: bool = False):
    """Lazily load the search index on first use, or rebuild if requested."""
    global _movies_df, _search_index, _search_model
    if rebuild:
        from floportop.movie_search import INDEX_FAISS, load_movie_data, build_index
        # Clear only the index file (keep movies.pkl - CSV data doesn't change)
        if INDEX_FAISS.exists():
            INDEX_FAISS.unlink()
        # Clear in-memory cache
        _search_index = None
        # Load movies (from cache) and rebuild index
        _movies_df = load_movie_data()
        _search_index = build_index(_movies_df)
        _search_model = get_model()
        print("✅ Search index rebuilt")
    elif _search_index is None:
        _movies_df, _search_index = ensure_index()
        _search_model = get_model()
        print("✅ Search index loaded and ready")


@app.get("/similar-film")
def similar_film(query: str, k: int = 10, rebuild: bool = False):
    """
    Find similar films based on a text query.

    Parameters:
    - query: Search text (movie title, description, genre, actor, etc.)
    - k: Number of results to return (default 10)
    - rebuild: Force rebuild of the search index (default false)

    Returns:
    - results: List of similar movies with scores
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    _ensure_search_index(rebuild=rebuild)
    q_emb = _search_model.encode([query], normalize_embeddings=True).astype("float32")
    scores, idxs = _search_index.search(q_emb, k)

    results = []
    for i, idx in enumerate(idxs[0]):
        row = _movies_df.iloc[idx]
        results.append({
            "title": row["title"],
            "imdb_id": row["imdbId"],
            "overview": row["overview"],
            "genres": row["genre_names"],
            "directors": row["directors"],
            "cast": row["cast_top"],
            "vote_average": row["vote_average"],
            "score": float(scores[0][i])
        })

    return {"query": query, "results": results}
