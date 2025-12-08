package com.smartaccident.backend.incident.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class IncidentResponse {

    private Long id;
    private String cameraName;
    private String severity;
    private int victimCount;
    private String status;
    private String timestamp;
    private Double locationLat;
    private Double locationLng;
    private String snapshotUrl;

    //  Full AI-generated JSON report
    private String likelyInjuriesJson;

    // Clean doctor-friendly summary (for frontend and WhatsApp)
    private String doctorReportSummary;
}
