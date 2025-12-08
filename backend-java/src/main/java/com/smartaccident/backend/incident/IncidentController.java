package com.smartaccident.backend.incident;

import com.smartaccident.backend.incident.dto.IncidentIngestRequest;
import com.smartaccident.backend.incident.dto.IncidentResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/incidents")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class IncidentController {

    private final IncidentService incidentService;

    @PostMapping("/ingest")
    public ResponseEntity<IncidentResponse> ingestIncident(@RequestBody IncidentIngestRequest request) {
        IncidentResponse savedIncident = incidentService.handleIngest(request);
        return ResponseEntity.ok(savedIncident);
}

    @GetMapping
    public List<IncidentResponse> getIncidents(@RequestParam(required = false) String status) {
        return incidentService.getIncidents(status);
    }

    @GetMapping("/{id}")
    public IncidentResponse getIncident(@PathVariable Long id) {
        return incidentService.getIncident(id);
    }
}
