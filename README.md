# Pebl Test - Climbing Route Detection & Management

A full-stack application for detecting climbing holds on spray walls, creating routes, and managing a route collection with AI-powered duplicate detection.

## Overview

This project helps climbers:
- Upload images of climbing walls
- Automatically detect climbing holds with color identification
- Create routes by selecting holds
- Compare new routes with existing ones using AI
- Browse and manage their route collection

## Architecture

- **Backend**: FastAPI (Python) with Roboflow for object detection and Google Gemini for route comparison
- **Frontend**: Next.js (React/TypeScript) with interactive canvas for hold selection

## Features

### Core Functionality
- ✅ Automatic hold detection using computer vision
- ✅ Color identification for each detected hold
- ✅ Interactive hold selection interface
- ✅ Route highlighting (blue for saved routes, red for comparison)
- ✅ AI-powered route comparison using Google Gemini
- ✅ Duplicate route detection
- ✅ Route gallery with image browsing

### Technical Highlights
- Async/await API endpoints with thread pool executors
- Non-blocking image processing
- Base64 image encoding for efficient transfer
- Session-based state management
- Responsive UI with loading states

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+ (or pnpm)
- API keys for:
  - [Roboflow](https://roboflow.com/) - Object detection
  - [Google AI Studio](https://makersuite.google.com/app/apikey) - Gemini API

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
echo "ROBOFLOW_API_KEY=your_key_here" > .env
echo "GEMINI_API_KEY=your_key_here" >> .env

# Run server
uvicorn app:app --reload
```

Backend runs on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install  # or pnpm install

# Create .env.local file
echo "NEXT_PUBLIC_BACKEND_SERVER_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev  # or pnpm dev
```

Frontend runs on `http://localhost:3000`

## Project Structure

```
pebl-test/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── detector.py         # Image processing & detection
│   ├── requirements.txt    # Python dependencies
│   ├── images/            # Generated route images
│   └── README.md          # Backend documentation
├── frontend/
│   ├── app/               # Next.js app directory
│   │   ├── page.tsx       # Home/upload page
│   │   ├── select/        # Route selection pages
│   │   └── routes/        # Routes gallery page
│   ├── package.json       # Node dependencies
│   └── README.md          # Frontend documentation
└── README.md              # This file
```

## Usage

1. **Upload Image**: Go to home page and upload a climbing wall image
2. **Detect Holds**: System automatically detects holds and identifies colors
3. **Select Holds**: Click on holds to select them for your route
4. **Submit Route**: Click "Submit Selected" to create the route
5. **View Results**: 
   - If duplicate: See the existing route
   - If new: Route is saved and added to collection
6. **Browse Routes**: Visit `/routes` to see all saved routes

## API Endpoints

### Backend (`http://localhost:8000`)

- `POST /detect-holds` - Upload image and detect holds
- `POST /select/{id}` - Create route and compare with existing routes
- `GET /routes` - List all saved routes
- `GET /routes/images/{filename}` - Serve route image

See [backend/README.md](backend/README.md) for detailed API documentation.

## Technologies

### Backend
- FastAPI - Modern Python web framework
- Roboflow - Object detection API
- Google Generative AI - Route comparison
- OpenCV - Image processing
- scikit-learn - Color clustering

### Frontend
- Next.js 14+ - React framework
- TypeScript - Type safety
- Canvas API - Interactive hold selection

## Environment Variables

### Backend (`.env`)
```
ROBOFLOW_API_KEY=your_roboflow_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### Frontend (`.env.local`)
```
NEXT_PUBLIC_BACKEND_SERVER_URL=http://localhost:8000
```

## Development

### Backend Development
- Uses async/await for non-blocking operations
- Thread pool executors for blocking I/O
- Automatic image cleanup for duplicates

### Frontend Development
- Hot module replacement enabled
- Session storage for temporary data
- Responsive design with inline styles

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
