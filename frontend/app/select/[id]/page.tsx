"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";

interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
  center: { x: number; y: number };
}

interface Detection {
  id: number;
  color: string;
  confidence: number;
  class: string;
  bbox: BoundingBox;
  raw: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

interface DetectionData {
  image: string;  // Changed from labeled_image to image
  detections: Detection[];
  image_dimensions: {
    width: number;
    height: number;
    original_width: number;
    original_height: number;
  };
  total_detections: number;
}

export default function SelectPage() {
  const params = useParams();
  const id = params.id as string;
  const [imageUrl, setImageUrl] = useState<string>("");
  const [detections, setDetections] = useState<Detection[]>([]);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  useEffect(() => {
    // Load detection data from sessionStorage
    const storedData = sessionStorage.getItem(`detection_${id}`);
    if (storedData) {
      try {
        const data: DetectionData = JSON.parse(storedData);
        const imageUrl = `data:image/jpeg;base64,${data.image}`;
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

    // Draw bounding boxes
    detections.forEach((detection) => {
      const { x1, y1, x2, y2 } = detection.bbox;
      const isSelected = selectedIds.has(detection.id);
      const isHovered = hoveredId === detection.id;

      // Draw bounding box
      ctx.strokeStyle = isSelected
        ? "#00ff00" // Green for selected
        : isHovered
        ? "#ffff00" // Yellow for hovered
        : "#ff0000"; // Red for unselected
      ctx.lineWidth = isSelected ? 4 : isHovered ? 3 : 2;
      ctx.setLineDash(isSelected ? [] : [5, 5]);
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

      // Fill with semi-transparent overlay if selected
      if (isSelected) {
        ctx.fillStyle = "rgba(0, 255, 0, 0.2)";
        ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
      }

      // Draw color label background
      ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
      ctx.fillRect(x1, y1 - 20, 60, 20);

      // Draw color label text
      ctx.fillStyle = "#ffffff";
      ctx.font = "12px Arial";
      ctx.fillText(detection.color, x1 + 5, y1 - 5);
    });
  }, [detections, selectedIds, hoveredId, imageLoaded]);

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
  }, [selectedIds, hoveredId, imageLoaded, drawCanvas]);

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

  const getDetectionAtPoint = (x: number, y: number): Detection | null => {
    // Find the detection that contains this point (check if point is inside bounding box)
    for (const detection of detections) {
      const { x1, y1, x2, y2 } = detection.bbox;
      if (x >= x1 && x <= x2 && y >= y1 && y <= y2) {
        return detection;
      }
    }
    return null;
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getMousePos(e);
    const detection = getDetectionAtPoint(pos.x, pos.y);

    if (detection) {
      // Toggle selection
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(detection.id)) {
          newSet.delete(detection.id);
        } else {
          newSet.add(detection.id);
        }
        return newSet;
      });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getMousePos(e);
    const detection = getDetectionAtPoint(pos.x, pos.y);
    setHoveredId(detection ? detection.id : null);
  };

  const handleMouseLeave = () => {
    setHoveredId(null);
  };

  const getColorHex = (color: string): string => {
    const colorMap: { [key: string]: string } = {
      red: "#ff0000",
      yellow: "#ffff00",
      green: "#00ff00",
      blue: "#0000ff",
      purple: "#800080",
      black: "#000000",
      white: "#ffffff",
      gray: "#808080",
      grey: "#808080",
      unknown: "#cccccc",
    };
    return colorMap[color.toLowerCase()] || "#cccccc";
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return "#00aa00"; // Green for high confidence
    if (confidence >= 0.6) return "#ffaa00"; // Orange for medium confidence
    return "#ff0000"; // Red for low confidence
  };

  const handleSubmit = async () => {
    if (selectedIds.size === 0) {
      alert("Please select at least one bounding box");
      return;
    }

    setSubmitting(true);
    try {
      const selectedDetections = detections.filter((d) =>
        selectedIds.has(d.id)
      );

      const backendUrl =
        process.env.NEXT_PUBLIC_BACKEND_SERVER_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/select/${id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          selected_detections: selectedDetections,
          all_detections: detections,
          selected_ids: Array.from(selectedIds),
        }),
      });

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
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <h1 style={{ marginBottom: "1.5rem" }}>Select Areas</h1>
      
      <div style={{ position: "relative", display: "inline-block", width: "100%" }}>
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{
            border: "1px solid #ccc",
            cursor: "pointer",
            maxWidth: "100%",
            display: "block",
          }}
        />
      </div>
      
      <div style={{ marginTop: "1.5rem" }}>
        <div style={{ marginBottom: "1rem" }}>
          <p style={{ marginBottom: "0.5rem" }}>
            <strong>Total detections:</strong> {detections.length} |{" "}
            <strong>Selected:</strong> {selectedIds.size}
          </p>
          <p style={{ fontSize: "0.9rem", color: "#666" }}>
            Click on bounding boxes to select them. Selected boxes are highlighted in green.
          </p>
        </div>
        
        <div style={{ display: "flex", gap: "1rem" }}>
          <button
            onClick={handleSubmit}
            disabled={selectedIds.size === 0 || submitting}
            style={{
              padding: "0.75rem 1.5rem",
              fontSize: "1rem",
              cursor: selectedIds.size === 0 ? "not-allowed" : "pointer",
              backgroundColor: selectedIds.size === 0 ? "#ccc" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              fontWeight: "500",
            }}
          >
            {submitting ? "Submitting..." : "Submit Selected"}
          </button>
          {selectedIds.size > 0 && (
            <button
              onClick={() => setSelectedIds(new Set())}
              style={{
                padding: "0.75rem 1.5rem",
                fontSize: "1rem",
                cursor: "pointer",
                backgroundColor: "#6c757d",
                color: "white",
                border: "none",
                borderRadius: "4px",
                fontWeight: "500",
              }}
            >
              Unselect All
            </button>
          )}
        </div>
      </div>
      
      {selectedIds.size > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2 style={{ marginBottom: "1rem", fontSize: "1.25rem" }}>
            Selected Holds ({selectedIds.size})
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: "1rem",
            }}
          >
            {detections
              .filter((d) => selectedIds.has(d.id))
              .map((detection) => (
                <div
                  key={detection.id}
                  style={{
                    padding: "1rem",
                    backgroundColor: "#fff",
                    borderRadius: "6px",
                    border: "1px solid #ddd",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "0.75rem",
                      paddingBottom: "0.75rem",
                      borderBottom: "1px solid #eee",
                    }}
                  >
                    <strong style={{ fontSize: "1rem" }}>Hold #{detection.id}</strong>
                    <span
                      style={{
                        padding: "0.25rem 0.75rem",
                        backgroundColor: getColorHex(detection.color),
                        color: "white",
                        borderRadius: "12px",
                        fontSize: "0.85rem",
                        fontWeight: "500",
                      }}
                    >
                      {detection.color}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.9rem", color: "#555" }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: "0.5rem",
                      }}
                    >
                      <span>
                        <strong>Confidence:</strong>
                      </span>
                      <span
                        style={{
                          color: getConfidenceColor(detection.confidence),
                          fontWeight: "600",
                        }}
                      >
                        {(detection.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: "0.5rem",
                      }}
                    >
                      <span>
                        <strong>Size:</strong>
                      </span>
                      <span>
                        {detection.bbox.width} × {detection.bbox.height} px
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>
                        <strong>Position:</strong>
                      </span>
                      <span>
                        ({detection.bbox.center.x}, {detection.bbox.center.y})
                      </span>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
