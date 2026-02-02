# Will This Movie Be Good?

A machine learning tool that predicts a movie's IMDb rating from its metadata and plot description — with the ability to suggest similar existing movies for reference.

## The Problem

It's hard to judge a movie concept early because:

- **Complex Factors**: Success depends on story, genre, and audience taste
- **Human Intuition**: Limited comparisons and subjective biases
- **No Reference Points**: "Great" ideas can be risky without context

## Our Solution

Learn patterns from thousands of past movies to:
1. **Predict** expected audience rating
2. **Find** similar movies for context and benchmarking

All inputs are available before release — making predictions realistic and useful for creators.

## Datasets

| Dataset | Purpose | Key Features |
|---------|---------|--------------|
| [IMDb Dataset](https://www.kaggle.com/datasets/ashirwadsangwan/imdb-dataset) | Core Training Labels | Year, runtime, genres, IMDb score/votes |
| [TMDB Movies Dataset](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset) | NLP Features | Plot overview, budget, revenue, credits |

## Model Inputs

- **Plot Summary** ("overview") - Converted to embeddings via NLP
- **Genres** (Action, Drama, Sci-Fi, etc.)
- **Runtime** + **Release Year**
- **Budget** (optional)

## Deliverables

### Must Have

1. **Rating Prediction (Metadata)**
   - Input: Year, runtime, genres
   - Output: Predicted IMDb rating (e.g., 7.3/10)

2. **Rating + Plot Understanding (NLP)**
   - Enhanced predictions using plot summary, keywords, and tagline
   - Better accuracy through content understanding

3. **Simple Demo UI**
   - Select genre + runtime
   - Paste a plot description
   - Get instant predicted rating

### Stretch Goals

- **Similar Movies Suggestions**: Top 5 most similar existing movies with their ratings as benchmarks
- **Explainability**: Show which factors (keywords, genre, runtime) influenced the prediction
- **Confidence Scoring**: High/Medium/Low confidence levels based on training data coverage

## Example

**Input:**
- Genre: Sci-Fi, Thriller
- Runtime: 118 min
- Plot: "A detective investigates crimes in a city controlled by AI..."

**Output:**
- Predicted Rating: **7.2/10**
- Similar Movies:
  - Blade Runner 2049 (8.0)
  - Minority Report (7.6)
  - Ex Machina (7.7)

## Model Performance

| Metric | Value | Notes |
|--------|-------|-------|
| R² Score | 0.42 | For new movies (no vote data) |
| Training Data | 39k movies | Rich dataset with TMDB plot data |
| Algorithm | GradientBoosting | Best performer across 18 experiments |
| Features | 49 | IMDb metadata + 20 PCA components from plot embeddings |

See `notebooks/jesus/model_v4.ipynb` for full experiment results.

## Tech Stack

- Python 3.12
- pandas / numpy
- scikit-learn (GradientBoostingRegressor)
- sentence-transformers (plot embeddings)
- FastAPI (REST API)
- Streamlit (demo UI)

## Project Structure

```
floportop/
├── data/                    # Datasets (not tracked in git)
│   ├── raw/                 # Original Kaggle files (IMDb + TMDB)
│   ├── processed/           # Clean merged datasets
│   ├── embeddings/          # Plot embeddings
│   └── v1/                  # Legacy intermediate files
├── notebooks/
│   ├── jesus/               # Main data pipeline
│   │   ├── data_pipeline.ipynb        # IMDb + TMDB cleaning & merging
│   │   ├── feature_engineering.ipynb  # Feature creation for modeling
│   │   └── v1/              # Previous notebook versions
│   └── ...                  # Other team members' notebooks
├── floportop/               # Source code (prediction & search)
├── api/                     # FastAPI endpoints
├── frontend/                # Streamlit UI (calls API via HTTP)
├── models/                  # Trained models & FAISS index
├── requirements.txt         # Full dependencies (dev + prod)
├── requirements-prod.txt    # Production only (slim Docker)
├── Dockerfile               # Multi-stage build, CPU-only PyTorch
└── README.md
```
## API

### Running the API

```bash
pip install -e .
cd api
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/predict` | GET | Predict movie rating from metadata |
| `/similar-film` | GET | Find similar movies by text query |

### Examples

**Predict rating (v5):**
```bash
curl "http://localhost:8000/predict?startYear=2024&runtimeMinutes=148&genres=Action,Sci-Fi&overview=A%20team%20of%20astronauts%20travel%20through%20a%20wormhole%20in%20search%20of%20a%20new%20home%20for%20humanity"
```

**Parameters:**
- `startYear` (required): Release year
- `runtimeMinutes` (required): Movie length
- `overview` (required): Plot description - used for semantic analysis
- `genres` (optional): Comma-separated genres (default: "Drama")
- `budget` (optional): Production budget in dollars

**Find similar movies:**
```bash
curl "http://localhost:8000/similar-film?query=dark+sci-fi+time+travel&k=5"
```

Note: The similarity search index is built lazily on the first `/similar-film` call. Subsequent calls use the cached index from `api/cache/`.

## Search engine CLI

```bash
python -m floportop.movie_search "dark sci-fi time travel"
```

## Team

| Name | Role |
|------|------|
| **Igor Novokshonov** | Team Leader |
| Benjamin Steinborn | Developer |
| Jesús López | Developer |
| Kyle Thomas | Developer |
| mucahit TIMAR | Developer |

## 🚀Deployment
## 🚀 Deployment & Operations Guide

### 1. Prerequisites & Container Engine
* **Project ID:** `wagon-bootcamp-479218`
* **Region:** `europe-west1`
* **Engine:** Use **OrbStack** (recommended for Mac) or **Docker Desktop**.
* **Note:** OrbStack is a lightweight, drop-in replacement that uses the same `docker` commands but with better performance on Apple Silicon.

---

### 2. Architecture & Platform Fix
**Critical:** Google Cloud Run requires **`linux/amd64`** images.

* **The Issue:** Apple Silicon Macs (M1/M2/M3) build `arm64` images by default.
* **The Fix:** Use **Remote Builds**. By running `gcloud builds submit`, the image is built natively on Google’s `amd64` servers, bypassing local architecture mismatches.

---

### 3. Deployment Commands
| Task | Command | Description |
| :--- | :--- | :--- |
| **Build & Push** | `make gcp_build` | Remote build on GCP; ensures `amd64` compatibility. |
| **Live Deploy** | `make gcp_deploy` | Launches the latest image to the public Cloud Run URL. |
| **Full Ship** | `make gcp_ship` | Runs both build and deploy in one sequence. |

# Example of a manual deploy with required resources
gcloud run deploy floportop-v2 \
  --image gcr.io/wagon-bootcamp-479218/floportop-v2 \
  --memory 2Gi \
  --set-env-vars KAGGLE_API_TOKEN=your_token_here \
  --region europe-west1

---

### 4. Monitoring & App Access
* **Streamlit UI:** `https://floportop-v2-25462497140.europe-west1.run.app`
* **Features:** Rating prediction + Similar films search (two tabs)
* **Note:** Cold starts take ~60s due to model loading. The container runs both Streamlit (port 8501, exposed) and FastAPI (port 8080, internal).
* **Logs:** View live server logs in the terminal:
  ```bash
  gcloud run services logs read floportop-v2 --region europe-west1

### 5. Troubleshooting: exec format error

If the app deploys but the logs show exec user process caused "exec format error", you have pushed an arm64 image instead of amd64.
Verification: Run docker inspect [IMAGE_NAME] | grep Architecture.The Fix: Re-run make gcp_build or use the manual --platform linux/amd64 flag.

### ⚠️ Critical Deployment Notes
* **Memory Requirements**: This service requires at least **2Gi** of RAM to load the FAISS index and models.
* **Image Size**: Optimized to **~1.8GB** using CPU-only PyTorch and production-only dependencies.
* **Ports**: Container runs API on 8080 (internal) and Streamlit on 8501 (exposed to Cloud Run).
* **FAISS Index**: Downloaded from GCS during build (`https://storage.googleapis.com/floportop-models/index.faiss`).
* **Lazy Imports**: Do not move the Kaggle import back to the top of `movie_search.py`; it must remain inside the function to allow the API to boot.

### Docker Build

```bash
# Build optimized image (CPU-only, ~1.8GB)
docker build -t floportop .

# Run locally (exposes both API and Streamlit UI)
docker run -p 8080:8080 -p 8501:8501 floportop

# Access:
# - Streamlit UI: http://localhost:8501
# - API directly: http://localhost:8080

# Test API endpoints
curl http://localhost:8080/
curl "http://localhost:8080/predict?startYear=2024&runtimeMinutes=120&genres=Action&overview=A%20hero%20saves%20the%20world"
curl "http://localhost:8080/similar-film?query=comedy&k=5"
```

## Le Wagon Data Science & AI Bootcamp

Final project for [Le Wagon](https://www.lewagon.com/) Batch #2201 (2025)

---

*This project demonstrates real-world data processing, NLP, and machine learning — combining prediction with discovery to help creators and fans alike.*
