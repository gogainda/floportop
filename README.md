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

**Predict rating:**
```bash
curl "http://localhost:8000/predict?startYear=2024&runtimeMinutes=120&numVotes=50000&genres=Action,Sci-Fi"
```

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

## Le Wagon Data Science & AI Bootcamp

Final project for [Le Wagon](https://www.lewagon.com/) Batch #2201 (2025)

---

*This project demonstrates real-world data processing, NLP, and machine learning — combining prediction with discovery to help creators and fans alike.*
