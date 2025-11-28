"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";

interface Circle {
  x: number;
  y: number;
  radius: number;
}

interface DetectionData {
  labeled_image: string;
  detections: unknown[];
}

export default function SelectPage() {
  const params = useParams();
  const id = params.id as string;
  const [imageUrl, setImageUrl] = useState<string>("");
  const [detections, setDetections] = useState<unknown[]>([]);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [circles, setCircles] = useState<Circle[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentCircle, setCurrentCircle] = useState<Circle | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Load detection data from sessionStorage
    const storedData = sessionStorage.getItem(`detection_${id}`);
    if (storedData) {
      try {
        const data: DetectionData = JSON.parse(storedData);
        const imageUrl = `data:image/jpeg;base64,${data.labeled_image}`;
        setImageUrl(imageUrl);
        setDetections(data.detections || []);
      } catch (error) {
        console.error("Error parsing stored data:", error);
      }
    }
  }, [id]);

  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img || !imageLoaded) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);

    circles.forEach((circle) => {
      ctx.beginPath();
      ctx.arc(circle.x, circle.y, circle.radius, 0, 2 * Math.PI);
      ctx.strokeStyle = "red";
      ctx.lineWidth = 3;
      ctx.stroke();
    });

    if (currentCircle) {
      ctx.beginPath();
      ctx.arc(
        currentCircle.x,
        currentCircle.y,
        currentCircle.radius,
        0,
        2 * Math.PI
      );
      ctx.strokeStyle = "red";
      ctx.lineWidth = 3;
      ctx.stroke();
    }
  }, [circles, currentCircle, imageLoaded]);

  useEffect(() => {
    if (imageUrl && canvasRef.current) {
      const img = new Image();
      img.onload = () => {
        imageRef.current = img;
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.width = img.width;
          canvas.height = img.height;
          setImageLoaded(true);
        }
      };
      img.src = imageUrl;
    }
  }, [imageUrl]);

  useEffect(() => {
    if (imageLoaded) {
      drawCanvas();
    }
  }, [circles, currentCircle, imageLoaded, drawCanvas]);

  const getMousePos = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getMousePos(e);
    setIsDrawing(true);
    setCurrentCircle({ x: pos.x, y: pos.y, radius: 0 });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !currentCircle) return;

    const pos = getMousePos(e);
    const radius = Math.sqrt(
      Math.pow(pos.x - currentCircle.x, 2) +
        Math.pow(pos.y - currentCircle.y, 2)
    );

    setCurrentCircle({ ...currentCircle, radius });
    drawCanvas();
  };

  const handleMouseUp = () => {
    if (currentCircle && currentCircle.radius > 5) {
      setCircles([...circles, currentCircle]);
    }
    setIsDrawing(false);
    setCurrentCircle(null);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_SERVER_URL || 'http://localhost:8000';
      const response = await fetch(
        `${backendUrl}/select/${id}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ 
            circles,
            detections, // Include original detections from API
          }),
        }
      );

      if (response.ok) {
        alert("Submitted successfully!");
      } else {
        alert("Submit failed");
      }
    } catch {
      alert("Error submitting");
    } finally {
      setSubmitting(false);
    }
  };

  if (!imageUrl) {
    return <div style={{ padding: "2rem" }}>Loading image...</div>;
  }

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Select Areas</h1>
      <div style={{ position: "relative", display: "inline-block" }}>
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          style={{
            border: "1px solid #ccc",
            cursor: "crosshair",
            maxWidth: "100%",
          }}
        />
      </div>
      <div style={{ marginTop: "1rem" }}>
        <p>Circles drawn: {circles.length}</p>
        <button
          onClick={handleSubmit}
          disabled={circles.length === 0 || submitting}
        >
          {submitting ? "Submitting..." : "Submit"}
        </button>
      </div>
    </div>
  );
}
