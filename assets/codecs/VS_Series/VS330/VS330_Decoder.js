/**
 * Payload Decoder
 *
 * Copyright 2024 Milesight IoT
 *
 * @product VS330
 */
// Chirpstack v4
function decodeUplink(input) {
    var decoded = milesightDeviceDecode(input.bytes);
    return { data: decoded };
}

// Chirpstack v3
function Decode(fPort, bytes) {
    return milesightDeviceDecode(bytes);
}

// The Things Network
function Decoder(bytes, port) {
    return milesightDeviceDecode(bytes);
}

function milesightDeviceDecode(bytes) {
    var decoded = {};

    for (var i = 0; i < bytes.length; ) {
        var channel_id = bytes[i++];
        var channel_type = bytes[i++];

        // BATTERY
        if (channel_id === 0x01 && channel_type === 0x75) {
            decoded.battery = bytes[i];
            i += 1;
        }
        // DISTANCE
        else if (channel_id === 0x02 && channel_type === 0x82) {
            decoded.distance = readUInt16LE(bytes.slice(i, i + 2));
            i += 2;
        }
        // OCCUPANCY
        else if (channel_id === 0x03 && channel_type === 0x8e) {
            decoded.occupancy = bytes[i] === 0 ? "vacant" : "occupied";
            i += 1;
        }
        // CALIBRATION
        else if (channel_id === 0x04 && channel_type === 0x8e) {
            decoded.calibration = bytes[i] === 0 ? "failed" : "success";
            i += 1;
        } else {
            break;
        }
    }

    return decoded;
}

// bytes to number
function readUInt16LE(bytes) {
    var value = (bytes[1] << 8) + bytes[0];
    return value & 0xffff;
}
