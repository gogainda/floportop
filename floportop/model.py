"""
Model loading and prediction functions.

Extracted from notebooks/model_training_v2.ipynb
"""

import pickle
import warnings
from pathlib import Path
from typing import Union

import pandas as pd
import numpy as np

# Suppress sklearn version mismatch warnings
warnings.filterwarnings("ignore", message="Trying to unpickle estimator")

from .preprocessing import preprocess_single_movie


# Default model path
DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "models" / "model_v2.pkl"

# Cache for loaded model
_model_cache = {}


def load_model(model_path: str = None):
    """
    Load the trained model from disk.

    Args:
        model_path: Path to the .pkl file. If None, uses default model.

    Returns:
        Trained sklearn pipeline.
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
        features: DataFrame with preprocessed features (from preprocess_features
                  or preprocess_single_movie)
        model: Trained model. If None, loads default model.

    Returns:
        Array of predicted ratings.
    """
    if model is None:
        model = load_model()

    predictions = model.predict(features)
    return predictions


def predict_movie(movie_data: dict, model=None) -> float:
    """
    Predict rating for a single movie.

    Args:
        movie_data: Dict with movie attributes:
            - startYear: int (e.g., 2020)
            - runtimeMinutes: int (e.g., 120)
            - numVotes: int (e.g., 5000)
            - isAdult: int (0 or 1)
            - genres: str (e.g., "Action,Adventure,Sci-Fi")

    Returns:
        Predicted rating (float between 1-10)

    Example:
        >>> predict_movie({
        ...     "startYear": 2020,
        ...     "runtimeMinutes": 148,
        ...     "numVotes": 500000,
        ...     "isAdult": 0,
        ...     "genres": "Action,Adventure,Sci-Fi"
        ... })
        7.23
    """
    if model is None:
        model = load_model()

    # Preprocess the input
    features = preprocess_single_movie(movie_data)

    # Predict
    prediction = model.predict(features)[0]

    # Clip to valid rating range
    prediction = np.clip(prediction, 1.0, 10.0)

    return float(prediction)
