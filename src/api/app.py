from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import os
from contextlib import asynccontextmanager

# 1. Define the expected JSON payload
class RatingRequest(BaseModel):
    user_id: int
    item_id: int

# Global variable to hold our model
model = None
MODEL_PATH = "svd_model.pkl"

# 2. Modern Lifespan approach (Replaces @app.on_event("startup"))
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Everything before the 'yield' runs on startup
    global model
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        print("Model loaded successfully.")
    else:
        print(f" Warning: {MODEL_PATH} not found.")
    
    yield # The server runs while paused here
    
    # Everything after the 'yield' runs on shutdown (cleanup)
    model = None 

# Initialize the app with the lifespan
app = FastAPI(title="Recommendation System API", version="1.0", lifespan=lifespan)

# 3. Create the prediction endpoint
@app.post("/predict")
def predict_rating(request: RatingRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")
    
    prediction = model.predict(uid=request.user_id, iid=request.item_id)
    
    return {
        "user_id": request.user_id,
        "item_id": request.item_id,
        "predicted_rating": round(prediction.est, 2)
    }