package com.smartaccident.backend.debug;

import com.smartaccident.backend.alert.AlertService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/debug")
@CrossOrigin(origins = "*")
public class DebugController {

    private final AlertService alertService;

    //  Call this endpoint to test Twilio WhatsApp
    @GetMapping("/test-alert")
    public String sendTestAlert() {
        System.out.println("[DEBUG] /api/debug/test-alert called. Sending test WhatsApp message...");
        alertService.sendTestAlert();
        return "Test alert requested. Check logs + WhatsApp device.";
    }
}
