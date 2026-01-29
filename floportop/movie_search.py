"""
Simplified Movie Recommendation Engine - Pure Script Version
"""

import pickle
import warnings
import argparse
from pathlib import Path

import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from kaggle.api.kaggle_api_extended import KaggleApi

warnings.filterwarnings("ignore", message="Columns.*mixed types")


# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent

CACHE_DIR = PROJECT_ROOT / "cache"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"

MOVIES_PKL = CACHE_DIR / "movies.pkl"
INDEX_FAISS = MODELS_DIR / "index.faiss"

MODEL_DIR = CACHE_DIR / "model"

KAGGLE_DATASET = "rounakbanik/the-movies-dataset"
MODEL_NAME = "BAAI/bge-base-en-v1.5"

CACHE_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


# ============================================================================
# Helper Functions
# ============================================================================

def download_dataset():
    """Download Kaggle dataset if needed"""
    required_files = {"movies_metadata.csv", "credits.csv", "keywords.csv", "links.csv"}
    existing_files = {f.name for f in DATA_DIR.iterdir()}

    if required_files.issubset(existing_files):
        print("✅ Dataset already downloaded")
        return

    print("⬇️ Downloading dataset...")
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(KAGGLE_DATASET, path=str(DATA_DIR), unzip=True)
    print("✅ Download complete")


def load_csv(filename):
    """Load CSV and print basic info"""
    path = DATA_DIR / filename
    df = pd.read_csv(path, low_memory=False)
    print(f"   📄 {filename}: {len(df):,} rows")
    return df


def parse_json_column(value):
    """Safely parse JSON strings to Python objects"""
    if isinstance(value, str):
        try:
            import ast
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return []
    return value if isinstance(value, (list, dict)) else []


def extract_names(items, key="name"):
    """Extract name field from list of dicts"""
    return [item.get(key, "") for item in items if isinstance(item, dict)]


def join_list(lst):
    """Join list into comma-separated string"""
    return ", ".join(map(str, lst)) if isinstance(lst, list) else str(lst)


def merge_plot_arcs(df):
    """Merge plot arc data from parquet file"""
    plot_arc_path = PROJECT_ROOT / "models" / "wide_df_with_plot_arc.parquet"

    if not plot_arc_path.exists():
        print("⚠️  Plot arc file not found, skipping plot arcs")
        df["plot_arc"] = ""
        return df

    # Normalize IMDb ID column name
    if "imdb_id" in df.columns:
        df = df.assign(tconst=df["imdb_id"])
    elif "imdbId" in df.columns:
        df = df.assign(tconst=df["imdbId"])
    else:
        print("⚠️  No IMDb ID column found, skipping plot arcs")
        df["plot_arc"] = ""
        return df

    # Load and merge plot arcs
    df_plot = (
        pd.read_parquet(plot_arc_path, engine="fastparquet")
        .rename(columns={"imdbId": "tconst"})
        [["tconst", "plot_arc"]]
        .dropna(subset=["plot_arc"])
    )

    df = df.merge(df_plot, on="tconst", how="left").fillna({"plot_arc": ""})
    df = df.drop(columns=["tconst"])

    print(f"   🎭 Merged plot arcs for {df['plot_arc'].astype(bool).sum():,} movies")
    return df


def create_embedding_text(row):
    """Create searchable text from movie features"""
    return "\n".join([
        f"Overview: {row.get('overview', '')}",
        f"Genres: {join_list(row.get('genre_names', []))}",
        f"Keywords: {join_list(row.get('keyword_names', []))}",
        f"Plot Arc: {row.get('plot_arc', '')}",
        f"Cast: {join_list(row.get('cast_top', []))}",
        f"Director: {join_list(row.get('directors', []))}"
    ])


# ============================================================================
# Data Loading
# ============================================================================

