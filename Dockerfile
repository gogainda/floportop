FROM python:3.10-slim

WORKDIR /prod

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY api api

# This is the line we are fixing inside the file
COPY floportop floportop
COPY models models
CMD uvicorn api.app:app --host 0.0.0.0 --port $PORT
