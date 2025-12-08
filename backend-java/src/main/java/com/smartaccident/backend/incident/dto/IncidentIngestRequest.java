package com.smartaccident.backend.incident.dto;

import lombok.Data;

@Data
public class IncidentIngestRequest {

    private String cameraId;
    private String timestamp;
    private boolean accident;
    private String severity;
    private int victimCount;
    private LocationDTO location;
    private String snapshotUrl;

    //  Changed from List<String> to Object (Map) to support FULL JSON
    private Object likelyInjuries;

    //  New: Doctor-friendly report summary (plain text)
    private String doctorReportSummary;

    @Data
    public static class LocationDTO {
        private double lat;
        private double lng;
    }
}
