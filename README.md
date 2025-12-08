# Smart-Accident-And-Alert-System
AI-powered Smart Accident Detection &amp; Emergency Response System using YOLO, FastAPI, Spring Boot, and React. Automatically detects road accidents from live video or recordings, classifies severity, captures snapshots, and sends real-time WhatsApp alerts with location and incident. Includes a full dashboard for monitoring and incident logging.

#  IMPORTANT: Police/Hospital Alert Feature

This system supports automated alerting for law enforcement and hospitals.

DO NOT configure real police or hospital phone numbers during testing.
Use only your personal numbers or dummy test numbers.

Sending false accident alerts to real emergency services may be illegal.

## Overview
The Smart Accident Detection & Emergency Response System is a full-stack AI platform that detects road accidents from live camera feed or uploaded video, classifies severity, estimates injuries, captures timeline snapshots, and automatically sends WhatsApp emergency alerts using Twilio.

The system is designed for:

1. Smart cities

2. Highway surveillance

3. Emergency response automation

4. Real-time accident monitoring


# Tech Stack
## Frontend (React + Vite)
1. Live camera streaming

2. Video upload & analysis interface

3. Dashboard with accident logs

4. Severity badges & snapshot viewer  


## AI Microservice (FastAPI + YOLO/OpenCV)
1. Frame-by-frame accident detection

2. Victim count (person/vehicle detection)

3. Pre/impact/post snapshot generation

4. Sends structured JSON metadata to backend

## Backend (Spring Boot + MySQL)
1. Stores incident data

2. REST APIs for frontend

3. Manages incident severity, timestamps, camera ID

4. Integration with Twilio WhatsApp API

# How to Run the Project

## Start the AI Service
```cd ai-service-python```
```pip install -r requirements.txt```
```uvicorn main:app --reload```

## Start the Spring Boot Backend
```cd backend-java```
```mvn spring-boot:run```

## Start the React Frontend
```cd frontend-react```
```npm install```
```npm run dev```

# Features
1. Real-time Accident Detection
2. Severity Classification
-- Categorizes incidents as:
a. Minor
b. Moderate 
c. Major
d. Critical
### Medical Injury Estimation
-- AI-based injury approximation based on severity and victim count.

### Snapshot Timeline
#### Stores three images:
1. Pre-impact
2. Impact
3. Post-impact

### WhatsApp Alert Automation
-- Send the Alert message from twilio and to start this service first create and verify your whatsapp number from Twilio and make sure to update ```application.properties file``` in the backend.

#  Configuration & Secrets (IMPORTANT)
This project **does NOT** include any credentials in the source code.  
You must provide your own API keys and secrets via environment variables.

Set the following in your system in the backend where the file loction is ```Backend-java\src\main\resources\application.properties``` :

DB_URL=jdbc:mysql://localhost:3306/accidents_db
DB_USERNAME=your_db_user
DB_PASSWORD=your_db_password
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890 
#  Warning: Emergency Numbers

This project includes optional Police/Hospital alert automation.

- DO NOT use real police numbers
- DO NOT use real hospital emergency numbers
- Use dummy placeholders like +0000000000

Misuse of real emergency numbers is illegal and can result in penalties.
This feature is intended for research, educational projects, and simulations only.

# Contact
If you want to extend this system, build a research paper, or create a production-ready deployment, feel free to ask.

Have suggestions or want to collaborate?  
Please open an issue in the GitHub repository.

(For privacy and security reasons, no direct contact details are shared.)
