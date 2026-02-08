"""
Feature engineering and preprocessing functions.

Model v5: Uses PCA embeddings from overview, optional budget, no vote features.
"""

import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache

from .paths import MODELS_DIR, CACHE_DIR, DATA_DIR

# Constants
CURRENT_YEAR = 2026
RUNTIME_CAP = 300  # minutes
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
N_PCA_COMPONENTS = 20

# Genres that passed the 1000 occurrence threshold
VALID_GENRES = [
    'Drama', 'Comedy', 'Documentary', 'Romance', 'Action', 'Crime',
    'Thriller', 'Horror', 'Adventure', 'Mystery', 'Family', 'Biography',
    'Fantasy', 'History', 'Music', 'Sci-Fi', 'Musical', 'War',
    'Animation', 'Western', 'Sport', 'Adult'
]

# PCA column names
PCA_COLS = [f"pca_{i}" for i in range(N_PCA_COMPONENTS)]

# Final feature order for model v5 (49 features)
FEATURE_ORDER_V5 = [
    # IMDb Core (5 features)
    "movie_age", "decade", "runtimeMinutes_capped", "genre_count", "isAdult",
    # Genres (22 features)
    "Genre_Drama", "Genre_Comedy", "Genre_Documentary", "Genre_Romance",
    "Genre_Action", "Genre_Crime", "Genre_Thriller", "Genre_Horror",
    "Genre_Adventure", "Genre_Mystery", "Genre_Family", "Genre_Biography",
    "Genre_Fantasy", "Genre_History", "Genre_Music", "Genre_Sci-Fi",
    "Genre_Musical", "Genre_War", "Genre_Animation", "Genre_Western",
    "Genre_Sport", "Genre_Adult",
    # PCA Embeddings (20 features)
] + PCA_COLS + [
    # Budget (2 features)
    "log_budget", "has_budget"
]

# Paths to model artifacts
PREDICTION_MODEL_DIR = CACHE_DIR / "prediction_model"
PCA_PATH = MODELS_DIR / "pca_transformer.pkl"
BUDGET_MEDIANS_PATH = MODELS_DIR / "budget_medians.json"


# Cached loaders for heavy objects
_pca_transformer = None
_embedding_model = None
_budget_medians = None


def load_pca_transformer():
    """Load the fitted PCA transformer from disk."""
    global _pca_transformer
    if _pca_transformer is None:
        with open(PCA_PATH, "rb") as f:
            _pca_transformer = pickle.load(f)
    return _pca_transformer


