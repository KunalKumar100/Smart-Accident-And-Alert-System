package com.smartaccident.backend.camera;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "camera_streams")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CameraStream {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;        // e.g. "cam_01"
    private String rtspUrl;     // later for live streams

    private Double locationLat;
    private Double locationLng;

    private String city;        //  e.g. "Gurugram", "Delhi", "Mumbai"

    private boolean active;
}
