from fastapi.testclient import TestClient
from src.api.app import app

# Initialize the test client with our FastAPI app
# We use 'with TestClient' to trigger the lifespan context manager (model loading)

def test_predict_valid_request():
    """Test that the API returns a valid rating for correct inputs."""
    with TestClient(app) as client:
        payload = {
            "user_id": 1,
            "item_id": 50
        }
        response = client.post("/predict", json=payload)
        
        # 1. Check that the request was successful
        assert response.status_code == 200
        
        # 2. Check the response structure and data types
        data = response.json()
        assert data["user_id"] == 1
        assert data["item_id"] == 50
        assert "predicted_rating" in data
        
        # 3. Ensure the rating falls within the 1-5 movie rating scale
        assert 1.0 <= data["predicted_rating"] <= 5.0

def test_predict_invalid_request():
    """Test that Pydantic properly blocks requests missing required fields."""
    with TestClient(app) as client:
        # Missing the 'item_id'
        payload = {
            "user_id": 1
        }
        response = client.post("/predict", json=payload)
        
        # 422 Unprocessable Entity is FastAPI's default error code for bad JSON schemas
        assert response.status_code == 422