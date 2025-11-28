from roboflow import Roboflow
import cv2
import numpy as np
import json
import os
import uuid
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
        tuple: (predictions_json, labeled_image_path)
            - predictions_json: Dictionary with detection results and colors
            - labeled_image_path: Path to the output image with bounding boxes
    """
    # Generate unique filenames for this request
    unique_id = str(uuid.uuid4())[:8]
    resized_path = f"temp_resized_{unique_id}.jpg"
    labeled_path = f"temp_labeled_{unique_id}.jpg"
    
    try:
        # --- Resize image ---
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image from {image_path}")
        
        img = cv2.resize(img, (1024, 1024), interpolation=cv2.INTER_AREA)
        cv2.imwrite(resized_path, img)
        
        # --- Get model and predict ---
        model = get_model()
        result = model.predict(resized_path, confidence=40)
        predictions = result.json()
        
        # --- Load resized image for processing ---
        image = cv2.imread(resized_path)
        
        # --- Process each detection ---
        for pred in predictions["predictions"]:
            x, y, w, h = int(pred["x"]), int(pred["y"]), int(pred["width"]), int(pred["height"])
            
            x1, x2 = x - w // 2, x + w // 2
            y1, y2 = y - h // 2, y + h // 2
            crop = image[y1:y2, x1:x2]
            
            if crop.size > 0:
                color = get_dominant_color_centered(crop, fraction=0.7)
            else:
                color = "unknown"
            
            pred["color"] = color
            
            # --- Draw bounding box ---
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 255), 2)
            
            # --- Label with color ---
            cv2.putText(
                image,
                color,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )
        
        # --- Save labeled image ---
        cv2.imwrite(labeled_path, image)
        
        # Cleanup resized image
        if os.path.exists(resized_path):
            os.remove(resized_path)
        
        return predictions, labeled_path
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(resized_path):
            os.remove(resized_path)
        if os.path.exists(labeled_path):
            os.remove(labeled_path)
        raise e


# Allow running as a script for testing
if __name__ == "__main__":
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else "wall.jpg"
    
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        sys.exit(1)
    
    predictions, labeled_path = detect_holds(image_path)
    
    # Save JSON for script usage
    json_path = "detection_with_color.json"
    with open(json_path, "w") as f:
        json.dump(predictions, f, indent=2)
    
    print(f"Saved: {labeled_path}")
    print(f"Saved: {json_path}")