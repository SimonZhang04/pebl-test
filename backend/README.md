# Backend

Backend service for the pebl-test project, providing API endpoints and image processing capabilities for climbing wall hold detection and route comparison.

## Features

- **Object Detection**: Uses Roboflow to detect climbing holds on spray walls
- **Color Analysis**: Identifies the dominant color of detected holds using K-means clustering
- **Image Processing**: Resizes and processes images using OpenCV
- **Route Highlighting**: Generates images with selected holds highlighted in blue or red
- **Route Comparison**: Uses Google Gemini AI to compare new routes with existing routes
- **Duplicate Detection**: Automatically detects and prevents duplicate route submissions
- **FastAPI**: RESTful API framework with async support

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

   Then edit `.env` and add your API keys:

   ```
   ROBOFLOW_API_KEY=your_roboflow_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

   Get your API keys from:
   - [Roboflow](https://roboflow.com/) - for object detection
   - [Google AI Studio](https://makersuite.google.com/app/apikey) - for Gemini API

## Dependencies

- `fastapi` - Modern web framework for building APIs
- `uvicorn` - ASGI server for FastAPI
- `roboflow` - Object detection model integration
- `opencv-python` - Computer vision and image processing
- `scikit-learn` - Machine learning utilities (K-means clustering)
- `numpy` - Numerical computing
- `python-dotenv` - Environment variable management
- `google-generativeai` - Google Gemini AI integration for route comparison

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

Start the FastAPI server:

```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### `POST /detect-holds`
Upload an image and detect climbing holds with color identification.

**Request**: Multipart form data with image file

**Response**: JSON containing:
- `detections`: Array of detected holds with bounding boxes and colors
- `image`: Base64 encoded image (1024x1024 resized)
- `image_dimensions`: Image size information
- `total_detections`: Number of holds detected

#### `POST /select/{id}`
Create highlighted images for selected holds and compare with existing routes.

**Request**: JSON body containing:
- `selected_detections`: Array of selected detection objects
- `all_detections`: Array of all detection objects
- `selected_ids`: Array of selected detection IDs
- `image_base64`: Base64 encoded image

**Response**: JSON containing:
- `success`: Boolean indicating success
- `is_match`: Boolean indicating if route matches an existing one
- If match: `matching_image_filename` and `gemini_response`
- If no match: `blue_image`, `red_image`, `blue_filename`, `red_filename`, and `gemini_response`

#### `GET /routes`
Get list of all saved blue highlighted route images.

**Response**: JSON containing:
- `success`: Boolean
- `images`: Array of image filenames
- `count`: Number of routes

#### `GET /routes/images/{filename}`
Serve a specific route image file.

**Response**: Image file (JPEG)

## Configuration

### Environment Variables

API keys are stored in a `.env` file (not committed to git for security).

1. Create a `.env` file in the backend directory
2. Add your API keys:
   ```
   ROBOFLOW_API_KEY=your_roboflow_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

The `.env` file is automatically ignored by git to keep your API keys secure.

### Image Storage

- Generated route images are saved in the `images/` directory
- Blue images represent saved routes
- Red images are temporary (used for comparison only)
- Images are automatically cleaned up if a duplicate route is detected

## Project Structure

```
backend/
├── app.py              # FastAPI application with route comparison
├── detector.py         # Image processing and detection logic
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
├── images/            # Generated route images (created automatically)
└── README.md          # This file
```

## How It Works

### Route Detection Flow

1. **Image Upload**: User uploads an image via `/detect-holds`
2. **Hold Detection**: Roboflow detects climbing holds and identifies colors
3. **Route Selection**: User selects holds via frontend
4. **Route Comparison**: 
   - Red highlighted image is compared with all existing blue route images
   - Gemini AI analyzes hold characteristics (color, shape, position)
   - Determines if the route matches an existing one
5. **Route Saving**:
   - If match found: Existing route is surfaced, new images are not saved
   - If no match: New route images are saved to `images/` directory

### Technical Details

- Images are resized to 1024x1024 for processing
- Color detection uses HSV color space and K-means clustering
- Object detection uses 40% confidence threshold
- Gemini API uses `gemini-3-pro-preview` model for route comparison
- All blocking operations run in thread pool executors to prevent server freezing
- Route images are stored with timestamp and UUID in filename format: `blue_YYYYMMDD_HHMMSS_uuid.jpg`

## Notes

- The detector script processes images locally and saves output files
- Color detection uses HSV color space and K-means clustering
- The model is configured for climbing hold detection with 40% confidence threshold
- Route comparison uses Google Gemini AI to analyze visual similarities
- Duplicate routes are automatically detected to prevent redundant entries
