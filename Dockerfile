FROM python:3.10-slim

WORKDIR /prod

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Now copy your local code/models into the image
COPY floportop floportop
COPY api api
COPY models models

# Use the JSON format to make Docker happy
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080"]
