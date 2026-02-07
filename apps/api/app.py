"""
Floportop API - Movie Rating Prediction

Endpoints:
- GET /              : HTML + jQuery frontend
- GET /health        : Health check
- GET /predict       : Predict movie rating
- GET /similar-film  : Find similar movies by text query
- POST /rebuild-index : Rebuild the search index
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional


# Import our package
import sys
from pathlib import Path

# Add project roots for local runs (repo root + src).
APP_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = APP_ROOT / "src"
FRONTEND_WEB_DIR = APP_ROOT / "apps" / "frontend" / "web"
sys.path.insert(0, str(APP_ROOT))
sys.path.insert(0, str(SRC_ROOT))

from floportop import predict_movie, load_model
from floportop.preprocessing import load_embedding_model
from floportop.movie_search import load_movie_data, build_index, load_index, load_model as load_similarity_model


app = FastAPI(
    title="Floportop API",
    description="Predict IMDb movie ratings using machine learning",
    version="5.0.0"
)

if FRONTEND_WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_WEB_DIR)), name="static")


@app.on_event("startup")
def startup_event():
    """Load all models and data on startup."""
    print("🚀 Starting up Floportop API...")

    # 1. Load prediction model (v5)
    try:
        load_model()
        print("✅ Prediction model v5 loaded")
    except Exception as e:
        print(f"⚠️ Prediction model failed to load: {e}")

    # 2. Load preprocessing embedding model (all-MiniLM-L6-v2)
    try:
        load_embedding_model()
        print("✅ Preprocessing embedding model loaded")
    except Exception as e:
        print(f"⚠️ Preprocessing embedding model failed to load: {e}")

    # 3. Load movie search resources
    try:
        movies_df = load_movie_data()
        print(f"✅ Movie data loaded ({len(movies_df):,} movies)")

        search_index = load_index()
        if search_index:
            print(f"✅ Search index loaded ({search_index.ntotal:,} items)")
        else:
            print("ℹ️ Search index not found, will need to be built")

        load_similarity_model()
        print("✅ Similarity embedding model loaded")
    except Exception as e:
        print(f"⚠️ Search resources failed to load: {e}")

    print("🏁 API ready and resources cached")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "online", "model_version": "v5"}


@app.get("/", include_in_schema=False)
def root():
    """Serve frontend single-page app."""
    index_file = FRONTEND_WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "online", "model_version": "v5"}


@app.get("/robots.txt", include_in_schema=False)
def robots():
    robots_file = FRONTEND_WEB_DIR / "robots.txt"
    if robots_file.exists():
        return FileResponse(robots_file, media_type="text/plain")
    return "User-agent: *\nAllow: /\n"


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap():
    sitemap_file = FRONTEND_WEB_DIR / "sitemap.xml"
    if sitemap_file.exists():
        return FileResponse(sitemap_file, media_type="application/xml")
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'


@app.get("/predict")
def predict(
    startYear: int,
    runtimeMinutes: int,
    overview: str,
    isAdult: int = 0,
    genres: str = "Drama",
    budget: Optional[float] = None
):
    """
    Predict the rating for a movie.

    Parameters:
    - startYear: Release year (e.g., 2024)
    - runtimeMinutes: Movie length in minutes (e.g., 120)
    - overview: Plot description (REQUIRED). Used for semantic analysis.
    - isAdult: Adult content flag (0 or 1, default 0)
    - genres: Comma-separated genres (e.g., "Action,Adventure,Sci-Fi")
    - budget: Production budget in dollars (optional, will be imputed if not provided)

    Returns:
    - predicted_rating: Predicted IMDb rating (1-10 scale)

    Example:
    /predict?startYear=2024&runtimeMinutes=148&genres=Action,Sci-Fi&overview=A team of astronauts...
    """
    if not overview or not overview.strip():
        raise HTTPException(status_code=400, detail="overview is required and cannot be empty")

    try:
        rating = predict_movie(
            movie_data={
                "startYear": startYear,
                "runtimeMinutes": runtimeMinutes,
                "isAdult": isAdult,
                "genres": genres
            },
            overview=overview,
            budget=budget
        )

        return {
            "predicted_rating": round(rating, 2),
            "input": {
                "startYear": startYear,
                "runtimeMinutes": runtimeMinutes,
                "overview": overview[:100] + "..." if len(overview) > 100 else overview,
                "isAdult": isAdult,
                "genres": genres,
                "budget": budget
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
