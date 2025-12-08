import requests
from datetime import datetime
from typing import Optional, Dict, Any

JAVA_BACKEND_URL = "http://localhost:8080/api/incidents/ingest"


def send_incident_to_backend(
    camera_id: str,
    severity: str,
    victims: int,
    source: str,
    location_lat: float,
    location_lng: float,
    snapshot_url: Optional[str],
    time: datetime,
    likely_injuries: Optional[Dict[str, Any]] = None,
    doctor_report_summary: Optional[str] = None,
):
    """Sends an incident JSON to the Spring Boot backend and returns parsed JSON response."""

    if time.tzinfo:
        ts_iso = time.astimezone().isoformat()
    else:
        ts_iso = time.isoformat() + "Z"

    payload = {
        "accident": True,
        "cameraId": camera_id,
        "timestamp": ts_iso,
        "severity": severity,
        "victimCount": victims,
        "location": {
            "lat": location_lat,
            "lng": location_lng,
        },
        "snapshotUrl": snapshot_url,
        "source": source,
    }

    if likely_injuries is not None:
        payload["likelyInjuries"] = likely_injuries

    if doctor_report_summary is not None:
        payload["doctorReportSummary"] = doctor_report_summary

    print("[PY→JAVA] Sending payload:", payload)

    try:
        resp = requests.post(JAVA_BACKEND_URL, json=payload, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        print("[JAVA→PY] Response:", data)
        return data
    except Exception as e:
        print(f"[ERROR] Failed to send incident to backend: {e}")
        return None
