BACKEND_BASE_URL = "http://localhost:8080"  # change if your Spring Boot runs on another port

# Endpoint on Java backend that ingests incidents
INGEST_INCIDENT_URL = f"{BACKEND_BASE_URL}/api/incidents/ingest"
