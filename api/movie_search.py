import os
import ast
import pickle
import argparse

import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# ======================
# Config
# ======================
CACHE_DIR = "cache"
MOVIES_PKL = os.path.join(CACHE_DIR, "movies.pkl")
INDEX_FAISS = os.path.join(CACHE_DIR, "index.faiss")
MODEL_DIR = os.path.join(CACHE_DIR, "model")

os.makedirs(CACHE_DIR, exist_ok=True)

# ======================
# Storage helpers
# ======================
def save_pickle(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_pickle(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def save_index(index):
    faiss.write_index(index, INDEX_FAISS)


def load_index():
    if not os.path.exists(INDEX_FAISS):
        return None
    return faiss.read_index(INDEX_FAISS)


# ======================
# Data loading
# ======================
def load_csv(file_path):
    return kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "rounakbanik/the-movies-dataset",
        file_path,
    )


def load_movie_data(force_reload=False):
    if not force_reload:
        cached = load_pickle(MOVIES_PKL)
        if cached is not None:
            print("✅ Using cached movies dataframe")
            return cached

    print("⬇️ Loading Kaggle movie dataset...")

    movies = load_csv("movies_metadata.csv")
    credits = load_csv("credits.csv")
    keywords = load_csv("keywords.csv")
    links = load_csv("links.csv")

    movies = movies[movies["id"].str.isnumeric()]
    movies["id"] = movies["id"].astype(int)
    credits["id"] = credits["id"].astype(int)
    keywords["id"] = keywords["id"].astype(int)
    links["imdbId"] = links["imdbId"].apply(lambda x: f"tt{x:07d}")

    df = (
        movies.merge(credits, on="id", how="left")
        .merge(keywords, on="id", how="left")
        .merge(links, left_on="id", right_on="tmdbId", how="left")
    )

    def parse_json(col):
        return col.apply(lambda x: ast.literal_eval(x) if pd.notna(x) else [])

    for col in ["genres", "keywords", "cast", "crew"]:
        df[col] = parse_json(df[col])

    df["genre_names"] = df["genres"].apply(lambda xs: [x["name"] for x in xs])
    df["keyword_names"] = df["keywords"].apply(lambda xs: [x["name"] for x in xs])
    df["cast_top"] = df["cast"].apply(lambda xs: [x["name"] for x in xs[:10]])
    df["directors"] = df["crew"].apply(
        lambda xs: [x["name"] for x in xs if x["job"] == "Director"]
    )

    movies_df = df[
        [
            "id",
            "imdbId",
            "title",
            "overview",
            "genre_names",
            "keyword_names",
            "cast_top",
            "directors",
            "vote_average",
            "vote_count",
        ]
    ].reset_index(drop=True)

    movies_df["embedding_text"] = (
        "Title: " + movies_df["title"].fillna("") + "\n"
        "Overview: " + movies_df["overview"].fillna("") + "\n"
        "Genres: " + movies_df["genre_names"].apply(lambda x: ", ".join(x)) + "\n"
        "Keywords: " + movies_df["keyword_names"].apply(lambda x: ", ".join(x)) + "\n"
        "Cast: " + movies_df["cast_top"].apply(lambda x: ", ".join(x)) + "\n"
        "Director: " + movies_df["directors"].apply(lambda x: ", ".join(x))
    )

    save_pickle(movies_df, MOVIES_PKL)
    print("💾 Cached movies dataframe")

    return movies_df


# ======================
# Model / index
# ======================
def get_model():
    if os.path.exists(MODEL_DIR):
        return SentenceTransformer(MODEL_DIR)

    print("🧠 Downloading sentence transformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    model.save(MODEL_DIR)
    return model


def build_index(movies_df):
    print("🔨 Building embeddings + FAISS index...")

    model = get_model()
    embeddings = model.encode(
        movies_df["embedding_text"].tolist(),
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    save_index(index)
    print(f"✅ Index built with {index.ntotal} vectors")

    return index


def ensure_index():
    movies_df = load_movie_data()
    index = load_index()

    if index is None:
        index = build_index(movies_df)
    else:
        print("⚡ Using cached FAISS index")

    return movies_df, index


# ======================
# Search
# ======================
def search(query, k=10):
    movies_df, index = ensure_index()
    model = get_model()

    q_emb = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, idxs = index.search(q_emb, k)

    results = movies_df.iloc[idxs[0]].copy()
    results["score"] = scores[0]
    return results


# ======================
# CLI
# ======================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--rebuild", action="store_true")

    args = parser.parse_args()

    if args.rebuild:
        load_movie_data(force_reload=True)
        build_index(load_pickle(MOVIES_PKL))

    results = search(args.query, args.k)

    print("\n🎬 Top results:\n")
    for _, row in results.iterrows():
        print(f"{row['title']}  (score={row['score']:.3f})")
