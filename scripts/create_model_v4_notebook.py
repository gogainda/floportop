
import nbformat as nbf

nb = nbf.v4.new_notebook()

nb.cells = [
    nbf.v4.new_markdown_cell("""# Model Training v4 (Combined Datasets)

**Goal:** Train and compare models using features from both IMDb and TMDb.

**Inputs:**
- `data/movies_wide.csv` (IMDb features, ~298k movies)
- `data/tmdb_wide.csv` (TMDb features + Plot PCA, ~44k movies)

**Strategy:**
1. Merge datasets (Left Join on IMDb ID).
2. Experiment 1: Baseline (IMDb features only).
3. Experiment 2: Add Plot PCA features (fill missing with 0).
4. Experiment 3: Add Budget/Revenue features."""),

    nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

# Paths
DATA_DIR = Path('../data')

print("Setup complete!")"""),

    nbf.v4.new_markdown_cell("## 1. Load and Merge Data"),

    nbf.v4.new_code_cell("""# Load datasets
imdb = pd.read_csv(DATA_DIR / 'movies_clean.csv') # Need tconst for merging
imdb_wide = pd.read_csv(DATA_DIR / 'movies_wide.csv')
tmdb_wide = pd.read_csv(DATA_DIR / 'tmdb_wide.csv')

print(f"IMDb wide shape: {imdb_wide.shape}")
print(f"TMDb wide shape: {tmdb_wide.shape}")

# Note: movies_wide.csv lost tconst, so we need to be careful.
# Assuming row alignment is preserved from movies_clean.csv is risky.
# Better approach: We'll reconstruct the full dataset using movies_clean as the anchor.

# Let's check if movies_wide has the same length as movies_clean
if len(imdb) != len(imdb_wide):
    print("Warning: Length mismatch!")
else:
    print("Lengths match. Attaching tconst to imdb_wide...")
    imdb_wide['tconst'] = imdb['tconst']

# Merge TMDb features
# Left join: Keep all IMDb movies, add TMDb info where available
merged = imdb_wide.merge(tmdb_wide, left_on='tconst', right_on='imdbId', how='left')

# Fill missing TMDb features with 0
# Identify new columns (those from tmdb_wide)
tmdb_cols = [c for c in tmdb_wide.columns if c != 'imdbId']
merged[tmdb_cols] = merged[tmdb_cols].fillna(0)

print(f"Merged dataset shape: {merged.shape}")
display(merged.head())"""),

    nbf.v4.new_markdown_cell("## 2. Define Feature Sets"),

    nbf.v4.new_code_cell("""# Identify feature groups
target = 'averageRating'
ignore_cols = ['tconst', 'imdbId', 'director_names', target] # director_names needs processing if we want to use it

# 1. Base Features (from IMDb)
base_features = [c for c in imdb_wide.columns if c not in ignore_cols and c != 'tconst']

# 2. PCA Features
pca_features = [c for c in merged.columns if c.startswith('pca_')]

# 3. Budget/Revenue
money_features = ['log_budget', 'log_revenue']

print(f"Base features: {len(base_features)}")
print(f"PCA features: {len(pca_features)}")
print(f"Money features: {len(money_features)}")"""),

    nbf.v4.new_markdown_cell("## 3. Train/Test Split"),

    nbf.v4.new_code_cell("""# Drop rows with NaN in target or base features (should be none for base)
df_model = merged.dropna(subset=[target] + base_features)

X = df_model.drop(columns=[target, 'tconst', 'imdbId', 'director_names'])
y = df_model[target]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

print(f"Train size: {len(X_train):,}")
print(f"Test size: {len(X_test):,}")"""),

    nbf.v4.new_markdown_cell("## 4. Experiment 1: Baseline (IMDb Only)"),

    nbf.v4.new_code_cell("""print("Training Baseline Model...")
rf_base = RandomForestRegressor(n_estimators=50, max_depth=10, n_jobs=-1, random_state=42)
rf_base.fit(X_train[base_features], y_train)

y_pred_base = rf_base.predict(X_test[base_features])
r2_base = r2_score(y_test, y_pred_base)
mae_base = mean_absolute_error(y_test, y_pred_base)

print(f"Baseline R²: {r2_base:.4f}")
print(f"Baseline MAE: {mae_base:.4f}")"""),

    nbf.v4.new_markdown_cell("## 5. Experiment 2: Baseline + Plot PCA"),

    nbf.v4.new_code_cell("""features_v2 = base_features + pca_features
print(f"Training Model with Plots ({len(features_v2)} features)...")

rf_pca = RandomForestRegressor(n_estimators=50, max_depth=10, n_jobs=-1, random_state=42)
rf_pca.fit(X_train[features_v2], y_train)

y_pred_pca = rf_pca.predict(X_test[features_v2])
r2_pca = r2_score(y_test, y_pred_pca)
mae_pca = mean_absolute_error(y_test, y_pred_pca)

print(f"PCA Model R²: {r2_pca:.4f}")
print(f"PCA Model MAE: {mae_pca:.4f}")"""),

    nbf.v4.new_markdown_cell("## 6. Experiment 3: Baseline + Plot PCA + Budget"),

    nbf.v4.new_code_cell("""features_v3 = base_features + pca_features + money_features
print(f"Training Full Model ({len(features_v3)} features)...")

rf_full = RandomForestRegressor(n_estimators=50, max_depth=10, n_jobs=-1, random_state=42)
rf_full.fit(X_train[features_v3], y_train)

y_pred_full = rf_full.predict(X_test[features_v3])
r2_full = r2_score(y_test, y_pred_full)
mae_full = mean_absolute_error(y_test, y_pred_full)

print(f"Full Model R²: {r2_full:.4f}")
print(f"Full Model MAE: {mae_full:.4f}")"""),

    nbf.v4.new_markdown_cell("## Summary of Results"),

    nbf.v4.new_code_cell("""results = pd.DataFrame({
    'Model': ['Baseline', 'Base + Plots', 'Base + Plots + Budget'],
    'R2': [r2_base, r2_pca, r2_full],
    'MAE': [mae_base, mae_pca, mae_full]
})
results['Improvement'] = results['R2'] - results.iloc[0]['R2']
display(results)""")
]

with open('notebooks/model_v4_jesus.ipynb', 'w') as f:
    nbf.write(nb, f)

print("Notebook created successfully.")
