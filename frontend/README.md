# Frontend

Next.js frontend application for climbing route detection and management.

## Features

- **Image Upload**: Upload climbing wall images for hold detection
- **Interactive Hold Selection**: Click on detected holds to select them for route creation
- **Route Visualization**: Visual feedback for selected holds (green highlight)
- **Route Comparison**: Automatic comparison with existing routes using AI
- **Route Gallery**: Browse all saved routes in a grid layout
- **Duplicate Detection**: Shows existing route when duplicate is detected

## Tech Stack

- **Next.js 14+** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **React Hooks** - State management and effects

## Setup

1. **Install dependencies**:

   ```bash
   npm install
   # or
   pnpm install
   ```

2. **Set up environment variables**:

   Create a `.env.local` file in the frontend directory:

   ```
   NEXT_PUBLIC_BACKEND_SERVER_URL=http://localhost:8000
   ```

3. **Run the development server**:

   ```bash
   npm run dev
   # or
   pnpm dev
   ```

   The application will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Home page with image upload
│   ├── select/
│   │   └── [id]/
│   │       └── page.tsx     # Route selection page
│   ├── routes/
│   │   └── page.tsx          # Routes gallery page
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── package.json              # Dependencies
└── README.md                 # This file
```

## Pages

### Home (`/`)
- Image upload interface
- Uploads image to backend for hold detection
- Redirects to selection page after upload

### Route Selection (`/select/[id]`)
- Displays detected holds with bounding boxes
- Interactive canvas for selecting holds
- Submit button to create route
- Shows route comparison results
- Displays existing route if duplicate detected

### Routes Gallery (`/routes`)
- Grid layout of all saved routes
- Click to view full-size image
- Refresh button to reload routes

## Usage Flow

1. **Upload Image**: Navigate to home page and upload a climbing wall image
2. **Select Holds**: Click on detected holds to select them (highlighted in green)
3. **Submit Route**: Click "Submit Selected" to create the route
4. **View Results**: 
   - If duplicate: See existing route image
   - If new: Route is saved and added to gallery
5. **Browse Routes**: Navigate to `/routes` to see all saved routes

## Features

### Interactive Selection
- Hover over holds to see yellow highlight
- Click to toggle selection (green highlight)
- Selected holds counter displayed
- Unselect all button available

### Route Comparison
- Automatic AI-powered comparison with existing routes
- Visual feedback when duplicate detected
- Explanation of comparison results

### Loading States
- Beautiful loading overlay during route processing
- Prevents interaction during API calls
- Clear status messages

## Environment Variables

- `NEXT_PUBLIC_BACKEND_SERVER_URL`: Backend API URL (default: `http://localhost:8000`)

## Development

- Uses Next.js App Router
- Client-side components with React hooks
- Session storage for temporary data
- Responsive design with inline styles

