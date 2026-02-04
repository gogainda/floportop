FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy model files and download large files from GCS
COPY models/ models/
RUN curl -f -o models/index.faiss https://storage.googleapis.com/wagon-01-models/index.faiss && \
    curl -f -o models/movies.pkl https://storage.googleapis.com/wagon-01-models/movies.pkl

# Copy cached embedding model (used by movie_search.py)
COPY cache/model cache/model

# Install Python dependencies (CPU-only PyTorch to save ~2.5GB)
COPY requirements-prod.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements-prod.txt

# Pre-download sentence-transformer models to cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5'); SentenceTransformer('all-MiniLM-L6-v2')"

# --- Runtime stage ---
FROM python:3.12-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libomp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy models from builder
COPY --from=builder /app/models /app/models

# Copy HuggingFace model cache from builder
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface

# Copy cached embedding model for movie_search
COPY --from=builder /app/cache/model /app/cache/model

# Copy application code
COPY . .

EXPOSE 8080 8501

RUN chmod +x start.sh

CMD ["./start.sh"]
