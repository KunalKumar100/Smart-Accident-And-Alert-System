import { useEffect, useState } from "react";
import axios from "axios";

function getSeverityBadge(severity) {
  const baseStyle = {
    padding: "4px 10px",
    borderRadius: "999px",
    fontSize: "0.7rem",
    fontWeight: "bold",
    color: "#fff",
    textTransform: "uppercase",
    boxShadow: "0px 0px 5px rgba(0,0,0,0.4)",
    letterSpacing: "0.06em",
  };

  switch (severity) {
    case "CRITICAL":
      return { ...baseStyle, backgroundColor: "#b71c1c" };
    case "MAJOR":
      return { ...baseStyle, backgroundColor: "#e65100" };
    case "MEDIUM":
      return { ...baseStyle, backgroundColor: "#fbc02d", color: "#000" };
    case "MINOR":
      return { ...baseStyle, backgroundColor: "#2e7d32" };
    default:
      return { ...baseStyle, backgroundColor: "#616161" };
  }
}

export default function IncidentTable({ reloadKey, newIncidentIds = [] }) {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchIncidents = () => {
    setLoading(true);
    axios
      .get("http://localhost:8080/api/incidents")
      .then((res) => setIncidents(res.data))
      .catch((err) => console.error("Error fetching incidents:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchIncidents();
  }, [reloadKey]);

  return (
    <div
      style={{
        padding: "1.2rem 1.2rem 1.4rem",
        backgroundColor: "#101010",
        borderRadius: 16,
        height: "100%",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: "0.75rem",
        }}
      >
        <h2
          style={{
            color: "#ffffff",
            fontSize: "1.1rem",
            margin: 0,
          }}
        >
          Detected Incidents
        </h2>
        <span
          style={{
            fontSize: "0.75rem",
            color: "#aaaaaa",
          }}
        >
          Total: {incidents.length}
        </span>
      </div>

      {loading && (
        <p style={{ fontSize: "0.85rem", color: "#bbbbbb" }}>
          Loading incidents…
        </p>
      )}

      {!loading && incidents.length === 0 ? (
        <p style={{ fontSize: "0.85rem", color: "#999" }}>
          No incidents recorded yet. Try uploading a video or using Live Camera.
        </p>
      ) : (
        !loading && (
          <div style={{ overflowX: "auto", maxHeight: "430px" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                backgroundColor: "#141414",
                color: "#fff",
                fontSize: "0.8rem",
              }}
            >
              <thead>
                <tr style={{ backgroundColor: "#181818" }}>
                  {[
                    "ID",
                    "Snapshot",
                    "Camera",
                    "Severity",
                    "Victims",
                    "Status",
                    "Time",
                  ].map((header) => (
                    <th
                      key={header}
                      style={{
                        padding: "10px 8px",
                        borderBottom: "1px solid #333",
                        color: "#E5E5E5",
                        textAlign: "left",
                        fontSize: "0.75rem",
                        textTransform: "uppercase",
                        letterSpacing: "0.08em",
                      }}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {incidents.map((i, index) => {
                  const isNew = newIncidentIds.includes(i.id);
                  const rowBg =
                    index % 2 === 0 ? "rgba(255,255,255,0.01)" : "transparent";
                  return (
                    <tr
                      key={i.id}
                      style={{
                        background: isNew
                          ? "linear-gradient(90deg, rgba(229,9,20,0.18), rgba(0,0,0,0))"
                          : rowBg,
                        borderBottom: "1px solid #262626",
                        transition: "background 0.15s, transform 0.08s",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = "translateY(-1px)";
                        e.currentTarget.style.background =
                          isNew
                            ? "linear-gradient(90deg, rgba(229,9,20,0.24), rgba(0,0,0,0.3))"
                            : "rgba(255,255,255,0.03)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = "translateY(0)";
                        e.currentTarget.style.background = isNew
                          ? "linear-gradient(90deg, rgba(229,9,20,0.18), rgba(0,0,0,0))"
                          : rowBg;
                      }}
                    >
                      {/* ID + NEW badge */}
                      <td style={{ padding: "9px 8px", whiteSpace: "nowrap" }}>
                        {i.id}
                        {isNew && (
                          <span
                            style={{
                              marginLeft: 6,
                              padding: "2px 6px",
                              backgroundColor: "#E50914",
                              color: "#fff",
                              borderRadius: "999px",
                              fontSize: "0.65rem",
                              textTransform: "uppercase",
                            }}
                          >
                            New
                          </span>
                        )}
                      </td>

                      {/* Snapshot thumbnail */}
                      <td style={{ padding: "9px 8px" }}>
                        {i.snapshotUrl ? (
                          <img
                            src={i.snapshotUrl}
                            alt={`Incident ${i.id}`}
                            width={80}
                            style={{
                              borderRadius: 6,
                              cursor: "pointer",
                              border: "1px solid #444",
                              display: "block",
                              maxHeight: 50,
                              objectFit: "cover",
                            }}
                            onClick={() =>
                              window.open(i.snapshotUrl, "_blank")
                            }
                          />
                        ) : (
                          <span style={{ opacity: 0.55 }}>No image</span>
                        )}
                      </td>

                      {/* Camera */}
                      <td style={{ padding: "9px 8px" }}>
                        {i.cameraName || "—"}
                      </td>

                      {/* Severity badge */}
                      <td style={{ padding: "9px 8px" }}>
                        <span style={getSeverityBadge(i.severity)}>
                          {i.severity}
                        </span>
                      </td>

                      {/* Victims */}
                      <td style={{ padding: "9px 8px" }}>{i.victimCount}</td>

                      {/* Status */}
                      <td style={{ padding: "9px 8px" }}>
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "999px",
                            border: "1px solid #444",
                            fontSize: "0.65rem",
                            letterSpacing: "0.05em",
                            textTransform: "uppercase",
                            color: "#ccc",
                          }}
                        >
                          {i.status}
                        </span>
                      </td>

                      {/* Time */}
                      <td style={{ padding: "9px 8px", whiteSpace: "nowrap" }}>
                        {i.timestamp
                          ? new Date(i.timestamp).toLocaleString()
                          : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  );
}
  