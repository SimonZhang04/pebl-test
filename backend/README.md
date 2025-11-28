# Backend

Backend service for the pebl-test project, providing API endpoints and image processing capabilities for climbing wall hold detection.

## Features

- **Object Detection**: Uses Roboflow to detect climbing holds on spray walls
- **Color Analysis**: Identifies the dominant color of detected holds using K-means clustering
- **Image Processing**: Resizes and processes images using OpenCV
- **FastAPI**: RESTful API framework (when implemented)

## Requirements

- Python 3.12+
- Virtual environment (recommended)

## Setup

1. **Create a virtual environment** (if not already created):

   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment**:

   ```bash
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the backend directory:

   ```bash
   cp .env.example .env
   # or create .env manually
   ```

   Then edit `.env` and add your Roboflow API key:

   ```
   ROBOFLOW_API_KEY=your_api_key_here
   ```

   Get your API key from [Roboflow](https://roboflow.com/)

## Dependencies

- `fastapi` - Modern web framework for building APIs
- `uvicorn` - ASGI server for FastAPI
- `roboflow` - Object detection model integration
- `opencv-python` - Computer vision and image processing
- `scikit-learn` - Machine learning utilities (K-means clustering)
- `numpy` - Numerical computing
- `python-dotenv` - Environment variable management

## Usage

### Running the Detector

The `detector.py` script processes images to detect climbing holds and identify their colors:

```bash
python detector.py
```

**Note**: Make sure you have:

- A `.env` file with your `ROBOFLOW_API_KEY` set

The script will:

1. Resize the input image to 1024x1024
2. Run object detection using the Roboflow model
3. Analyze the color of each detected hold
4. Generate:
   - `prediction_colored.jpg` - Image with bounding boxes and color labels
   - `detection_with_color.json` - JSON file with detection results and colors

### Running the API Server

When the FastAPI application is implemented, you can run it with:

```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

## Configuration

### Roboflow API Key

The API key is stored in a `.env` file (not committed to git for security).

1. Create a `.env` file in the backend directory
2. Add your Roboflow API key:
   ```
   ROBOFLOW_API_KEY=your_actual_api_key_here
   ```

The `.env` file is automatically ignored by git to keep your API key secure.

## Project Structure

```
backend/
├── app.py              # FastAPI application (to be implemented)
├── detector.py         # Image processing and detection logic
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## Notes

- The detector script processes images locally and saves output files
- Color detection uses HSV color space and K-means clustering
- The model is configured for climbing hold detection with 40% confidence threshold
