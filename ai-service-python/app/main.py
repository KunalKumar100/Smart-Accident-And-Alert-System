import os
import uuid
import time
from collections import deque
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .schemas import VideoAnalysisResponse
from .services.accident_client import send_incident_to_backend
from .ai_model import get_model  # YOLO loader

app = FastAPI(
    title="AI Accident Detection Service",
    description="FastAPI microservice for accident detection in live and pre-recorded video.",
    version="1.4.0",
)

# ----- CORS so React (Vite) can call this service -----
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories to save uploaded videos and snapshots
VIDEO_SAVE_DIR = "uploaded_videos"
SNAPSHOT_DIR = "snapshots"

os.makedirs(VIDEO_SAVE_DIR, exist_ok=True)
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# --------- Detection tuning / heuristics ---------
CONF_THRESH = 0.3  # slightly relaxed to catch more detections

# --------- Temporal logic & cooldown (LIVE) ---------
ACCIDENT_CONFIRM_FRAMES = 3        # wait a bit deeper into accident
FRAME_BUFFER_SIZE = 30
ALERT_COOLDOWN_SECONDS = 60        # avoid duplicate alerts for same accident

# --------- Multi-snapshot config (used for BOTH live & video) ---------
PRE_SNAPSHOT_COUNT = 5             # how many frames BEFORE accident to save
POST_CAPTURE_SECONDS = 5           # conceptual 5 seconds
POST_CAPTURE_FPS = 5               # ~5 frames per second
POST_CAPTURE_FRAMES = POST_CAPTURE_SECONDS * POST_CAPTURE_FPS  # ~25 frames

# --------- Temporal logic for pre-recorded video ---------
VIDEO_CONFIRM_FRAMES = 3           # require 3 consecutive accident frames

# Per-camera state (in-memory) for LIVE
camera_states: Dict[str, Dict[str, Any]] = {}


def get_camera_state(camera_id: str) -> Dict[str, Any]:
    """
    Returns (and initializes if needed) the state dict for a given camera.
    Used for temporal smoothing, multi-snapshot capture, and cooldown handling in LIVE mode.
    """
    if camera_id not in camera_states:
        camera_states[camera_id] = {
            "accident_counter": 0,
            "frame_buffer": deque(maxlen=FRAME_BUFFER_SIZE),
            # stores recent accident frames with severity, overlap & snapshot
            "candidate_frames": deque(maxlen=15),
            "last_alert_time": 0.0,
            # post-accident multi-frame capture
            "post_capture_remaining": 0,
            "post_capture_counter": 0,
            "current_incident_tag": None,  # used to group snapshots by incident
        }
    return camera_states[camera_id]


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve snapshots as static files
# URL: http://localhost:8000/snapshots/<filename>.jpg
app.mount("/snapshots", StaticFiles(directory=SNAPSHOT_DIR), name="snapshots")