def load_movie_data(force_rebuild=False):
    """Load or build movie dataset"""

    # Try loading from cache
    if not force_rebuild and MOVIES_PKL.exists():
        with open(MOVIES_PKL, "rb") as f:
            movies_df = pickle.load(f)
        print(f"✅ Loaded cached data: {len(movies_df):,} movies")
        return movies_df

    # Build from scratch
    print("📦 Building movie dataset...")
    download_dataset()

    # Load raw data
    movies = load_csv("movies_metadata.csv")
    credits = load_csv("credits.csv")
    keywords = load_csv("keywords.csv")
    links = load_csv("links.csv")

    # Clean IDs
    movies = movies[movies["id"].str.isnumeric()].copy()
    movies["id"] = movies["id"].astype(int)
    credits["id"] = credits["id"].astype(int)
    keywords["id"] = keywords["id"].astype(int)
    links["imdbId"] = links["imdbId"].apply(lambda x: f"tt{x:07d}")

    # Merge datasets
    df = (
        movies
        .merge(credits, on="id", how="left")
        .merge(keywords, on="id", how="left")
        .merge(links, left_on="id", right_on="tmdbId", how="left")
    )

    # Merge plot arcs
    df = merge_plot_arcs(df)

    # Parse JSON columns
    for col in ["genres", "keywords", "cast", "crew"]:
        df[col] = df[col].apply(parse_json_column)

    # Extract features
    df["genre_names"] = df["genres"].apply(extract_names)
    df["keyword_names"] = df["keywords"].apply(extract_names)
    df["cast_top"] = df["cast"].apply(lambda x: extract_names(x[:10]))
    df["directors"] = df["crew"].apply(
        lambda x: [item["name"] for item in x if item.get("job") == "Director"]
    )

    # Extract year from release_date
    df["year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year

    # Select final columns
    movies_df = df[[
        "id", "imdbId", "title", "year", "overview",
        "genre_names", "keyword_names", "cast_top", "directors",
        "vote_average", "vote_count", "plot_arc"
    ]].copy()

    # Create embedding text
    movies_df["embedding_text"] = movies_df.apply(create_embedding_text, axis=1)

    print(f"✅ Built dataset: {len(movies_df):,} movies")

    # Save to cache
    with open(MOVIES_PKL, "wb") as f:
        pickle.dump(movies_df, f)

    return movies_df


# ============================================================================
# Model & Index
# ============================================================================

def load_model():
    """Load or download embedding model"""
    if MODEL_DIR.exists():
        return SentenceTransformer(str(MODEL_DIR))

    print("🧠 Downloading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    model.save(str(MODEL_DIR))
    return model


def build_index(movies_df):
    """Build FAISS search index, 1 hour usually"""
    print("🔨 Building search index...")

    model = load_model()
    embeddings = model.encode(
        movies_df["embedding_text"].tolist(),
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True
    ).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_FAISS))
    print(f"✅ Index built: {index.ntotal:,} movies")

    return index


def load_index():
    """Load cached FAISS index"""
    if not INDEX_FAISS.exists():
        return None
    return faiss.read_index(str(INDEX_FAISS))


# ============================================================================
# Search
# ============================================================================

def search(query, k=10, force_rebuild=False):
    """Search for movies matching query"""

    # Load data
    movies_df = load_movie_data(force_rebuild)

    # Load or build index
    if force_rebuild or not INDEX_FAISS.exists():
        index = build_index(movies_df)
    else:
        index = load_index()
        print("⚡ Loaded cached index")

    # Load model and encode query
    model = load_model()
    query_embedding = model.encode([query], normalize_embeddings=True).astype("float32")

    # Search
    scores, indices = index.search(query_embedding, k)

    # Return results
    results = movies_df.iloc[indices[0]].copy()
    results["score"] = scores[0]

    return results


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Movie Recommendation Engine")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--k", type=int, default=10, help="Number of results")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild cache")

    args = parser.parse_args()

    # Search
    results = search(args.query, args.k, args.rebuild)

    # Display results
    print(f"\n🎬 Top {args.k} results for '{args.query}':\n")
    for i, (_, movie) in enumerate(results.iterrows(), 1):
        year = f"({int(movie['year'])})" if pd.notna(movie['year']) else ""
        overview = movie['overview'][:150] + "..." if len(str(movie['overview'])) > 150 else movie['overview']

        print(f"{i}. {movie['title']} {year}")
        print(f"   Score: {movie['score']:.3f}")
        print(f"   {overview}")
        print()
