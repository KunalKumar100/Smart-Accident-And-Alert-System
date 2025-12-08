package com.smartaccident.backend.emergency;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "police_stations")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PoliceStation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;
    private String contactNumber;
    private String city;
    private Double latitude;
    private Double longitude;
}
