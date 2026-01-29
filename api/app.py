"""
Floportop API - Movie Rating Prediction

Endpoints:
- GET /              : Health check
- GET /predict       : Predict movie rating
- GET /similar-film  : Find similar movies by text query
- POST /rebuild-index : Rebuild the search index
"""

from fastapi import FastAPI, HTTPException
from typing import Optional
import numpy as np


# Import our package
import sys
from pathlib import Path

# Add parent directory to path so we can import floportop package
sys.path.insert(0, str(Path(__file__).parent.parent))

from floportop import predict_movie, load_model
from floportop.movie_search import INDEX_FAISS, load_movie_data, build_index, load_index, load_model as load_similarity_model


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
    numVotes: Optional[int] = None,
    isAdult: int = 0,
    genres: str = "Drama"
):
    """
    Predict the rating for a movie.

    Parameters:
    - startYear: Release year (e.g., 2020)
    - runtimeMinutes: Movie length in minutes (e.g., 120)
    - numVotes: Number of IMDb votes (optional - uses median=85 if not provided).
                Omit this for new movies that don't have vote data yet.
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


"""
Floportop API - Movie Rating Prediction

Endpoints:
- GET /              : Health check
- GET /predict       : Predict movie rating
- GET /similar-film  : Find similar movies by text query
- POST /rebuild-index : Rebuild the search index
"""

from fastapi import FastAPI, HTTPException
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path so we can import floportop package
sys.path.insert(0, str(Path(__file__).parent.parent))

from floportop import predict_movie, load_model
from floportop.movie_search import load_movie_data, build_index, load_index, load_model as load_similarity_model


app = FastAPI(
    title="Floportop API",
    description="Predict IMDb movie ratings using machine learning",
    version="2.0.0"
)


@app.on_event("startup")
def startup_event():
    """Load prediction model on startup."""
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
    numVotes: Optional[int] = None,
    isAdult: int = 0,
    genres: str = "Drama"
):
    """
    Predict the rating for a movie.

    Parameters:
    - startYear: Release year (e.g., 2020)
    - runtimeMinutes: Movie length in minutes (e.g., 120)
    - numVotes: Number of IMDb votes (optional - uses median=85 if not provided)
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


@app.get("/similar-film")
def similar_film(query: str, k: int = 10):
    """
    Find similar films based on a text query.

    Parameters:
    - query: Search text (movie title, description, genre, actor, etc.)
    - k: Number of results to return (default 10)

    Returns:
    - results: List of similar movies with scores
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        # Load resources
        search_index = load_index()
        if search_index is None:
            raise HTTPException(
                status_code=503,
                detail="Search index not built. Call POST /rebuild-index first."
            )

        search_model = load_similarity_model()
        movies_df = load_movie_data()

        # Search
        q_emb = search_model.encode([query], normalize_embeddings=True).astype("float32")
        scores, idxs = search_index.search(q_emb, k)

        # Format results
        results = []
        for i, idx in enumerate(idxs[0]):
            row = movies_df.iloc[idx]
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

        return {"query": query, "count": len(results), "results": results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/rebuild-index")
def rebuild_index():
    """
    Rebuild the movie search index.

    This will process movie metadata, generate embeddings, and build FAISS search index.
    Note: This operation can take 10-20 minutes on first run.

    Returns:
    - status: Success message with index stats
    """
    try:
        print("🔨 Building search index...")

        movies_df = load_movie_data()
        search_index = load_index() or build_index(movies_df)

        print("✅ Search index built successfully")

        return {
            "status": "success",
            "message": "Search index built successfully",
            "index_size": search_index.ntotal
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")
