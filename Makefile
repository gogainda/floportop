# Project Variables
GCP_PROJECT_ID ?= $(shell gcloud config get-value project 2>/dev/null)
DOCKER_IMAGE_NAME ?= floportop-v2
REGION ?= europe-west1

.PHONY: install run_api docker_build check_gcp gcp_build gcp_deploy gcp_ship

# --- Local Commands ---

install:
	pip install -r requirements/dev.txt

run_api:
	PYTHONPATH=src:. uvicorn apps.api.app:app --reload

docker_build:
	docker build -f deploy/docker/Dockerfile -t floportop:local .

# --- Google Cloud Commands ---

check_gcp:
	@command -v gcloud >/dev/null 2>&1 || (echo "gcloud CLI not found. Install it from https://cloud.google.com/sdk/docs/install" >&2; exit 1)
	@test -n "$(GCP_PROJECT_ID)" && [ "$(GCP_PROJECT_ID)" != "(unset)" ] && [ "$(GCP_PROJECT_ID)" != "unset" ] || (echo "GCP_PROJECT_ID is not set. Run 'gcloud config set project <id>' or pass GCP_PROJECT_ID=..." >&2; exit 1)

# 1. Build the image on Google Cloud (uses Kaniko layer caching)
gcp_build: check_gcp
	gcloud builds submit --project $(GCP_PROJECT_ID) --config deploy/cloudbuild.yaml .

# 2. Deploy the image to a live URL
gcp_deploy: check_gcp
	gcloud run deploy $(DOCKER_IMAGE_NAME) --project $(GCP_PROJECT_ID) --image gcr.io/$(GCP_PROJECT_ID)/$(DOCKER_IMAGE_NAME) --platform managed --region $(REGION) --allow-unauthenticated --memory 2Gi --port 8501

# 3. Do both in one go
gcp_ship: gcp_build gcp_deploy
