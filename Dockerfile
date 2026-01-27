FROM python:3.10-slim

WORKDIR /prod

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY api api

# This is the line we are fixing inside the file
CMD uvicorn api.app:app --host 0.0.0.0 --port $PORT
