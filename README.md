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
| [TMDB Movies Dataset](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) | NLP Features | Plot overview, tagline, keywords, credits |

## Model Inputs

- Genres (Action, Drama, Sci-Fi, etc.)
- Runtime + Release Year
- Plot Summary ("overview")
- Keywords & Tagline

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

## Tech Stack

- Python 3.12
- pandas / numpy
- scikit-learn
- NLP libraries (TBD)
- Streamlit (for demo UI)

## Project Structure

```
floportop/
├── data/                    # IMDb & TMDB datasets (not tracked in git)
│   ├── title.basics.tsv
│   ├── title.ratings.tsv
│   └── ...
├── notebooks/               # Individual exploration notebooks
│   ├── notebook_ben.ipynb
│   ├── notebook_igor.ipynb
│   ├── notebook_jesus.ipynb
│   ├── notebook_kyle.ipynb
│   └── notebook_mucahit.ipynb
├── src/                     # Source code (TBD)
├── models/                  # Trained models (TBD)
└── README.md
```
## Search engine

### How to use

```
pip install -e .
python api/movie_search.py "dark sci-fi time travel"
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
The API is hosted on Google Cloud Run.
- Production URL: https://floportop-v2-233992317574.europe-west1.run.app/predict
- Required Inputs: startYear, runtimeMinutes, numVotes.
- Build Engine: Google Cloud Build (Remote).

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
* **The Fix:**

* **Option A**  Use **Remote Builds**. By running `gcloud builds submit`, the image is built natively on Google’s `amd64` servers, bypassing local architecture mismatches.

 * **Option B** Manual Local AMD64 Build
If you must build locally using OrbStack or Docker, explicitly force the AMD64 platform flag:
'bash
docker build --platform linux/amd64 -t gcr.io/wagon-bootcamp-479218/floportop-v2 .

### 3. Deployment Commands
| Task | Command | Description |
| :--- | :--- | :--- |
| **Build & Push** | `make gcp_build` | Remote build on GCP; ensures `amd64` compatibility. |
| **Live Deploy** | `make gcp_deploy` | Launches the latest image to the public Cloud Run URL. |
| **Full Ship** | `make gcp_ship` | Runs both build and deploy in one sequence. |

---

### 4. Monitoring & App Access

* **App URL:** `https://floportop-v2-233992317574.europe-west1.run.app/predict`
* **Documentation:** Append `/docs` to the URL for the interactive Swagger UI.
* **Logs:** View live server logs in the terminal:
  ```bash
  gcloud run services logs read floportop-v2 --region europe-west1

### 5. Troubleshooting
If the app deploys but the logs show exec user process caused "exec format error", you have pushed an arm64 image instead of amd64.

* **App URL:** `https://floportop-v2-233992317574.europe-west1.run.app/predict`
* **Documentation:** Append `/docs` to the URL for the interactive Swagger UI.

* **Logs:** View live server logs in the terminal:


## Le Wagon Data Science & AI Bootcamp

Final project for [Le Wagon](https://www.lewagon.com/) Batch #2201 (2025)

---

*This project demonstrates real-world data processing, NLP, and machine learning — combining prediction with discovery to help creators and fans alike.*
