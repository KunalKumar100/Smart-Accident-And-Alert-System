package com.smartaccident.backend.emergency;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface PoliceStationRepository extends JpaRepository<PoliceStation, Long> {
    Optional<PoliceStation> findFirstByCity(String city);
}
