# app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import base64
import uuid
from detector import detect_holds

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/detect-holds")
async def detect_holds_api(file: UploadFile = File(...)):
    """
    Upload an image and detect climbing holds with color identification.
    
    Returns:
        dict: Contains 'json' (detection results) and 'image_base64' (labeled image)
    """
    # Generate unique filename to avoid conflicts
    file_extension = os.path.splitext(file.filename)[1] or ".jpg"
    unique_id = str(uuid.uuid4())[:8]
    filepath = f"temp_upload_{unique_id}{file_extension}"
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Run detection
        result_json, labeled_image_path = detect_holds(filepath)
        
        # Encode labeled image as base64
        with open(labeled_image_path, "rb") as f:
            img_bytes = f.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        
        # Cleanup temporary files
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(labeled_image_path):
            os.remove(labeled_image_path)
        
        return {
            "success": True,
            "detections": result_json,
            "labeled_image": img_base64,  # Base64 encoded image with bounding boxes and labels
            "image_format": "data:image/jpeg;base64"  # For easy use in frontend: data:image/jpeg;base64,{img_base64}
        }
        
    except ValueError as e:
        # Cleanup on error
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Cleanup on error
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Climbing Hold Detection API", "endpoints": ["/detect-holds"]}