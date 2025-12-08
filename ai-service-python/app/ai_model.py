# app/ai_model.py
from ultralytics import YOLO

# Load YOLO model once at startup
# You can start with a generic model; later you can train your own accident model.
_model = YOLO("yolov8n.pt")  # small + fast; make sure the file is downloaded or path is correct

def get_model():
    return _model
