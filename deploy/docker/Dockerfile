FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer reuse.
COPY requirements/prod.lock requirements/prod.lock
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements/prod.lock

# Pre-download embedding models to avoid runtime cold-start downloads.
RUN mkdir -p cache/search_model cache/prediction_model && \
    python -c "from sentence_transformers import SentenceTransformer; \
               m1 = SentenceTransformer('BAAI/bge-base-en-v1.5'); m1.save('cache/search_model'); \
               m2 = SentenceTransformer('all-MiniLM-L6-v2'); m2.save('cache/prediction_model');"

# Copy versioned model artifacts and fetch large binary artifacts from GCS.
COPY models/ models/
RUN curl -f -o models/index.faiss https://storage.googleapis.com/floportop-models/index.faiss && \
    curl -f -o models/movies.pkl https://storage.googleapis.com/floportop-models/movies.pkl

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Runtime Python deps and entrypoints.
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Runtime artifacts prepared in builder.
COPY --from=builder /app/models /app/models
COPY --from=builder /app/cache /app/cache

# Runtime application source only.
COPY apps/api/ apps/api/
COPY apps/frontend/ apps/frontend/
COPY src/floportop/ src/floportop/
COPY start.sh start.sh

ENV API_URL=http://localhost:8080
ENV PYTHONUNBUFFERED=1

RUN chmod +x /app/start.sh

EXPOSE 8080 8501
CMD ["/app/start.sh"]
