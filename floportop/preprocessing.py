"""
Feature engineering and preprocessing functions.

Extracted from notebooks/eda_feature_engineering.ipynb
"""

import pandas as pd
import numpy as np
from pathlib import Path


# Genres that passed the 1000 occurrence threshold
VALID_GENRES = [
    'Drama', 'Comedy', 'Documentary', 'Romance', 'Action', 'Crime',
    'Thriller', 'Horror', 'Adventure', 'Mystery', 'Family', 'Biography',
    'Fantasy', 'History', 'Music', 'Sci-Fi', 'Musical', 'War',
    'Animation', 'Western', 'Sport', 'Adult'
]

CURRENT_YEAR = 2026
RUNTIME_CAP = 300  # minutes

# Median numVotes from training data (see model_v3_jesus.ipynb Section 8)
# Used for imputation when numVotes is not provided (e.g., predicting new movies)
# Why median? numVotes is heavily right-skewed; median is robust to outliers
MEDIAN_NUM_VOTES = 85
HIT_THRESHOLD = 648  # 80th percentile from training data


def load_clean_data(filepath: str = None) -> pd.DataFrame:
    """
    Load the clean movies dataset.

    Args:
        filepath: Path to movies_clean.csv. If None, uses default path.

    Returns:
        DataFrame with clean movie data.
    """
    if filepath is None:
        # Default path relative to package
        filepath = Path(__file__).parent.parent / "data" / "movies_clean.csv"

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
    # Convert to numeric (runtimeMinutes is stored as string in movies_clean.csv)
    df['runtimeMinutes'] = pd.to_numeric(df['runtimeMinutes'], errors='coerce')
    df['runtimeMinutes_capped'] = df['runtimeMinutes'].clip(upper=cap)
    return df


def create_popularity_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add log-transformed votes and hit flag."""
    df = df.copy()

    # Log transform for skewed vote distribution
    df['log_numVotes'] = np.log1p(df['numVotes'])

    # Hit flag: top 20% by votes
    percentile_80 = df['numVotes'].quantile(0.80)
    df['hit'] = (df['numVotes'] >= percentile_80).astype(int)

    return df


def create_budget_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add budget features (log transform and binary flag)."""
    df = df.copy()
    
    # Ensure budget is numeric
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

    # Genre count
    df['genre_count'] = df['genres'].str.split(',').str.len()

    # One-hot encode each genre
    for genre in genres:
        df[f'Genre_{genre}'] = df['genres'].str.contains(genre, regex=False).astype(int)

    return df


def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all feature engineering transformations.

    This is the main function that converts raw data to model-ready features.

    Args:
        df: Raw movie DataFrame (from movies_clean.csv)

    Returns:
        DataFrame with all engineered features, ready for modeling.
    """
    # Apply transformations in order
    df = create_temporal_features(df)
    df = cap_runtime(df)
    df = create_popularity_features(df)
    df = create_genre_features(df)

    # Drop rows with missing values (typically ~22 rows)
    df = df.dropna(subset=['startYear'])

    # Select and order columns for modeling
    feature_columns = [
        'averageRating',  # Target
        'isAdult', 'startYear', 'numVotes', 'genre_count', 'decade',
        'movie_age', 'runtimeMinutes_capped', 'log_numVotes', 'hit',
    ] + [f'Genre_{g}' for g in VALID_GENRES]

    return df[feature_columns]


def preprocess_single_movie(movie_data: dict) -> pd.DataFrame:
    """
    Preprocess a single movie for prediction.

    Args:
        movie_data: Dict with keys: startYear, runtimeMinutes, numVotes (optional),
                    isAdult, genres (comma-separated string)

                    If numVotes is None or not provided, uses MEDIAN_NUM_VOTES.
                    This handles the case of predicting ratings for new movies
                    that don't have vote data yet.

    Returns:
        DataFrame with one row, ready for model.predict()
    """
    df = pd.DataFrame([movie_data])

    # Handle missing numVotes with median imputation
    # See model_v3_jesus.ipynb Section 8 for justification
    if 'numVotes' not in df.columns or df['numVotes'].isna().any() or df['numVotes'].iloc[0] is None:
        df['numVotes'] = MEDIAN_NUM_VOTES

    # Apply transformations
    df['movie_age'] = CURRENT_YEAR - df['startYear']
    df['decade'] = (df['startYear'] // 10 * 10)
    df['runtimeMinutes_capped'] = df['runtimeMinutes'].clip(upper=RUNTIME_CAP)
    df['log_numVotes'] = np.log1p(df['numVotes'])

    # Hit flag (using threshold from training data)
    df['hit'] = (df['numVotes'] >= HIT_THRESHOLD).astype(int)

    # Genre count and one-hot encoding
    df['genre_count'] = df['genres'].str.split(',').str.len()
    for genre in VALID_GENRES:
        df[f'Genre_{genre}'] = df['genres'].str.contains(genre, regex=False).astype(int)

    # Select feature columns (exclude target)
    feature_columns = [
        'isAdult', 'startYear', 'numVotes', 'genre_count', 'decade',
        'movie_age', 'runtimeMinutes_capped', 'log_numVotes', 'hit',
    ] + [f'Genre_{g}' for g in VALID_GENRES]

    return df[feature_columns]
