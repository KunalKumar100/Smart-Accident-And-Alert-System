package com.smartaccident.backend.alert;

import com.smartaccident.backend.incident.Incident;
import com.twilio.Twilio;
import com.twilio.rest.api.v2010.account.Message;
import com.twilio.type.PhoneNumber;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class AlertService {

    @Value("${twilio.account_sid}")
    private String accountSid;

    @Value("${twilio.auth_token}")
    private String authToken;

    @Value("${twilio.whatsapp_from}")
    private String whatsappFrom;

    @Value("${twilio.whatsapp_to_police}")
    private String whatsappToPolice;

    @Value("${twilio.whatsapp_to_hospital}")
    private String whatsappToHospital;

    private boolean initialized = false;

    private void initTwilioIfNeeded() {
        if (!initialized) {
            Twilio.init(accountSid, authToken);
            initialized = true;
            System.out.println("[TWILIO] Initialized with account SID: " + accountSid);
        }
    }

    public void sendAlertMessages(Incident incident) {
        initTwilioIfNeeded();

        String cameraName = incident.getCamera() != null
                ? incident.getCamera().getName()
                : "UNKNOWN";

        Double lat = incident.getLocationLat();
        Double lng = incident.getLocationLng();

        String mapsLink;
        if (lat != null && lng != null) {
            mapsLink = "https://www.google.com/maps?q=" + lat + "," + lng;
        } else {
            mapsLink = "Location unavailable";
        }

        String snapshot = (incident.getSnapshotUrl() != null && !incident.getSnapshotUrl().isBlank())
                ? incident.getSnapshotUrl()
                : "N/A";

        String baseText =
                "Severity: " + incident.getSeverity() + "\n" +
                "Victims: " + incident.getVictimCount() + "\n" +
                "Camera: " + cameraName + "\n" +
                "Time: " + incident.getTimestamp() + "\n" +
                "Location: " + mapsLink + "\n" +
                "Snapshot: " + snapshot;

        // POLICE ALERT — no medical details
        sendWhatsApp(
                whatsappToPolice,
                " POLICE ALERT Detect the Accident \n" + baseText
        );

        //  HOSPITAL ALERT — includes AI injury report, if present
        String hospitalText = " HOSPITAL ALERT Detect the accident \n" + baseText;

        String doctorReport = incident.getDoctorReportSummary();
        if (doctorReport != null && !doctorReport.isBlank()) {
            hospitalText += "\n\n🩺 *AI Injury Report For Hospital:*\n" + doctorReport;
        }

        sendWhatsApp(
                whatsappToHospital,
                hospitalText
        );
    }

    private void sendWhatsApp(String to, String body) {
        try {
            System.out.println("[WHATSAPP] Sending to " + to);
            Message.creator(
                    new PhoneNumber(to),
                    new PhoneNumber(whatsappFrom),
                    body
            ).create();
            System.out.println("[WHATSAPP] Sent successfully to " + to);
        } catch (Exception e) {
            System.err.println("[WHATSAPP] Failed to send to " + to + ": " + e.getMessage());
        }
    }
        // 🔹 Simple test method to check if Twilio + WhatsApp works
    public void sendTestAlert() {
        initTwilioIfNeeded();

        String testBody = " Test WhatsApp alert from Smart Accident System.\n"
                + "If you received this, Twilio config is working correctly.";

        // you can change to whatsappToPolice if you prefer
        sendWhatsApp(whatsappToHospital, testBody);
    }

}
