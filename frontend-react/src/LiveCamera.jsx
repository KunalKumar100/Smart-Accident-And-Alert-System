import { useEffect, useRef, useState } from "react";
import axios from "axios";

export default function LiveCamera({ onIncident }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [streaming, setStreaming] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const enableWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setStreaming(true);
        }
      } catch (err) {
        console.error("Error accessing webcam:", err);
        setMessage("Cannot access camera. Check permissions.");
      }
    };

    enableWebcam();

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach((t) => t.stop());
      }
    };
  }, []);

  const captureAndDetect = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, width, height);

    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, "image/jpeg")
    );

    const formData = new FormData();
    formData.append("frame", blob, "frame.jpg");
    formData.append("camera_id", "LIVE_CAM_1");

    try {
      setMessage("Sending frame for detection…");
      const res = await axios.post(
        "http://localhost:8000/detect-accident",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      setMessage(res.data.message || "Frame analyzed.");

      if (onIncident && res.data?.incident_ids?.length > 0) {
        onIncident(res.data);
      }
    } catch (err) {
      console.error("Error detecting accident:", err);
      setMessage("Error during detection.");
    }
  };

  useEffect(() => {
    if (!detecting) return;

    const intervalId = setInterval(() => {
      captureAndDetect();
    }, 5000);

    return () => clearInterval(intervalId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detecting]);

  return (
    <div>
      <div
        style={{
          backgroundColor: "#000",
          borderRadius: 12,
          overflow: "hidden",
          border: "1px solid #333",
          marginBottom: "0.75rem",
          position: "relative",
        }}
      >
        <video
          ref={videoRef}
          autoPlay
          playsInline
          style={{
            width: "100%",
            display: streaming ? "block" : "none",
          }}
        />
        {!streaming && (
          <div
            style={{
              padding: "1.2rem",
              textAlign: "center",
              fontSize: "0.85rem",
              color: "#aaaaaa",
            }}
          >
            Waiting for camera permission…
          </div>
        )}
        {streaming && (
          <div
            style={{
              position: "absolute",
              top: 8,
              right: 8,
              padding: "2px 8px",
              borderRadius: "999px",
              backgroundColor: "rgba(0,0,0,0.6)",
              fontSize: "0.7rem",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              border: "1px solid rgba(255,255,255,0.2)",
            }}
          >
            Live
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button
          onClick={() => setDetecting((prev) => !prev)}
          disabled={!streaming}
          style={{
            flex: 1,
            padding: "0.5rem 0.8rem",
            backgroundColor: detecting ? "#444" : "#E50914",
            border: "none",
            color: "#fff",
            cursor: streaming ? "pointer" : "not-allowed",
            borderRadius: "999px",
            fontWeight: "bold",
            fontSize: "0.8rem",
            boxShadow: detecting
              ? "none"
              : "0 8px 18px rgba(229,9,20,0.35)",
            transition: "background 0.15s, transform 0.08s",
          }}
        >
          {detecting ? "Stop Auto Detection" : "Start Auto Detection"}
        </button>

        <button
          onClick={captureAndDetect}
          disabled={!streaming}
          style={{
            padding: "0.5rem 0.8rem",
            backgroundColor: "#333",
            border: "none",
            color: "#fff",
            cursor: streaming ? "pointer" : "not-allowed",
            borderRadius: "999px",
            fontWeight: "bold",
            fontSize: "0.8rem",
          }}
        >
          Capture Once
        </button>
      </div>

      {message && (
        <p
          style={{
            marginTop: "0.7rem",
            fontSize: "0.8rem",
            color: "#cccccc",
          }}
        >
          {message}
        </p>
      )}

      <canvas ref={canvasRef} style={{ display: "none" }} />
    </div>
  );
}
