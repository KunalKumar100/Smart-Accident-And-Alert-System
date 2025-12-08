from pydantic import BaseModel
from typing import List, Optional,Dict
from datetime import datetime


# -------- Location DTO (matches Java IncidentIngestRequest.location) --------
class Location(BaseModel):
    lat: float
    lng: float


# -------- Python → Java Request DTO (matches IncidentIngestRequest in Java) --------
class IncidentIngestRequest(BaseModel):
    accident: bool
    cameraId: str
    timestamp: str   # ISO string, ex: "2025-11-29T11:05:00Z"
    severity: str
    victimCount: int
    likelyInjuries: List[str] = []
    location: Location
    snapshotUrl: Optional[str] = None


# -------- Live Camera Request (for /detect-accident) --------
class LiveAccidentRequest(BaseModel):
    camera_id: str
    frame_id: Optional[str] = None
    timestamp: Optional[datetime] = None


# -------- Response model for /analyze-video --------
class VideoAnalysisResponse(BaseModel):
    message: str
    accidents_detected: int
    incident_ids: List[int]
     # 👈 NEW: raw Java response for debugging
