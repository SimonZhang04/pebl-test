# app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import shutil
import os
import base64
import uuid
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from dotenv import load_dotenv
from detector import detect_holds, create_highlighted_image

# Load environment variables
load_dotenv()

# Thread pool executor for blocking operations (prevents terminal freezing)
executor = ThreadPoolExecutor(max_workers=2)

# Thread pool executor for blocking operations
executor = ThreadPoolExecutor(max_workers=2)

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
        detections_data, original_image_path = detect_holds(filepath)
        
        # Encode original image (without labels) as base64
        with open(original_image_path, "rb") as f:
            img_bytes = f.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        
        # Cleanup temporary files
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(original_image_path):
            os.remove(original_image_path)
        
        return {
            "success": True,
            "detections": detections_data["detections"],  # Array of detections with bounding boxes
            "image_dimensions": detections_data["image_dimensions"],  # Image size info
            "total_detections": detections_data["total_detections"],
            "image": img_base64,  # Base64 encoded original image (without labels)
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

class SelectRequest(BaseModel):
    selected_detections: List[Dict[str, Any]]
    all_detections: List[Dict[str, Any]]
    selected_ids: List[int]
    image_base64: str  # Base64 encoded image (without data URI prefix)

@app.post("/select/{id}")
async def select_holds_api(id: str, request: SelectRequest):
    """
    Create two highlighted images with selected holds - one in blue and one in red.
    
    Args:
        id: Session ID (not currently used but kept for consistency)
        request: Contains selected detections, all detections, selected IDs, and base64 image
        
    Returns:
        dict: Contains 'blue_image' and 'red_image' as base64 encoded strings
    """
    try:
        # Validate that we have selected detections
        if not request.selected_detections or len(request.selected_detections) == 0:
            raise HTTPException(status_code=400, detail="No selected detections provided")
        
        # Extract base64 image (remove data URI prefix if present)
        image_base64 = request.image_base64
        if image_base64.startswith("data:image"):
            # Remove data URI prefix (e.g., "data:image/jpeg;base64,")
            image_base64 = image_base64.split(",", 1)[1]
        
        # Create blue highlighted image (BGR: (255, 0, 0) = blue)
        blue_image_base64 = create_highlighted_image(
            image_base64,
            request.selected_detections,
            highlight_color=(255, 0, 0)  # Blue in BGR
        )
        
        # Create red highlighted image (BGR: (0, 0, 255) = red)
        red_image_base64 = create_highlighted_image(
            image_base64,
            request.selected_detections,
            highlight_color=(0, 0, 255)  # Red in BGR
        )
        
        # Get current working directory (backend directory) and create images directory
        cwd = os.getcwd()
        images_dir = os.path.join(cwd, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Call Gemini API FIRST to check if this matches an existing route
        # We'll only save images if it's a new route
        gemini_response = None
        matching_image_filename = None
        is_match = False
        
        try:
            gemini_response, matching_image_filename, is_match = await compare_with_gemini(
                red_image_base64, images_dir
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Gemini API error: {str(e)}")
        
        # If it's a match, don't save images and return the matching image
        if is_match and matching_image_filename:
            return {
                "success": True,
                "is_match": True,
                "matching_image_filename": matching_image_filename,
                "gemini_response": gemini_response
            }
        
        # If not a match, save the new images
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        blue_filename = f"blue_{timestamp}_{unique_id}.jpg"
        red_filename = f"red_{timestamp}_{unique_id}.jpg"
        
        blue_path = os.path.join(images_dir, blue_filename)
        red_path = os.path.join(images_dir, red_filename)
        
        # Decode and save blue image
        blue_img_bytes = base64.b64decode(blue_image_base64)
        with open(blue_path, "wb") as f:
            f.write(blue_img_bytes)
        
        # Decode and save red image
        red_img_bytes = base64.b64decode(red_image_base64)
        with open(red_path, "wb") as f:
            f.write(red_img_bytes)
        
        return {
            "success": True,
            "is_match": False,
            "blue_image": blue_image_base64,
            "red_image": red_image_base64,
            "blue_filename": blue_filename,
            "red_filename": red_filename,
            "gemini_response": gemini_response
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error processing images: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

async def compare_with_gemini(red_image_base64: str, images_dir: str) -> tuple:
    """
    Compare red highlighted image with all existing blue highlighted images using Gemini API.
    
    Args:
        red_image_base64: Base64 encoded red highlighted image
        images_dir: Directory containing blue images
        
    Returns:
        tuple: (gemini_response_dict, matching_image_filename, is_match)
            - gemini_response_dict: Contains 'explanation' and 'full_response'
            - matching_image_filename: Filename of matching image if found, None otherwise
            - is_match: Boolean indicating if a match was found
    """
    # Get Gemini API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3-pro-preview')
    
    # Get all existing blue images
    # Use thread pool for file I/O to avoid blocking the event loop
    blue_images = []
    blue_filenames = []
    if os.path.exists(images_dir):
        def read_image_file(filename):
            filepath = os.path.join(images_dir, filename)
            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    img_bytes = f.read()
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                return {
                    "filename": filename,
                    "base64": img_base64
                }
            return None
        
        filenames = [f for f in os.listdir(images_dir) 
                     if f.startswith("blue_") and f.endswith(".jpg")]
        blue_filenames = filenames.copy()
        
        # Read files in parallel using thread pool to prevent blocking
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(executor, read_image_file, f) for f in filenames]
        results = await asyncio.gather(*tasks)
        blue_images = [r for r in results if r is not None]
    
    if len(blue_images) == 0:
        return {
            "explanation": "No existing routes to compare with."
        }, None, False
    
    # Prepare the prompt - ask Gemini to identify which image matched
    image_labels = [f"Image {i+1}" for i in range(len(blue_images))]
    image_list = ", ".join(image_labels)
    
    prompt = f"""You will receive two types of images:
1. Reference images — {len(blue_images)} image(s) showing climbing routes from my collection (labeled as {image_list}).
• Every hold belonging to each route is circled in blue.
• Each circle represents exactly one hold, but the circle may not perfectly match the size of the hold (it may be too big or too small).
• All holds in a route are the same colour (e.g., all green holds or all red holds), and the blue circles mark those holds.
2. Query image — This image shows a different set of holds:
• These holds are circled in red.
• Each red circle represents exactly one hold, but may also be inaccurately sized (too large, too small, or slightly misaligned).
• The red-circled holds together may represent a climb.

Task:
Determine whether the set of red-circled holds in the query image corresponds to any of the blue-circled routes shown in the reference images.
To do this, compare the physical holds on the wall—not the circles themselves—by examining:
• Hold colour
• Hold shape and texture
• Position and spacing relative to other holds
• Orientation
• Any distinctive wall features near the holds

Because circles may be inaccurate, use the actual hold characteristics rather than circle boundaries to make the determination.

Output format:
• Answer "Yes" if the red-circled holds represent the same route as one of the blue-circled routes, and specify which image (e.g., "Image 1", "Image 2", etc.).
• Answer "No" if they do not match any.
• Include a brief explanation referencing the visual evidence (e.g., hold colour consistency, positional layout, matching shapes, or mismatched holds)."""
    
    # Prepare content for Gemini
    content_parts = [prompt]
    
    # Add red image (query image)
    red_img_data = base64.b64decode(red_image_base64)
    content_parts.append({
        "mime_type": "image/jpeg",
        "data": red_img_data
    })
    
    # Add all blue (reference) images
    for blue_img in blue_images:
        blue_img_data = base64.b64decode(blue_img["base64"])
        content_parts.append({
            "mime_type": "image/jpeg",
            "data": blue_img_data
        })
    
    # Call Gemini API in a thread pool to avoid blocking the event loop
    # This prevents the terminal/server from freezing during long API calls
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        executor,
        lambda: model.generate_content(content_parts)
    )
    response_text = response.text.strip()
    
    # Parse response to extract answer and explanation
    # Check if answer is Yes
    is_match = False
    matching_image_filename = None
    
    response_lower = response_text.lower()
    
    # Check if answer is Yes (handle various formats)
    if "yes" in response_lower and ("no" not in response_lower[:50] or response_lower.find("yes") < response_lower.find("no")):
        is_match = True
        
        # Try to identify which image matched
        # Look for patterns like "Image 1", "Image 2", "first image", "second image", etc.
        for i, filename in enumerate(blue_filenames):
            image_num = i + 1
            # Check for various patterns
            patterns = [
                f"image {image_num}",
                f"image{image_num}",
                f"the {image_num}{'st' if image_num == 1 else 'nd' if image_num == 2 else 'rd' if image_num == 3 else 'th'} image",
                f"{image_num}{'st' if image_num == 1 else 'nd' if image_num == 2 else 'rd' if image_num == 3 else 'th'} image",
                ("first image" if image_num == 1 else "second image" if image_num == 2 else "third image" if image_num == 3 else None)
            ]
            
            for pattern in patterns:
                if pattern and pattern in response_lower:
                    matching_image_filename = filename
                    break
            
            if matching_image_filename:
                break
        
        # If no specific image identified but it's a match, use the first one
        if not matching_image_filename and len(blue_filenames) > 0:
            matching_image_filename = blue_filenames[0]
    
    # Extract explanation
    explanation = response_text
    
    # Try to extract explanation if it's in markdown format
    if "**Explanation:**" in response_text or "**Explanation**" in response_text:
        parts = response_text.split("**Explanation:**", 1)
        if len(parts) > 1:
            explanation = parts[1].strip()
        else:
            parts = response_text.split("**Explanation**", 1)
            if len(parts) > 1:
                explanation = parts[1].strip()
    
    # Remove markdown formatting from explanation
    explanation = explanation.replace("**", "").strip()
    
    # If explanation starts with common prefixes, remove them
    prefixes_to_remove = ["Explanation:", "Explanation", "Answer:", "Answer"]
    for prefix in prefixes_to_remove:
        if explanation.lower().startswith(prefix.lower()):
            explanation = explanation[len(prefix):].strip()
            if explanation.startswith(":"):
                explanation = explanation[1:].strip()
    
    print(f"Gemini response: {response_text}")
    print(f"Is match: {is_match}, Matching image: {matching_image_filename}")
    print(f"Extracted explanation: {explanation}")
    
    gemini_response_dict = {
        "explanation": explanation,
        "full_response": response_text
    }
    
    return gemini_response_dict, matching_image_filename, is_match

@app.get("/routes")
async def get_routes():
    """
    Get list of all blue highlighted images.
    
    Returns:
        dict: Contains list of blue image filenames
    """
    try:
        cwd = os.getcwd()
        images_dir = os.path.join(cwd, "images")
        
        # Create images directory if it doesn't exist
        os.makedirs(images_dir, exist_ok=True)
        
        blue_images = []
        
        # List all files in images directory that start with "blue_"
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.startswith("blue_") and filename.endswith(".jpg"):
                    filepath = os.path.join(images_dir, filename)
                    if os.path.isfile(filepath):
                        # Get file modification time for sorting
                        mtime = os.path.getmtime(filepath)
                        blue_images.append({
                            "filename": filename,
                            "modified_time": mtime
                        })
        
        # Sort by modification time (newest first)
        blue_images.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return {
            "success": True,
            "images": [img["filename"] for img in blue_images],
            "count": len(blue_images)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing images: {str(e)}")

@app.get("/routes/images/{filename}")
async def get_route_image(filename: str):
    """
    Serve a specific blue highlighted image.
    
    Args:
        filename: Name of the image file
        
    Returns:
        FileResponse: The image file
    """
    try:
        # Security: Only allow blue_*.jpg files
        if not filename.startswith("blue_") or not filename.endswith(".jpg"):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        cwd = os.getcwd()
        images_dir = os.path.join(cwd, "images")
        filepath = os.path.join(images_dir, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Image not found")
        
        return FileResponse(filepath, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Climbing Hold Detection API", "endpoints": ["/detect-holds", "/select/{id}", "/routes"]}