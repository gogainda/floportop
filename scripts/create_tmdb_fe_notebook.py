
import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()

nb.cells = [
    nbf.v4.new_markdown_cell("""# TMDb Feature Engineering

**Goal:** Generate plot embeddings, apply PCA, and process metadata from the clean TMDb dataset.

**Input:** `data/tmdb_clean.csv`
**Output:** `data/tmdb_wide.csv`

**Steps:**
1. Load Data
2. Generate Plot Embeddings (SentenceTransformer)
3. Apply PCA (20 components)
4. Process Budget & Revenue
5. Export Features"""),

    nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA

# Paths
DATA_DIR = Path('../data')

print("Setup complete!")"""),

    nbf.v4.new_markdown_cell("## 1. Load Data"),

    nbf.v4.new_code_cell("""df = pd.read_csv(DATA_DIR / 'tmdb_clean.csv')
print(f"Loaded {len(df):,} movies")
display(df.head(2))"""),

    nbf.v4.new_markdown_cell("## 2. Generate Embeddings"),

    nbf.v4.new_code_cell("""model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

print("Encoding overviews (this may take a few minutes)...")
# Ensure overviews are strings
overviews = df['overview'].fillna("").astype(str).tolist()
embeddings = model.encode(overviews, show_progress_bar=True, batch_size=64)

print(f"Embeddings shape: {embeddings.shape}")"""),

    nbf.v4.new_markdown_cell("## 3. PCA Reduction"),

    nbf.v4.new_code_cell("""N_COMPONENTS = 20
pca = PCA(n_components=N_COMPONENTS)
embeddings_pca = pca.fit_transform(embeddings)

print(f"Explained variance ratio: {pca.explained_variance_ratio_.sum():.4f}")

# Create PCA dataframe
pca_cols = [f'pca_{i}' for i in range(N_COMPONENTS)]
pca_df = pd.DataFrame(embeddings_pca, columns=pca_cols)
pca_df['imdbId'] = df['imdbId']  # Add ID for merging"""),

    nbf.v4.new_markdown_cell("## 4. Metadata Features"),

    nbf.v4.new_code_cell("""# Log transform budget and revenue
df['log_budget'] = np.log1p(df['budget'])
df['log_revenue'] = np.log1p(df['revenue'])

# Select final metadata columns
meta_cols = ['imdbId', 'log_budget', 'log_revenue', 'director_names']
meta_df = df[meta_cols]"""),

    nbf.v4.new_markdown_cell("## 5. Export"),

    nbf.v4.new_code_cell("""# Merge PCA features with Metadata
final_tmdb_wide = pd.merge(meta_df, pca_df, on='imdbId')

output_path = DATA_DIR / 'tmdb_wide.csv'
final_tmdb_wide.to_csv(output_path, index=False)
print(f"TMDb wide table exported to: {output_path}")
print(f"Shape: {final_tmdb_wide.shape}")""")
]

with open('notebooks/tmdb_feature_engineering.ipynb', 'w') as f:
    nbf.write(nb, f)

print("Notebook created successfully.")
