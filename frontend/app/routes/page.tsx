"use client";

import { useState, useEffect } from "react";

interface RouteImage {
  filename: string;
}

export default function RoutesPage() {
  const [images, setImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    fetchRoutes();
  }, []);

  const fetchRoutes = async () => {
    try {
      setLoading(true);
      setError("");
      const backendUrl =
        process.env.NEXT_PUBLIC_BACKEND_SERVER_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/routes`);

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.images) {
          setImages(data.images);
        } else {
          setError("Failed to load images");
        }
      } else {
        setError("Failed to fetch routes");
      }
    } catch (err) {
      setError("Error connecting to server");
      console.error("Error fetching routes:", err);
    } finally {
      setLoading(false);
    }
  };

  const getImageUrl = (filename: string): string => {
    const backendUrl =
      process.env.NEXT_PUBLIC_BACKEND_SERVER_URL || "http://localhost:8000";
    return `${backendUrl}/routes/images/${filename}`;
  };

  if (loading) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        <p>Loading routes...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "2rem" }}>
        <div
          style={{
            padding: "1rem",
            backgroundColor: "#fee",
            border: "1px solid #fcc",
            borderRadius: "4px",
            color: "#c00",
            marginBottom: "1rem",
          }}
        >
          {error}
        </div>
        <button
          onClick={fetchRoutes}
          style={{
            padding: "0.75rem 1.5rem",
            fontSize: "1rem",
            cursor: "pointer",
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "4px",
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "1400px", margin: "0 auto" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2rem",
        }}
      >
        <h1 style={{ margin: 0 }}>Routes</h1>
        <button
          onClick={fetchRoutes}
          style={{
            padding: "0.75rem 1.5rem",
            fontSize: "1rem",
            cursor: "pointer",
            backgroundColor: "#6c757d",
            color: "white",
            border: "none",
            borderRadius: "4px",
          }}
        >
          Refresh
        </button>
      </div>

      {images.length === 0 ? (
        <div
          style={{
            padding: "3rem",
            textAlign: "center",
            color: "#666",
            backgroundColor: "#f9f9f9",
            borderRadius: "8px",
          }}
        >
          <p style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>
            No routes found
          </p>
          <p style={{ fontSize: "0.9rem" }}>
            Submit some holds to create your first route!
          </p>
        </div>
      ) : (
        <>
          <p style={{ marginBottom: "1.5rem", color: "#666" }}>
            Found {images.length} route{images.length !== 1 ? "s" : ""}
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {images.map((filename) => (
              <div
                key={filename}
                style={{
                  backgroundColor: "#fff",
                  borderRadius: "8px",
                  border: "1px solid #ddd",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                  overflow: "hidden",
                  transition: "transform 0.2s, box-shadow 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-4px)";
                  e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.1)";
                }}
              >
                <div style={{ position: "relative", width: "100%", paddingTop: "100%" }}>
                  <img
                    src={getImageUrl(filename)}
                    alt={filename}
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      cursor: "pointer",
                    }}
                    onClick={() => {
                      // Open image in new tab for full size view
                      window.open(getImageUrl(filename), "_blank");
                    }}
                  />
                </div>
                <div style={{ padding: "1rem" }}>
                  <p
                    style={{
                      margin: 0,
                      fontSize: "0.9rem",
                      color: "#555",
                      wordBreak: "break-word",
                    }}
                  >
                    {filename}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

