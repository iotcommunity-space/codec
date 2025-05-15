// ChirpStack Payload Codec for Netvox RA02G (LoRaWAN Wireless Vaping/Smoke/Noise Sensor)
// Reference: Netvox RA02G User Manual (Hardware v0.5, 2024)
// Typical uplink FPort: 6 (data), 7 (configuration), 0x20 (rejoin); this handles primary data
// ----------------------------------------------------------------------------
// Codec developed by https://github.com/nishchayjeet
// ----------------------------------------------------------------------------

function decodeUplink(input) {
  // input.bytes: Array of bytes from the device
  // input.fPort: LoRaWAN port (should be 6 for main data uplink)

  const data = input.bytes;
  let result = {};

  // Map for deviceType and reportType values (RA02G specific)
  const DEVICE_TYPE_RA02G = 0xD7;

  // --- Handle Report Data (see manual §5.1, Table p.10) ---
  if (input.fPort === 6 && data.length >= 11 && data[1] === DEVICE_TYPE_RA02G) {
    const reportType = data[2];

    if (reportType === 0x01) {
      // Data Packet (typical periodic uplink)
      // Format: [CmdID, DeviceType, ReportType, Batt, Smoke, Noise, Shock, PowerOff, Reserved x3]
      // Example: 01 D7 01 00 00 01 00 00 00 00 00 (see manual p.10)

      result = {
        deviceType: "RA02G",
        battery: data[3] === 0 ? "DC powered" : (data[3] * 0.1).toFixed(1) + "V", // 0 = DC, else 0.1V steps
        smokeAlarm: data[4] === 1,     // IncenseSmokeAlarm: 0=no alarm, 1=alarm
        noiseAlarm: data[5] === 1,     // HighSoundAlarm: 0=no alarm, 1=alarm
        tamperAlarm: data[6] === 1,    // ShockAlarm: 0=no alarm, 1=alarm
        powerOffAlarm: data[7] === 1,  // PowerOffAlarm: 0=no alarm, 1=alarm
        raw: bytesToHex(data)
      };

      // Provide event names as tags (for ChirpStack compatibility)
      result.tags = {};
      if (result.smokeAlarm)   result.tags.smoke = "detected";
      if (result.noiseAlarm)   result.tags.noise = "detected";
      if (result.tamperAlarm)  result.tags.tamper = "triggered";
      if (result.powerOffAlarm) result.tags.power = "outage";

      // Useful for mapping to your LNS event
      result.eventType = (
        result.smokeAlarm   ? "Smoke/Vape Detected" :
        result.noiseAlarm   ? "Noise Alarm" :
        result.tamperAlarm  ? "Tamper/Vibration Alarm" :
        result.powerOffAlarm? "Power Outage" : "Normal"
      );
    } else if (reportType === 0x00) {
      // Version Packet
      result = {
        deviceType: "RA02G",
        version: {
          software: "V" + data[3],
          hardware: data[4],
          datecode: (
            (data[5] << 24 | data[6] << 16 | data[7] << 8 | data[8]).toString(16)
          ),
        },
        raw: bytesToHex(data)
      };
    } else {
      // Other report types (configuration, etc.)
      result = {
        warning: "Unhandled ReportType",
        reportType,
        raw: bytesToHex(data)
      };
    }
  } else {
    // Handle other ports / unknown data
    result = {
      warning: "Unknown uplink format or unsupported FPort",
      fPort: input.fPort,
      raw: bytesToHex(data)
    };
  }

  return {
    data: result
  };
}

// Helper function: convert bytes to hex string for raw inspection
function bytesToHex(bytes) {
  return bytes.map(x => ('0' + x.toString(16)).slice(-2)).join('');
}
