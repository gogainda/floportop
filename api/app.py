from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API is online"}

@app.get("/predict")
def predict(feature1: float, feature2: float):
    # Hardcoded dummy response
    return {
        "prediction": "positive",
        "probability": 0.95,
        "input_received": {"f1": feature1, "f2": feature2}
    }