def load_embedding_model():
    """Load the SentenceTransformer model (lazy, cached)."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        if PREDICTION_MODEL_DIR.exists():
            _embedding_model = SentenceTransformer(str(PREDICTION_MODEL_DIR))
        else:
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def load_budget_medians():
    """Load budget medians by decade for imputation."""
    global _budget_medians
    if _budget_medians is None:
        with open(BUDGET_MEDIANS_PATH, "r") as f:
            _budget_medians = json.load(f)
    return _budget_medians


def create_pca_features(overview: str) -> np.ndarray:
    """
    Generate PCA features from a movie overview text.

    Args:
        overview: Movie plot description text

    Returns:
        numpy array of shape (20,) with PCA features
    """
    model = load_embedding_model()
    pca = load_pca_transformer()

    # Generate embedding (384-dim)
    embedding = model.encode([overview], show_progress_bar=False)

    # Transform to PCA space (20-dim)
    pca_features = pca.transform(embedding)[0]

    return pca_features


def create_budget_features(budget: float, decade: int) -> tuple:
    """
    Create budget features with decade-based imputation.

    Args:
        budget: Budget in dollars (None or 0 to impute)
        decade: Movie decade (e.g., 2020) for imputation lookup

    Returns:
        tuple: (log_budget, has_budget)
    """
    budget_medians = load_budget_medians()

    if budget is not None and budget > 0:
        log_budget = np.log1p(budget)
        has_budget = 1
    else:
        # Impute with decade median, fall back to default
        decade_key = str(int(decade))
        log_budget = budget_medians.get(decade_key, budget_medians.get("default", 16.0))
        has_budget = 0

    return log_budget, has_budget


def preprocess_single_movie(
    movie_data: dict,
    overview: str,
    budget: float = None
) -> pd.DataFrame:
    """
    Preprocess a single movie for prediction (Model v5).

    Args:
        movie_data: Dict with keys:
            - startYear: int (e.g., 2020)
            - runtimeMinutes: int (e.g., 120)
            - isAdult: int (0 or 1)
            - genres: str (e.g., "Action,Adventure,Sci-Fi")
        overview: Movie plot description (REQUIRED, non-empty string)
        budget: Budget in dollars (optional, will be imputed if not provided)

    Returns:
        DataFrame with one row containing 49 features, ready for model.predict()

    Raises:
        ValueError: If overview is empty or None
    """
    # Validate overview
    if not overview or not overview.strip():
        raise ValueError("overview is required and cannot be empty")

    df = pd.DataFrame([movie_data])

    # Temporal features
    df['movie_age'] = CURRENT_YEAR - df['startYear']
    df['decade'] = (df['startYear'] // 10 * 10)

    # Runtime
    df['runtimeMinutes_capped'] = df['runtimeMinutes'].clip(upper=RUNTIME_CAP)

    # Genre features
    df['genre_count'] = df['genres'].str.split(',').str.len()
    for genre in VALID_GENRES:
        df[f'Genre_{genre}'] = df['genres'].str.contains(genre, regex=False).astype(int)

    # PCA features from overview
    pca_features = create_pca_features(overview)
    for i, col in enumerate(PCA_COLS):
        df[col] = pca_features[i]

    # Budget features (with imputation)
    decade = int(df['decade'].iloc[0])
    log_budget, has_budget = create_budget_features(budget, decade)
    df['log_budget'] = log_budget
    df['has_budget'] = has_budget

    # Return features in correct order
    return df[FEATURE_ORDER_V5]


# ============================================================================
# Legacy functions for batch processing (used in training)
# ============================================================================

def load_clean_data(filepath: str = None) -> pd.DataFrame:
    """
    Load the clean movies dataset.

    Args:
        filepath: Path to movies_clean.csv. If None, uses default path.

    Returns:
        DataFrame with clean movie data.
    """
    if filepath is None:
        filepath = DATA_DIR / "movies_clean.csv"

    df = pd.read_csv(filepath)
    return df


def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add movie_age and decade features."""
    df = df.copy()
    df['movie_age'] = CURRENT_YEAR - df['startYear']
    df['decade'] = (df['startYear'] // 10 * 10).astype('Int64')
    return df


def cap_runtime(df: pd.DataFrame, cap: int = RUNTIME_CAP) -> pd.DataFrame:
    """Cap runtime at specified maximum to handle outliers."""
    df = df.copy()
    df['runtimeMinutes'] = pd.to_numeric(df['runtimeMinutes'], errors='coerce')
    df['runtimeMinutes_capped'] = df['runtimeMinutes'].clip(upper=cap)
    return df


def create_budget_features_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Add budget features (log transform and binary flag)."""
    df = df.copy()

    if 'budget' in df.columns:
        df['budget'] = pd.to_numeric(df['budget'], errors='coerce').fillna(0)
        df['log_budget'] = np.log1p(df['budget'])
        df['has_budget'] = (df['budget'] > 0).astype(int)

    return df


def create_genre_features(df: pd.DataFrame, genres: list = None) -> pd.DataFrame:
    """One-hot encode genres."""
    df = df.copy()

    if genres is None:
        genres = VALID_GENRES

    df['genre_count'] = df['genres'].str.split(',').str.len()

    for genre in genres:
        df[f'Genre_{genre}'] = df['genres'].str.contains(genre, regex=False).astype(int)

    return df


def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all feature engineering transformations for batch processing.

    This is used for training data preparation.

    Args:
        df: Raw movie DataFrame

    Returns:
        DataFrame with all engineered features.
    """
    df = create_temporal_features(df)
    df = cap_runtime(df)
    df = create_genre_features(df)
    df = create_budget_features_batch(df)

    df = df.dropna(subset=['startYear'])

    return df
