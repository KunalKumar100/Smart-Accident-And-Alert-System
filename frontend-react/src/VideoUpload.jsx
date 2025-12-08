import { useState } from "react";
import axios from "axios";

export default function VideoUpload({ onAnalyzed }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0] || null);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a video file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploading(true);
      setMessage("Uploading and analyzing video…");

      const res = await axios.post(
        "http://localhost:8000/analyze-video",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      setMessage(res.data.message || "Video analyzed successfully.");

      if (onAnalyzed) {
        onAnalyzed(res.data);
      }
    } catch (err) {
      console.error("Error uploading video:", err);
      setMessage("Error analyzing video.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <label
        style={{
          display: "block",
          border: "1px dashed #444",
          borderRadius: 10,
          padding: "0.9rem",
          cursor: "pointer",
          marginBottom: "0.6rem",
          background:
            "linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01))",
        }}
      >
        <span
          style={{
            fontSize: "0.8rem",
            color: "#cccccc",
          }}
        >
          {file ? (
            <>
              Selected file:{" "}
              <span style={{ color: "#ffffff" }}>{file.name}</span>
            </>
          ) : (
            "Click to choose a video file"
          )}
        </span>
        <input
          type="file"
          accept="video/*"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
      </label>

      <button
        onClick={handleUpload}
        disabled={uploading}
        style={{
          padding: "0.5rem 1.1rem",
          backgroundColor: uploading ? "#444" : "#E50914",
          border: "none",
          color: "#fff",
          cursor: uploading ? "not-allowed" : "pointer",
          borderRadius: "999px",
          fontWeight: "bold",
          fontSize: "0.85rem",
          boxShadow: uploading
            ? "none"
            : "0 8px 18px rgba(229,9,20,0.35)",
          transition: "background 0.15s, transform 0.08s, box-shadow 0.15s",
        }}
      >
        {uploading ? "Analyzing…" : "Upload & Analyze"}
      </button>

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
    </div>
  );
}
