from roboflow import Roboflow
import cv2
import numpy as np
import json
from sklearn.cluster import KMeans

# --- Resize image ---
img = cv2.imread("wall.jpg")
img = cv2.resize(img, (1024, 1024), interpolation=cv2.INTER_AREA)
cv2.imwrite("wall_resized.jpg", img)

# --- Load model ---
rf = Roboflow(api_key="uHFsgXwDpQkhJkyfTrUd")
project = rf.workspace("spraywall-id").project("climbing-rv6vd")
model = project.version(1).model

# --- Predict ---
result = model.predict("wall_resized.jpg", confidence=40)
predictions = result.json()

image = cv2.imread("wall_resized.jpg")

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

# --- Process each detection ---
for pred in predictions["predictions"]:
    x, y, w, h = int(pred["x"]), int(pred["y"]), int(pred["width"]), int(pred["height"])

    x1, x2 = x - w // 2, x + w // 2
    y1, y2 = y - h // 2, y + h // 2
    crop = image[y1:y2, x1:x2]

    if crop.size > 0:
        color =  get_dominant_color_centered(crop, fraction=0.7)
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
cv2.imwrite("prediction_colored.jpg", image)

# --- Save JSON ---
with open("detection_with_color.json", "w") as f:
    json.dump(predictions, f, indent=2)

print("Saved: prediction_colored.jpg")
print("Saved: detection_with_color.json")