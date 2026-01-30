"""
Model loading and prediction functions.

Model v5: Uses PCA embeddings from overview, optional budget, no vote features.
"""

import pickle
import warnings
from pathlib import Path
from typing import Union, Optional

import pandas as pd
import numpy as np

# Suppress sklearn version mismatch warnings
warnings.filterwarnings("ignore", message="Trying to unpickle estimator")

from .preprocessing import preprocess_single_movie


# Default model path (v5)
DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "models" / "model_v5.pkl"

# Cache for loaded model
_model_cache = {}


def load_model(model_path: str = None):
    """
    Load the trained model from disk.

    Args:
        model_path: Path to the .pkl file. If None, uses default model (v5).

    Returns:
        Trained sklearn model (GradientBoostingRegressor).
    """
    if model_path is None:
        model_path = DEFAULT_MODEL_PATH

    model_path = str(model_path)

    # Return cached model if available
    if model_path in _model_cache:
        return _model_cache[model_path]

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    _model_cache[model_path] = model
    return model


def predict(features: pd.DataFrame, model=None) -> np.ndarray:
    """
    Make predictions using the trained model.

    Args:
        features: DataFrame with preprocessed features (from preprocess_single_movie)
        model: Trained model. If None, loads default model.

    Returns:
        Array of predicted ratings.
    """
    if model is None:
        model = load_model()

    predictions = model.predict(features)
    return predictions


def predict_movie(
    movie_data: dict,
    overview: str,
    budget: Optional[float] = None,
    model=None
) -> float:
    """
    Predict rating for a single movie.

    Args:
        movie_data: Dict with movie attributes:
            - startYear: int (e.g., 2024)
            - runtimeMinutes: int (e.g., 120)
            - isAdult: int (0 or 1)
            - genres: str (e.g., "Action,Adventure,Sci-Fi")
        overview: Movie plot description (REQUIRED, non-empty string).
                  This is used to generate semantic features via embeddings.
        budget: Production budget in dollars (optional).
                If not provided, will be imputed based on decade.
        model: Pre-loaded model (optional, for efficiency in batch calls)

    Returns:
        Predicted rating (float between 1-10)

    Raises:
        ValueError: If overview is empty or None

    Example:
        >>> predict_movie(
        ...     movie_data={
        ...         "startYear": 2024,
        ...         "runtimeMinutes": 148,
        ...         "isAdult": 0,
        ...         "genres": "Action,Adventure,Sci-Fi"
        ...     },
        ...     overview="A team of astronauts embarks on a dangerous mission...",
        ...     budget=200_000_000
        ... )
        7.23
    """
    if model is None:
        model = load_model()

    # Preprocess the input (includes overview embedding and budget imputation)
    features = preprocess_single_movie(movie_data, overview, budget)

    # Predict
    prediction = model.predict(features)[0]

    # Clip to valid rating range
    prediction = np.clip(prediction, 1.0, 10.0)

    return float(prediction)