# ==========================
# Helper: bounding box overlap (bool)
# ==========================
def boxes_overlap(box1, box2) -> bool:
    """
    Check if two YOLO bounding boxes (x1, y1, x2, y2) overlap.
    box1, box2 are 1D arrays or lists: [x1, y1, x2, y2]
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    if x1_max < x2_min or x2_max < x1_min:
        return False
    if y1_max < y2_min or y2_max < y1_min:
        return False
    return True



# Helper: max IoU overlap ratio between any two boxes

def compute_max_overlap_ratio(boxes: List[np.ndarray]) -> float:
    """
    Compute the maximum IoU (Intersection over Union) between any two boxes.
    Boxes are [x1, y1, x2, y2].
    Returns value in [0, 1].
    """
    n = len(boxes)
    if n < 2:
        return 0.0

    max_ratio = 0.0
    for i in range(n):
        x1_min, y1_min, x1_max, y1_max = boxes[i]
        area1 = max(0.0, (x1_max - x1_min)) * max(0.0, (y1_max - y1_min))
        if area1 <= 0:
            continue
        for j in range(i + 1, n):
            x2_min, y2_min, x2_max, y2_max = boxes[j]
            area2 = max(0.0, (x2_max - x2_min)) * max(0.0, (y2_max - y2_min))
            if area2 <= 0:
                continue

            ix_min = max(x1_min, x2_min)
            iy_min = max(y1_min, y2_min)
            ix_max = min(x1_max, x2_max)
            iy_max = min(y1_max, y2_max)

            iw = max(0.0, ix_max - ix_min)
            ih = max(0.0, iy_max - iy_min)
            inter = iw * ih
            if inter <= 0:
                continue
            union = area1 + area2 - inter
            if union <= 0:
                continue

            ratio = inter / union
            if ratio > max_ratio:
                max_ratio = ratio
    return float(max_ratio)


# ==========================
# Helper: build AI injury report + doctor summary
# ==========================
def build_expected_injury_report(
    severity: str,
    vehicle_type: Optional[str],
    victim_count: int,
    collision_detected: bool,
    person_count: int,
) -> Dict[str, Any]:
    """
    Simple rule-based injury estimation using severity, vehicle presence, and people count.
    Returns a dict that will be stored as JSON in Java backend.
    """

    report: Dict[str, Any] = {
        "priorityLevel": "LOW",
        "mechanismOfInjury": "",
        "estimatedInjuries": [],
        "victimInfo": {
            "estimatedVictims": victim_count,
            "posture": "unknown",
        },
        "recommendedPreparation": [],
        "summaryForDoctors": "",
    }

    # --- Priority level ---
    if severity == "CRITICAL":
        report["priorityLevel"] = "CRITICAL"
    elif severity == "MAJOR":
        report["priorityLevel"] = "HIGH"
    elif severity == "MEDIUM":
        report["priorityLevel"] = "MODERATE"
    else:
        report["priorityLevel"] = "LOW"

    # --- Mechanism of injury text ---
    mech_parts = []
    if collision_detected:
        mech_parts.append("collision detected")
    if vehicle_type:
        mech_parts.append(f"involving a {vehicle_type}")
    if person_count > 0:
        mech_parts.append(f"{person_count} person(s) in scene")

    report["mechanismOfInjury"] = ", ".join(mech_parts) or "Road traffic accident"

    # --- Injury region risks ---
    injuries = []

    if severity in ("MAJOR", "CRITICAL"):
        injuries.append({"region": "Head/Neck", "risk": "HIGH"})
        injuries.append({"region": "Chest", "risk": "MEDIUM"})
        injuries.append({"region": "Limbs", "risk": "MEDIUM"})
    elif severity == "MEDIUM":
        injuries.append({"region": "Head/Neck", "risk": "MEDIUM"})
        injuries.append({"region": "Limbs", "risk": "MEDIUM"})
    else:
        injuries.append({"region": "Head/Neck", "risk": "LOW"})
        injuries.append({"region": "Limbs", "risk": "LOW"})

    if victim_count >= 2:
        injuries.append({"region": "Pelvis/Spine", "risk": "MEDIUM"})

    report["estimatedInjuries"] = injuries

    # --- Recommended preparation ---
    prep: List[str] = []
    if report["priorityLevel"] in ("HIGH", "CRITICAL"):
        prep.extend(
            [
                "Activate trauma team",
                "Prepare CT scan and X-ray",
                "Prepare IV fluids and blood units",
            ]
        )
    elif report["priorityLevel"] == "MODERATE":
        prep.append("Prepare emergency doctor and X-ray")
    else:
        prep.append("Basic emergency assessment")

    report["recommendedPreparation"] = prep

    # --- Summary for doctors ---
    at_risk_regions = [i["region"] for i in injuries if i["risk"] in ("HIGH", "MEDIUM")]
    regions_text = ", ".join(at_risk_regions) if at_risk_regions else "no major regions identified"

    report["summaryForDoctors"] = (
        f"{report['mechanismOfInjury']} with {victim_count} victim(s). "
        f"Estimated increased risk of injuries to: {regions_text}. "
        f"Recommended: {', '.join(prep)}."
    )

    return report


# LIVE CAMERA MODE

@app.post("/detect-accident", response_model=VideoAnalysisResponse)
async def detect_accident(
    frame: UploadFile = File(...),
    camera_id: str = Form("LIVE_CAM_1"),
):
    """
    Live accident detection endpoint for webcam / IP camera snapshots.
    Uses:
    - temporal smoothing (ACCIDENT_CONFIRM_FRAMES consecutive accident frames)
    - candidate_frames buffer to choose BEST accident snapshot
      (by severity + overlap_ratio)
    - multi-snapshot: pre-accident (from buffer) + post-accident (next N frames)
    - per-camera cooldown to avoid duplicate alerts
    """

    # Read uploaded frame contents
    content = await frame.read()

    # Convert bytes -> OpenCV image (BGR)
    nparr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        print("[ERROR LIVE] Could not decode image from frame upload.")
        return VideoAnalysisResponse(
            message="Could not decode frame.",
            accidents_detected=0,
            incident_ids=[],
        )

    # Get per-camera state
    state = get_camera_state(camera_id)
    state["frame_buffer"].append(img)

    # --- POST-ACCIDENT SNAPSHOTS (for previous confirmed incident) ---
    if state["post_capture_remaining"] > 0 and state["current_incident_tag"] is not None:
        try:
            post_idx = state["post_capture_counter"]
            post_filename = f"accident_post_{state['current_incident_tag']}_{post_idx}.jpg"
            post_path = os.path.join(SNAPSHOT_DIR, post_filename)
            cv2.imwrite(post_path, img)
            state["post_capture_remaining"] -= 1
            state["post_capture_counter"] += 1
            print(f"[LIVE] Post-accident snapshot saved: {post_path} "
                  f"(remaining={state['post_capture_remaining']})")
        except Exception as e:
            print(f"[ERROR LIVE] Could not save post-accident snapshot: {e}")

    # Run YOLO inference for current frame
    model = get_model()
    results = model.predict(source=img, verbose=False)
    r = results[0]
    names = r.names

    # --- Count objects + detect collisions ---
    danger_class_names = {"person", "car", "truck", "motorcycle", "bus"}
    vehicle_classes = {"car", "truck", "motorcycle", "bus"}
    person_classes = {"person"}

    vehicle_count = 0
    person_count = 0
    collision_detected = False
    total_danger_detections = 0
    primary_vehicle_type: Optional[str] = None

    filtered_boxes_xyxy: List[np.ndarray] = []

    if r.boxes is not None and len(r.boxes) > 0:
        boxes = r.boxes

        for i in range(len(boxes)):
            cls_id = int(boxes[i].cls[0])
            cls_name = names.get(cls_id, "")

            score = float(boxes[i].conf[0])
            if score < CONF_THRESH:
                continue

            box_xyxy = boxes[i].xyxy[0].cpu().numpy()
            filtered_boxes_xyxy.append(box_xyxy)

            if cls_name in danger_class_names:
                total_danger_detections += 1
            if cls_name in vehicle_classes:
                vehicle_count += 1
                if primary_vehicle_type is None:
                    primary_vehicle_type = cls_name
            if cls_name in person_classes:
                person_count += 1

        for i in range(len(filtered_boxes_xyxy)):
            for j in range(i + 1, len(filtered_boxes_xyxy)):
                box1 = filtered_boxes_xyxy[i]
                box2 = filtered_boxes_xyxy[j]
                if boxes_overlap(box1, box2):
                    collision_detected = True
                    break
            if collision_detected:
                break

    # NEW: how strong is the overlap in this frame?
    max_overlap_ratio = compute_max_overlap_ratio(filtered_boxes_xyxy)

    print(
        f"[LIVE] danger={total_danger_detections}, vehicles={vehicle_count}, "
        f"persons={person_count}, collision={collision_detected}, "
        f"overlap_ratio={max_overlap_ratio:.3f} from {camera_id}"
    )

    # --- Single-frame accident decision ---
    accident_detected_frame = False
    if collision_detected and vehicle_count >= 2:
        accident_detected_frame = True
    elif collision_detected and person_count >= 1:
        accident_detected_frame = True
    elif vehicle_count >= 1 and person_count >= 1 and total_danger_detections >= 3:
        accident_detected_frame = True

    # --- Compute severity for THIS frame ---
    if collision_detected and vehicle_count >= 2:
        severity = "CRITICAL"
    elif collision_detected and person_count >= 1:
        severity = "MAJOR"
    elif vehicle_count >= 1 and person_count >= 2:
        severity = "MEDIUM"
    else:
        severity = "MINOR"

    severity_order = {"MINOR": 1, "MEDIUM": 2, "MAJOR": 3, "CRITICAL": 4}
    severity_score = severity_order.get(severity, 1)
    victims_estimated = person_count if person_count > 0 else 1

    # --- If this frame is accident → add to candidate_frames ---
    if accident_detected_frame:
        try:
            annotated_img = r.plot()  # YOLO's plotted boxes (BGR)
        except Exception as e:
            print(f"[WARN LIVE] Could not plot annotated frame: {e}")
            annotated_img = img.copy()

        state["candidate_frames"].append(
            {
                "severity": severity,
                "severity_score": severity_score,
                "overlap_ratio": max_overlap_ratio,
                "victims_estimated": victims_estimated,
                "person_count": person_count,
                "collision_detected": collision_detected,
                "primary_vehicle_type": primary_vehicle_type,
                "annotated_img": annotated_img,
            }
        )
        state["accident_counter"] += 1
    else:
        state["accident_counter"] = 0

    # --- Temporal confirmation ---
    final_decision = state["accident_counter"] >= ACCIDENT_CONFIRM_FRAMES

    # --- Cooldown logic ---
    now_ts = time.time()
    time_since_last_alert = now_ts - state["last_alert_time"] if state["last_alert_time"] else 9999
    in_cooldown = time_since_last_alert < ALERT_COOLDOWN_SECONDS

    if not final_decision:
        return VideoAnalysisResponse(
            message="No accident detected (temporal-smoothed).",
            accidents_detected=0,
            incident_ids=[],
        )

    if in_cooldown:
        print(f"[LIVE] Accident confirmed but in cooldown for {camera_id}. Skipping backend send.")
        return VideoAnalysisResponse(
            message="Accident already reported recently (cooldown active).",
            accidents_detected=0,
            incident_ids=[],
        )

    # --- Choose BEST frame from candidate_frames (severity + overlap) ---
    best_frame_data = None
    if state["candidate_frames"]:
        best_frame_data = max(
            state["candidate_frames"],
            key=lambda f: (f["severity_score"], f["overlap_ratio"])
        )

    if best_frame_data is None:
        print("[WARN LIVE] No candidate_frames; using current frame as best.")
        try:
            annotated_img_final = r.plot()
        except Exception:
            annotated_img_final = img.copy()
        best_severity = severity
        best_victims = victims_estimated
        best_collision = collision_detected
        best_person_count = person_count
        best_vehicle_type = primary_vehicle_type
    else:
        annotated_img_final = best_frame_data["annotated_img"]
        best_severity = best_frame_data["severity"]
        best_victims = best_frame_data["victims_estimated"]
        best_collision = best_frame_data["collision_detected"]
        best_person_count = best_frame_data["person_count"]
        best_vehicle_type = best_frame_data["primary_vehicle_type"]

    # --- Build AI Injury Report for BEST frame ---
    injury_report = build_expected_injury_report(
        severity=best_severity,
        vehicle_type=best_vehicle_type,
        victim_count=best_victims,
        collision_detected=best_collision,
        person_count=best_person_count,
    )

    # --- Generate incident tag to group snapshots ---
    incident_tag = f"{camera_id}_{int(now_ts)}"
    state["current_incident_tag"] = incident_tag

    # --- SAVE PRE-ACCIDENT SNAPSHOTS (raw frames from buffer) ---
    incident_ids: List[int] = []
    accidents_detected = 0

    try:
        pre_frames = list(state["frame_buffer"])[-PRE_SNAPSHOT_COUNT:]
        for idx, pre_img in enumerate(pre_frames):
            pre_filename = f"accident_pre_{incident_tag}_{idx}.jpg"
            pre_path = os.path.join(SNAPSHOT_DIR, pre_filename)
            cv2.imwrite(pre_path, pre_img)
        if pre_frames:
            print(f"[LIVE] Saved {len(pre_frames)} pre-accident snapshots for {incident_tag}")
    except Exception as e:
        print(f"[ERROR LIVE] Could not save pre-accident snapshots: {e}")

    # --- SAVE MAIN IMPACT SNAPSHOT (best annotated frame) ---
    try:
        snapshot_filename = f"accident_main_{incident_tag}_{uuid.uuid4()}.jpg"
        snapshot_path = os.path.join(SNAPSHOT_DIR, snapshot_filename)
        cv2.imwrite(snapshot_path, annotated_img_final)
        snapshot_url = f"http://localhost:8000/snapshots/{snapshot_filename}"
        print(f"[LIVE] Main accident snapshot saved at {snapshot_path}, URL={snapshot_url}")
    except Exception as e:
        print(f"[ERROR LIVE] Could not save main snapshot: {e}")
        snapshot_url = None

    # --- START POST-ACCIDENT CAPTURE (next N frames) ---
    state["post_capture_remaining"] = POST_CAPTURE_FRAMES
    state["post_capture_counter"] = 0
    print(
        f"[LIVE] Starting post-accident capture for {incident_tag}: "
        f"{POST_CAPTURE_FRAMES} frames (~{POST_CAPTURE_SECONDS}s at {POST_CAPTURE_FPS} fps)"
    )

    # --- Send incident to Java backend ---
    try:
        now = datetime.now(timezone.utc)

        backend_incident = send_incident_to_backend(
            camera_id=camera_id,
            severity=best_severity,
            victims=best_victims,
            source="LIVE_YOLO",
            location_lat=19.0,
            location_lng=73.0,
            snapshot_url=snapshot_url,
            time=now,
            likely_injuries=injury_report,
            doctor_report_summary=injury_report["summaryForDoctors"],
        )

        if backend_incident:
            print("[PY LIVE] Backend incident JSON:", backend_incident)

            incident_id = None
            if isinstance(backend_incident, dict):
                if "id" in backend_incident:
                    incident_id = backend_incident["id"]
                elif "incidentId" in backend_incident:
                    incident_id = backend_incident["incidentId"]
                elif "incident_id" in backend_incident:
                    incident_id = backend_incident["incident_id"]

            if incident_id is not None:
                try:
                    incident_ids.append(int(incident_id))
                    accidents_detected = 1
                except (ValueError, TypeError):
                    print(f"[WARN LIVE] Could not convert incident_id={incident_id} to int")

        # cooldown & reset per-incident state
        state["last_alert_time"] = now_ts
        state["accident_counter"] = 0
        state["candidate_frames"].clear()

    except Exception as e:
        print(f"[ERROR LIVE] While sending incident to backend: {e}")

    return VideoAnalysisResponse(
        message=f"Live accident confirmed. Severity={best_severity}.",
        accidents_detected=accidents_detected,
        incident_ids=incident_ids,
    )



# PRE-RECORDED VIDEO MODE

@app.post("/analyze-video", response_model=VideoAnalysisResponse)
async def analyze_video(file: UploadFile = File(...)):
    """
    Accepts a video file, stores it, then analyzes multiple frames using YOLO.
    - Pass 1: detect confirmed accident frames and find BEST (max severity + overlap) frame.
    - Pass 2: around that best frame, save:
        - PRE_SNAPSHOT_COUNT pre-accident frames
        - 1 main impact annotated frame
        - POST_CAPTURE_FRAMES post-accident frames
    - Sends incident to Java backend with main snapshot URL.
    """

    # ---- Save file to disk ----
    file_extension = os.path.splitext(file.filename)[1]
    video_id = str(uuid.uuid4())
    saved_filename = f"{video_id}{file_extension}"
    saved_path = os.path.join(VIDEO_SAVE_DIR, saved_filename)

    try:
        with open(saved_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        print(f"[ERROR VIDEO] Could not save video: {e}")
        raise HTTPException(status_code=500, detail="Could not save video")

    print(f"[VIDEO] Saved file to {saved_path}")

    
    # PASS 1: detect best accident frame index
    
    cap = cv2.VideoCapture(saved_path)
    if not cap.isOpened():
        print(f"[ERROR VIDEO] Could not open video file: {saved_path}")
        raise HTTPException(status_code=500, detail="Could not open video")

    model = get_model()

    FRAME_STEP = 3  # analyze every 3rd frame
    frame_index = 0

    severity_order = {"MINOR": 1, "MEDIUM": 2, "MAJOR": 3, "CRITICAL": 4}

    best_severity = "MINOR"
    best_severity_score = 0
    best_overlap_ratio = 0.0
    best_victims = 0
    best_person_count = 0
    best_collision = False
    best_vehicle_type: Optional[str] = None
    best_annotated_frame: Optional[np.ndarray] = None
    best_frame_index: Optional[int] = None

    accident_frames_total = 0

    danger_class_names = {"person", "car", "truck", "motorcycle", "bus"}
    vehicle_classes = {"car", "truck", "motorcycle", "bus"}
    person_classes = {"person"}

    video_accident_counter = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_index += 1
        if frame_index % FRAME_STEP != 0:
            continue  # skip this frame for detection

        # Run YOLO on this frame
        results = model.predict(source=frame, verbose=False)
        r = results[0]
        names = r.names

        vehicle_count = 0
        person_count = 0
        collision_detected = False
        total_danger_detections = 0
        primary_vehicle_type: Optional[str] = None
        filtered_boxes_xyxy: List[np.ndarray] = []

        if r.boxes is not None and len(r.boxes) > 0:
            boxes = r.boxes

            for i in range(len(boxes)):
                cls_id = int(boxes[i].cls[0])
                cls_name = names.get(cls_id, "")

                score = float(boxes[i].conf[0])
                if score < CONF_THRESH:
                    continue

                box_xyxy = boxes[i].xyxy[0].cpu().numpy()
                filtered_boxes_xyxy.append(box_xyxy)

                if cls_name in danger_class_names:
                    total_danger_detections += 1
                if cls_name in vehicle_classes:
                    vehicle_count += 1
                    if primary_vehicle_type is None:
                        primary_vehicle_type = cls_name
                if cls_name in person_classes:
                    person_count += 1

            for i in range(len(filtered_boxes_xyxy)):
                for j in range(i + 1, len(filtered_boxes_xyxy)):
                    box1 = filtered_boxes_xyxy[i]
                    box2 = filtered_boxes_xyxy[j]
                    if boxes_overlap(box1, box2):
                        collision_detected = True
                        break
                if collision_detected:
                    break

        max_overlap_ratio = compute_max_overlap_ratio(filtered_boxes_xyxy)

        # Single-frame decision
        accident_detected_frame = False
        if collision_detected and vehicle_count >= 2:
            accident_detected_frame = True
        elif collision_detected and person_count >= 1:
            accident_detected_frame = True
        elif vehicle_count >= 1 and person_count >= 1 and total_danger_detections >= 3:
            accident_detected_frame = True

        # Temporal confirmation for video
        if accident_detected_frame:
            video_accident_counter += 1
        else:
            video_accident_counter = 0

        if video_accident_counter < VIDEO_CONFIRM_FRAMES:
            continue

        # Confirmed accident frame
        accident_frames_total += 1

        # Compute severity for this frame
        if collision_detected and vehicle_count >= 2:
            severity = "CRITICAL"
        elif collision_detected and person_count >= 1:
            severity = "MAJOR"
        elif vehicle_count >= 1 and person_count >= 2:
            severity = "MEDIUM"
        else:
            severity = "MINOR"

        severity_score = severity_order.get(severity, 1)
        victims_estimated = person_count if person_count > 0 else 1

        # Keep the "worst" confirmed accident frame
        # Priority: severity_score, then overlap_ratio
        is_better = False
        if severity_score > best_severity_score:
            is_better = True
        elif severity_score == best_severity_score and max_overlap_ratio > best_overlap_ratio:
            is_better = True

        if is_better:
            best_severity_score = severity_score
            best_severity = severity
            best_overlap_ratio = max_overlap_ratio
            best_victims = victims_estimated
            best_person_count = person_count
            best_collision = collision_detected
            best_vehicle_type = primary_vehicle_type
            best_frame_index = frame_index
            try:
                best_annotated_frame = r.plot()
            except Exception as e:
                print(f"[WARN VIDEO] Could not plot annotated frame: {e}")
                best_annotated_frame = None

    cap.release()

    if best_severity_score == 0 or best_frame_index is None:
        return VideoAnalysisResponse(
            message="No accident detected in video.",
            accidents_detected=0,
            incident_ids=[],
        )

    print(
        f"[VIDEO] Accident detected in {accident_frames_total} confirmed frame(s). "
        f"Max severity={best_severity}, victims={best_victims}, "
        f"best_frame_index={best_frame_index}, best_overlap={best_overlap_ratio:.3f}"
    )

    # Build injury report for worst frame
    injury_report = build_expected_injury_report(
        severity=best_severity,
        vehicle_type=best_vehicle_type,
        victim_count=best_victims,
        collision_detected=best_collision,
        person_count=best_person_count,
    )

    
    # PASS 2: save pre/main/post snapshots around best_frame_index
    
    cap = cv2.VideoCapture(saved_path)
    if not cap.isOpened():
        print(f"[ERROR VIDEO] Could not re-open video file for snapshots: {saved_path}")
        raise HTTPException(status_code=500, detail="Could not open video for snapshots")

    # Generate incident tag
    now_ts = time.time()
    incident_tag = f"VIDEO_CAM_1_{int(now_ts)}"

    # Define snapshot index ranges
    pre_start_index = max(1, best_frame_index - PRE_SNAPSHOT_COUNT)
    pre_end_index = best_frame_index - 1
    post_end_index = best_frame_index + POST_CAPTURE_FRAMES

    frame_index = 0
    pre_saved = 0
    post_saved = 0
    main_saved = False
    snapshot_url = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_index += 1

        # Pre-accident frames
        if pre_start_index <= frame_index <= pre_end_index and pre_saved < PRE_SNAPSHOT_COUNT:
            try:
                pre_filename = f"video_accident_pre_{incident_tag}_{pre_saved}.jpg"
                pre_path = os.path.join(SNAPSHOT_DIR, pre_filename)
                cv2.imwrite(pre_path, frame)
                pre_saved += 1
            except Exception as e:
                print(f"[ERROR VIDEO] Could not save pre-accident frame: {e}")

        # Main accident frame (annotated from pass 1)
        if frame_index == best_frame_index and not main_saved and best_annotated_frame is not None:
            try:
                main_filename = f"video_accident_main_{incident_tag}_{uuid.uuid4()}.jpg"
                main_path = os.path.join(SNAPSHOT_DIR, main_filename)
                cv2.imwrite(main_path, best_annotated_frame)
                snapshot_url = f"http://localhost:8000/snapshots/{main_filename}"
                main_saved = True
                print(f"[VIDEO] Main accident snapshot saved at {main_path}, URL={snapshot_url}")
            except Exception as e:
                print(f"[ERROR VIDEO] Could not save main accident snapshot: {e}")

        # Post-accident frames
        if frame_index > best_frame_index and frame_index <= post_end_index and post_saved < POST_CAPTURE_FRAMES:
            try:
                post_filename = f"video_accident_post_{incident_tag}_{post_saved}.jpg"
                post_path = os.path.join(SNAPSHOT_DIR, post_filename)
                cv2.imwrite(post_path, frame)
                post_saved += 1
            except Exception as e:
                print(f"[ERROR VIDEO] Could not save post-accident frame: {e}")

        # Early break if everything saved
        if frame_index > post_end_index:
            break

    cap.release()
    print(
        f"[VIDEO] Saved {pre_saved} pre-accident, "
        f"{1 if main_saved else 0} main, {post_saved} post-accident snapshots for {incident_tag}"
    )

    # ---- Call Java backend ----
    accidents_detected = 0
    incident_ids: List[int] = []

    try:
        now = datetime.now(timezone.utc)
        backend_incident = send_incident_to_backend(
            camera_id="VIDEO_CAM_1",
            severity=best_severity,
            victims=best_victims,
            source="VIDEO",
            location_lat=19.0,
            location_lng=73.0,
            snapshot_url=snapshot_url,
            time=now,
            likely_injuries=injury_report,
            doctor_report_summary=injury_report["summaryForDoctors"],
        )

        if backend_incident:
            print("[PY VIDEO] Backend incident JSON:", backend_incident)

            incident_id = None
            if isinstance(backend_incident, dict):
                if "id" in backend_incident:
                    incident_id = backend_incident["id"]
                elif "incidentId" in backend_incident:
                    incident_id = backend_incident["incidentId"]
                elif "incident_id" in backend_incident:
                    incident_id = backend_incident["incident_id"]

            if incident_id is not None:
                try:
                    incident_ids.append(int(incident_id))
                    accidents_detected = 1
                except (ValueError, TypeError):
                    print(f"[WARN VIDEO] Could not convert incident_id={incident_id} to int")

    except Exception as e:
        print(f"[ERROR VIDEO] While sending incident to backend: {e}")

    return VideoAnalysisResponse(
        message=f"Video analyzed. Max severity detected = {best_severity}.",
        accidents_detected=accidents_detected,
        incident_ids=incident_ids,
    )
