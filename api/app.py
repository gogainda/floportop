"""
Floportop API - Movie Rating Prediction

Endpoints:
- GET /           : Health check
- GET /predict    : Predict movie rating
"""

from fastapi import FastAPI, HTTPException

# Import our package
import sys
from pathlib import Path

# Add parent directory to path so we can import floportop package
sys.path.insert(0, str(Path(__file__).parent.parent))

from floportop import predict_movie, load_model

app = FastAPI(
    title="Floportop API",
    description="Predict IMDb movie ratings using machine learning",
    version="2.0.0"
)

# Load model on startup (caches it for faster predictions)
@app.on_event("startup")
def startup_event():
    load_model()
    print("✅ Model loaded and ready")


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
