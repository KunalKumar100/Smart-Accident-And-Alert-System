// src/App.jsx
import { useState } from "react";
import IncidentTable from "./IncidentTable";
import VideoUpload from "./VideoUpload";
import LiveCamera from "./LiveCamera";

export default function App() {
  const [reloadKey, setReloadKey] = useState(0);
  const [newIncidentIds, setNewIncidentIds] = useState([]);
  const [mode, setMode] = useState("video"); // "video" | "live"

  // Called when FastAPI (video or live) creates incidents
  const handleIncidentsCreated = (result) => {
    console.log("Analysis result from FastAPI:", result);

    const ids = result?.incident_ids || [];
    if (!ids.length) return;

    setNewIncidentIds(ids);
    setReloadKey((prev) => prev + 1); // trigger IncidentTable reload
  };

  const containerStyle = {
    minHeight: "100vh",
    width: "100vw",
    margin: 0,
    padding: 0,
    overflowX: "hidden",
    background:
      "radial-gradient(circle at top left, #1f1f1f 0, #050505 45%, #000 100%)",
    color: "#fff",
    fontFamily:
      "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  };

  const headerStyle = {
    padding: "1rem 2.5rem",
    borderBottom: "1px solid #222",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    backdropFilter: "blur(8px)",
    position: "sticky",
    top: 0,
    zIndex: 10,
    background: "rgba(0,0,0,0.85)",
  };

  return (
    <div style={containerStyle}>
      {/* Top header */}
      <header style={headerStyle}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background:
                "linear-gradient(135deg, #E50914 0%, #ff6b6b 50%, #ffc371 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: "900",
              fontSize: "1rem",
            }}
          >
            SA
          </div>
          <div>
            <h1
              style={{
                color: "#ffffff",
                margin: 0,
                fontSize: "1.4rem",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              Smart Accident Response
            </h1>
            <p
              style={{
                margin: 0,
                fontSize: "0.8rem",
                color: "#bbbbbb",
              }}
            >
              Live AI monitoring · Incident logging · Snapshot intelligence
            </p>
          </div>
        </div>

        {/* Mode Switch Buttons */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            backgroundColor: "#181818",
            padding: "0.25rem",
            borderRadius: "999px",
            border: "1px solid #333",
          }}
        >
          <button
            onClick={() => setMode("video")}
            style={{
              padding: "0.35rem 0.9rem",
              borderRadius: "999px",
              border: "none",
              cursor: "pointer",
              backgroundColor: mode === "video" ? "#E50914" : "transparent",
              color: "#fff",
              fontWeight: 600,
              fontSize: "0.8rem",
              transition: "background 0.2s, transform 0.1s",
            }}
          >
            Pre-recorded
          </button>
          <button
            onClick={() => setMode("live")}
            style={{
              padding: "0.35rem 0.9rem",
              borderRadius: "999px",
              border: "none",
              cursor: "pointer",
              backgroundColor: mode === "live" ? "#E50914" : "transparent",
              color: "#fff",
              fontWeight: 600,
              fontSize: "0.8rem",
              transition: "background 0.2s, transform 0.1s",
            }}
          >
            Live Camera
          </button>
        </div>
      </header>

      {/* Notification banner when new incidents are created */}
      {newIncidentIds.length > 0 && (
        <div
          style={{
            margin: "1rem 2.5rem 0",
            padding: "0.7rem 1rem",
            borderRadius: 8,
            border: "1px solid #E50914",
            background:
              "linear-gradient(90deg, rgba(229,9,20,0.15), rgba(0,0,0,0.8))",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
          }}
        >
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 22,
              height: 22,
              borderRadius: "50%",
              backgroundColor: "#E50914",
              fontSize: "0.8rem",
              fontWeight: 700,
            }}
          >
            !
          </span>
          <div style={{ fontSize: "0.85rem" }}>
            <strong>New incident(s) logged:</strong>{" "}
            <span style={{ opacity: 0.9 }}>{newIncidentIds.join(", ")}</span>
          </div>
        </div>
      )}

      {/* Main content grid – right side wider now */}
      <main
        style={{
          margin: "1.5rem 2.5rem 2rem",
          display: "grid",
          gridTemplateColumns: "minmax(0, 0.9fr) minmax(0, 2.1fr)", // <— changed
          gap: "1.5rem",
        }}
      >
        {/* Left Card: Controls */}
        <section
          style={{
            background: "rgba(15,15,15,0.95)",
            padding: "1rem",
            borderRadius: 16,
            border: "1px solid #262626",
            boxShadow: "0 20px 45px rgba(0,0,0,0.7)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "0.6rem",
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: "1.05rem",
                color: "#f5f5f5",
              }}
            >
              {mode === "video" ? "Pre-recorded Analysis" : "Live Camera Feed"}
            </h2>
            <span
              style={{
                fontSize: "0.7rem",
                padding: "0.1rem 0.5rem",
                borderRadius: 999,
                backgroundColor: "#222",
                border: "1px solid #333",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "#aaaaaa",
              }}
            >
              {mode === "video" ? "upload mode" : "live mode"}
            </span>
          </div>

          <p style={{ fontSize: "0.8rem", color: "#a0a0a0", marginTop: 0 }}>
            {mode === "video"
              ? "Upload incident footage to run AI-assisted analysis and log new incidents."
              : "Stream from your webcam and let YOLO automatically detect accident-like scenarios in real time."}
          </p>

          <div style={{ marginTop: "0.75rem" }}>
            {mode === "video" ? (
              <VideoUpload onAnalyzed={handleIncidentsCreated} />
            ) : (
              <LiveCamera onIncident={handleIncidentsCreated} />
            )}
          </div>
        </section>

        {/* Right Card: Incident Table */}
        <section
          style={{
            background: "rgba(10,10,10,0.95)",
            borderRadius: 16,
            border: "1px solid #262626",
            boxShadow: "0 20px 45px rgba(0,0,0,0.8)",
          }}
        >
          <IncidentTable
            reloadKey={reloadKey}
            newIncidentIds={newIncidentIds}
          />
        </section>
      </main>
    </div>
  );
}
