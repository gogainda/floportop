#!/bin/bash
# Start both API and Streamlit frontend

# Set API URL for internal communication
export API_URL="http://localhost:8080"

# Start API in background
uvicorn api.app:app --host 0.0.0.0 --port 8080 &

# Wait for API to be ready
echo "Waiting for API to start..."
until curl -s http://localhost:8080/ > /dev/null 2>&1; do
    sleep 1
done
echo "API is ready"

# Start Streamlit in foreground
exec streamlit run frontend/app.py --server.port=8501 --server.address=0.0.0.0
