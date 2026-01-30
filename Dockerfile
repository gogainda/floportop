FROM python:3.12-slim

# Install C++ scaling libraries for PCA/Embeddings
RUN apt-get update && apt-get install -y \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole project (including the new heavy models)
COPY . .

# Set Port for Cloud Run
EXPOSE 8080

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080"]
