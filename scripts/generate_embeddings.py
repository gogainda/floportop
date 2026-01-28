
import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import sys
import os

# Add project root to path so we can import floportop
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from floportop.preprocessing import load_clean_data

DATA_DIR = Path('data')
EMBEDDINGS_FILE = DATA_DIR / 'plot_embeddings.npy'
MERGED_DATA_FILE = DATA_DIR / 'merged_imdb_tmdb.csv'

def main():
    print("Starting embedding generation process...")
    
    # 1. Load Data
    print("Loading data...")
    imdb = load_clean_data()
    tmdb_features = pd.read_csv(DATA_DIR / 'tmdb_features.csv')
    
    print(f"IMDb movies: {len(imdb)}")
    print(f"TMDb features: {len(tmdb_features)}")

    # 2. Merge Data
    print("Merging datasets...")
    merged = imdb.merge(
        tmdb_features[['imdbId', 'overview', 'budget', 'revenue', 'director_names']],
        left_on='tconst',
        right_on='imdbId',
        how='inner'
    )
    print(f"Merged dataset: {len(merged)} movies")
    
    # Save merged data
    merged.to_csv(MERGED_DATA_FILE, index=False)
    print(f"Saved merged data to {MERGED_DATA_FILE}")

    # 3. Generate Embeddings
    if EMBEDDINGS_FILE.exists():
        print(f"Embeddings file already exists at {EMBEDDINGS_FILE}. Skipping generation.")
        return

    print("Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print(f"Generating embeddings for {len(merged)} movies...")
    overviews_list = merged['overview'].fillna("").tolist()
    
    embeddings = model.encode(
        overviews_list,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    
    embeddings = np.array(embeddings, dtype='float32')
    
    # 4. Save Embeddings
    np.save(EMBEDDINGS_FILE, embeddings)
    print(f"Saved embeddings to {EMBEDDINGS_FILE} shape={embeddings.shape}")
    print("Done!")

if __name__ == "__main__":
    main()
