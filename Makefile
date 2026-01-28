# Project Variables
GCP_PROJECT_ID=wagon-bootcamp-479218
DOCKER_IMAGE_NAME=floportop-v2
REGION=europe-west1

# --- Local Commands ---

install:
	pip install -r requirements.txt

run_api:
	uvicorn api.fast:app --reload

# --- Google Cloud Commands ---

# 1. Build the image on Google Cloud (The 19-minute process)
gcp_build:
	gcloud builds submit --tag gcr.io/$(GCP_PROJECT_ID)/$(DOCKER_IMAGE_NAME) .

# 2. Deploy the image to a live URL
gcp_deploy:
	gcloud run deploy --image gcr.io/$(GCP_PROJECT_ID)/$(DOCKER_IMAGE_NAME) --platform managed --region $(REGION) --allow-unauthenticated

# 3. Do both in one go
gcp_ship: gcp_build gcp_deploy
