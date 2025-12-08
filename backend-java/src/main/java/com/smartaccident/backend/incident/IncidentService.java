package com.smartaccident.backend.incident;

import com.smartaccident.backend.alert.AlertService;
import com.smartaccident.backend.camera.CameraStream;
import com.smartaccident.backend.camera.CameraStreamRepository;
import com.smartaccident.backend.incident.dto.IncidentIngestRequest;
import com.smartaccident.backend.incident.dto.IncidentResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.List;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
@RequiredArgsConstructor
public class IncidentService {

    private final IncidentRepository incidentRepository;
    private final CameraStreamRepository cameraRepo;
    private final AlertService alertService;   // WhatsApp alert service
    private final ObjectMapper objectMapper;   // JSON mapper

    public IncidentResponse handleIngest(IncidentIngestRequest request) {

        // Log what Python sent
        System.out.println("[INCIDENT] Incoming ingest payload - " +
                "cameraId=" + request.getCameraId() +
                ", severityString=" + request.getSeverity() +
                ", victims=" + request.getVictimCount() +
                ", snapshotUrl=" + request.getSnapshotUrl());

        //  Find or create camera
        CameraStream camera = cameraRepo.findByName(request.getCameraId())
                .orElseGet(() -> cameraRepo.save(
                        CameraStream.builder()
                                .name(request.getCameraId())
                                .active(true)
                                .build()
                ));

        //  Parse timestamp safely
        Instant ts;
        try {
            ts = OffsetDateTime.parse(request.getTimestamp()).toInstant();
        } catch (Exception e) {
            System.out.println("[INCIDENT] Failed to parse timestamp '"
                    + request.getTimestamp() + "', using now(). Error: " + e.getMessage());
            ts = Instant.now();
        }

        //  Parse severity safely
        Severity severity;
        try {
            severity = Severity.valueOf(request.getSeverity());  // must match enum exactly
        } catch (Exception e) {
            System.out.println("[INCIDENT] Failed to parse severity '"
                    + request.getSeverity() + "', defaulting to MINOR. Error: " + e.getMessage());
            severity = Severity.MINOR;   // fallback
        }

        //  Handle location safely
        double lat = 0.0;
        double lng = 0.0;
        if (request.getLocation() != null) {
            lat = request.getLocation().getLat();
            lng = request.getLocation().getLng();
        }

        //  Handle likelyInjuries safely → convert to valid JSON string
        String likelyInjuriesJson = "[]";
        if (request.getLikelyInjuries() != null) {
            try {
                likelyInjuriesJson = objectMapper.writeValueAsString(request.getLikelyInjuries());
            } catch (JsonProcessingException e) {
                System.out.println("[INCIDENT] Failed to serialize likelyInjuries, using toString(). Error: " + e.getMessage());
                likelyInjuriesJson = request.getLikelyInjuries().toString();
            }
        }

        //  Doctor report summary text (may be null)
        String doctorReportSummary = request.getDoctorReportSummary();

        //  Build incident entity
        Incident incident = Incident.builder()
                .camera(camera)
                .timestamp(ts)
                .severity(severity)
                .victimCount(request.getVictimCount())
                .likelyInjuriesJson(likelyInjuriesJson)
                .doctorReportSummary(doctorReportSummary)
                .status(IncidentStatus.DETECTED)
                .locationLat(lat)
                .locationLng(lng)
                .snapshotUrl(request.getSnapshotUrl())
                .build();

        //  Save Incident
        Incident savedIncident = incidentRepository.save(incident);

        System.out.println("[INCIDENT] Saved incident id=" + savedIncident.getId()
                + ", finalSeverity=" + savedIncident.getSeverity());

        //  Trigger WhatsApp alerts ONLY for serious incidents (MAJOR / CRITICAL)
        if (savedIncident.getSeverity() == Severity.MAJOR
                || savedIncident.getSeverity() == Severity.CRITICAL) {

            System.out.println("[INCIDENT] Serious incident (" + savedIncident.getSeverity()
                    + "), calling AlertService...");
            alertService.sendAlertMessages(savedIncident);

        } else {
            System.out.println("[INCIDENT] Non-serious incident (" + savedIncident.getSeverity()
                    + "), alerts NOT triggered.");
        }

        //  Map entity → DTO
        return toResponse(savedIncident);
    }

    public List<IncidentResponse> getIncidents(String status) {
        List<Incident> incidents =
                (status == null || status.isBlank())
                        ? incidentRepository.findAll()
                        : incidentRepository.findByStatus(IncidentStatus.valueOf(status));

        return incidents.stream().map(this::toResponse).toList();
    }

    public IncidentResponse getIncident(Long id) {
        Incident incident = incidentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Incident not found"));
        return toResponse(incident);
    }

    private IncidentResponse toResponse(Incident i) {
        return IncidentResponse.builder()
                .id(i.getId())
                .cameraName(i.getCamera().getName())
                .severity(i.getSeverity().name())
                .victimCount(i.getVictimCount())
                .status(i.getStatus().name())
                .timestamp(i.getTimestamp().toString())
                .locationLat(i.getLocationLat())
                .locationLng(i.getLocationLng())
                .snapshotUrl(i.getSnapshotUrl())
                .likelyInjuriesJson(i.getLikelyInjuriesJson())
                .doctorReportSummary(i.getDoctorReportSummary())
                .build();
    }
}
