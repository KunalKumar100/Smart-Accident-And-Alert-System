package com.smartaccident.backend.camera;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface CameraStreamRepository extends JpaRepository<CameraStream, Long> {
    Optional<CameraStream> findByName(String name);
}
