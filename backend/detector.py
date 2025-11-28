from roboflow import Roboflow
import cv2
import numpy as np
import json
import os
import uuid
import base64
from sklearn.cluster import KMeans
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Load model (cached globally) ---
_model = None

def get_model():
    """Get or initialize the Roboflow model (singleton pattern)"""
    global _model
    if _model is None:
        api_key = os.getenv("ROBOFLOW_API_KEY")
        if not api_key:
            raise ValueError("ROBOFLOW_API_KEY environment variable is not set. Please create a .env file with your API key.")
        
        rf = Roboflow(api_key=api_key)
        project = rf.workspace("spraywall-id").project("climbing-rv6vd")
        _model = project.version(1).model
    return _model

# --- Color Helpers ---
def hsv_to_color_name(h, s, v):
    if v < 50:
        return "black"
    if s < 50:
        return "white" if v > 200 else "gray"

    if 0 <= h < 15 or 165 <= h <= 180:
        return "red"
    elif 15 <= h < 35:
        return "yellow"
    elif 35 <= h < 85:
        return "green"
    elif 85 <= h < 130:
        return "blue"
    elif 130 <= h < 165:
        return "purple"
    return "unknown"

def get_dominant_color_centered(crop, fraction=0.5):
    h, w, _ = crop.shape
    h_center = int(h * fraction)
    w_center = int(w * fraction)
    y1 = (h - h_center) // 2
    y2 = y1 + h_center
    x1 = (w - w_center) // 2
    x2 = x1 + w_center

    center_crop = crop[y1:y2, x1:x2]

    # Convert to HSV
    hsv = cv2.cvtColor(center_crop, cv2.COLOR_BGR2HSV)
    pixels = hsv.reshape((-1, 3))

    # Filter out low saturation / very bright pixels (likely wall)
    pixels = np.array([p for p in pixels if p[1] > 50 and p[2] < 220])
    if len(pixels) == 0:
        return "unknown"

    # Adjust number of clusters based on available pixels
    n_clusters = min(3, len(pixels))
    if n_clusters == 1:
        dominant_cluster = pixels[0]
    else:
        kmeans = KMeans(n_clusters=n_clusters, n_init="auto")
        kmeans.fit(pixels)
        labels, counts = np.unique(kmeans.labels_, return_counts=True)
        dominant_cluster = kmeans.cluster_centers_[labels[np.argmax(counts)]]

    h, s, v = dominant_cluster
    return hsv_to_color_name(h, s, v)

def detect_holds(image_path: str):
    """
    Detect climbing holds in an image and identify their colors.
    
    Args:
        image_path: Path to the input image file
        
    Returns:
        tuple: (detections_data, original_image_path)
            - detections_data: Dictionary with structured detection results including bounding boxes
            - original_image_path: Path to the original resized image (without labels)
    """
    # Generate unique filenames for this request
    unique_id = str(uuid.uuid4())[:8]
    resized_path = f"temp_resized_{unique_id}.jpg"
    
    try:
        # --- Load and resize image ---
        original_img = cv2.imread(image_path)
        if original_img is None:
            raise ValueError(f"Could not read image from {image_path}")
        
        original_height, original_width = original_img.shape[:2]
        img = cv2.resize(original_img, (1024, 1024), interpolation=cv2.INTER_AREA)
        cv2.imwrite(resized_path, img)
        
        # --- Get model and predict ---
        model = get_model()
        result = model.predict(resized_path, confidence=40)
        predictions = result.json()
        
        # --- Load resized image for processing ---
        image = cv2.imread(resized_path)
        
        # --- Process each detection and format for frontend ---
        formatted_detections = []
        for idx, pred in enumerate(predictions["predictions"]):
            # Roboflow returns center-based coordinates
            x_center = int(pred["x"])
            y_center = int(pred["y"])
            w = int(pred["width"])
            h = int(pred["height"])
            
            # Convert to corner coordinates (x1, y1, x2, y2) for 1024x1024 image
            x1 = x_center - w // 2
            y1 = y_center - h // 2
            x2 = x_center + w // 2
            y2 = y_center + h // 2
            
            # Get color from crop
            crop = image[y1:y2, x1:x2]
            if crop.size > 0:
                color = get_dominant_color_centered(crop, fraction=0.7)
            else:
                color = "unknown"
            
            # Format detection data for frontend
            detection = {
                "id": idx,  # Unique ID for selection
                "color": color,
                "confidence": pred.get("confidence", 0),
                "class": pred.get("class", "hold"),
                # Bounding box coordinates in resized image (1024x1024)
                "bbox": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "width": w,
                    "height": h,
                    "center": {"x": x_center, "y": y_center}
                },
                # Original coordinates from Roboflow (for reference)
                "raw": {
                    "x": x_center,
                    "y": y_center,
                    "width": w,
                    "height": h
                }
            }
            formatted_detections.append(detection)
        
        # Return structured data with original image (no labels drawn)
        detections_data = {
            "detections": formatted_detections,
            "image_dimensions": {
                "width": 1024,  # Resized image width
                "height": 1024,  # Resized image height
                "original_width": original_width,
                "original_height": original_height
            },
            "total_detections": len(formatted_detections)
        }
        
        return detections_data, resized_path
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(resized_path):
            os.remove(resized_path)
        raise e


def create_highlighted_image(image_base64: str, selected_detections: list, highlight_color: tuple) -> str:
    """
    Create an image with only selected holds highlighted in the specified color.
    
    Args:
        image_base64: Base64 encoded image string (without data URI prefix)
        selected_detections: List of detection objects with bbox information
        highlight_color: BGR color tuple (e.g., (255, 0, 0) for blue, (0, 0, 255) for red)
        
    Returns:
        Base64 encoded JPEG image string
    """
    # Decode base64 image
    img_bytes = base64.b64decode(image_base64)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Could not decode image from base64")
    
    # Create a copy of the image
    highlighted_img = img.copy()
    
    # Draw bounding boxes for selected detections only
    for detection in selected_detections:
        bbox = detection.get("bbox", {})
        if not bbox:
            continue  # Skip if no bbox data
        
        x1 = int(bbox.get("x1", 0))
        y1 = int(bbox.get("y1", 0))
        x2 = int(bbox.get("x2", 0))
        y2 = int(bbox.get("y2", 0))
        
        # Validate coordinates
        if x2 <= x1 or y2 <= y1:
            continue  # Skip invalid bounding boxes
        
        # Draw only the bounding box border (no fill/overlay) to preserve hold colors
        cv2.rectangle(highlighted_img, (x1, y1), (x2, y2), highlight_color, 4)
    
    # Encode image to JPEG base64
    _, buffer = cv2.imencode('.jpg', highlighted_img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return img_base64


# Allow running as a script for testing
if __name__ == "__main__":
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else "wall.jpg"
    
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        sys.exit(1)
    
    detections_data, image_path = detect_holds(image_path)
    
    # Save JSON for script usage
    json_path = "detection_with_color.json"
    with open(json_path, "w") as f:
        json.dump(detections_data, f, indent=2)
    
    print(f"Image saved: {image_path}")
    print(f"Saved: {json_path}")
    print(f"Total detections: {detections_data['total_detections']}")