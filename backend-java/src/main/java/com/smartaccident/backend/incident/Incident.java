package com.smartaccident.backend.incident;

import com.smartaccident.backend.camera.CameraStream;
import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;

@Entity
@Table(name = "incidents")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Incident {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "camera_id")
    private CameraStream camera;

    private Instant timestamp;

    @Enumerated(EnumType.STRING)
    private Severity severity;

    private int victimCount;

    //  Stores detailed AI JSON report (full object, doctor-level info, preparation steps, etc.)
    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String likelyInjuriesJson;

    //  Stores summarized plain text version, used for alert messages
    @Column(length = 1000)
    private String doctorReportSummary;

    @Enumerated(EnumType.STRING)
    private IncidentStatus status;

    private Double locationLat;
    private Double locationLng;

    private String snapshotUrl;
}
