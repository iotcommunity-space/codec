//@ts-nocheck
/* eslint-disable no-throw-literal */
/* eslint-disable vars-on-top */
/* eslint-disable no-var */
/* eslint-disable radix */
/* eslint-disable no-case-declarations */
/* eslint-disable no-unused-vars */
/* eslint-disable no-plusplus */
/* eslint-disable no-use-before-define */
/**
 * Entry, decoder.js
 */

function decodeUplink(input, port) {
  // init
  var bytes = bytes2HexString(input).toLocaleUpperCase();

  const result = {
    err: 0,
    payload: bytes,
    valid: true,
    messages: [],
  };
  const splitArray = dataSplit(bytes);
  // data decoder
  const decoderArray = [];
  for (let i = 0; i < splitArray.length; i++) {
    const item = splitArray[i];
    const { dataId } = item;
    const { dataValue } = item;
    const messages = dataIdAndDataValueJudge(dataId, dataValue);
    decoderArray.push(messages);
  }
  result.messages = decoderArray;
  return { data: result };
}

/**
 * data splits
 * @param bytes
 * @returns {*[]}
 */
function dataSplit(bytes) {
  const frameArray = [];

  for (let i = 0; i < bytes.length; i++) {
    const remainingValue = bytes;
    const dataId = remainingValue.substring(0, 2);
    let dataValue;
    let dataObj = {};
    switch (dataId) {
      case "01":
      case "20":
      case "21":
      case "30":
      case "31":
      case "33":
      case "40":
      case "41":
      case "42":
      case "43":
      case "44":
      case "45":
        dataValue = remainingValue.substring(2, 22);
        bytes = remainingValue.substring(22);
        dataObj = {
          dataId,
          dataValue,
        };
        break;
      case "4A":
        dataValue = remainingValue.substring(2, 22);
        bytes = remainingValue.substring(22);
        dataObj = {
          dataId: dataId,
          dataValue: dataValue,
        };
        break;
      case "02":
        dataValue = remainingValue.substring(2, 18);
        bytes = remainingValue.substring(18);
        dataObj = {
          dataId: "02",
          dataValue,
        };
        break;
      case "4B":
        dataValue = remainingValue.substring(2, 18);
        bytes = remainingValue.substring(18);
        dataObj = {
          dataId: dataId,
          dataValue: dataValue,
        };
        break;
      case "03":
      case "06":
        dataValue = remainingValue.substring(2, 4);
        bytes = remainingValue.substring(4);
        dataObj = {
          dataId,
          dataValue,
        };
        break;
      case "05":
      case "34":
        dataValue = bytes.substring(2, 10);
        bytes = remainingValue.substring(10);
        dataObj = {
          dataId,
          dataValue,
        };
        break;
      case "04":
      case "10":
      case "32":
      case "35":
      case "36":
      case "37":
      case "38":
      case "39":
        dataValue = bytes.substring(2, 20);
        bytes = remainingValue.substring(20);
        dataObj = {
          dataId,
          dataValue,
        };
        break;
      case "4C":
        dataValue = bytes.substring(2, 14);
        bytes = remainingValue.substring(14);
        dataObj = {
          dataId: dataId,
          dataValue: dataValue,
        };
        break;
      default:
        dataValue = "9";
        break;
    }
    if (dataValue.length < 2) {
      break;
    }
    frameArray.push(dataObj);
  }
  return frameArray;
}

function dataIdAndDataValueJudge(dataId, dataValue) {
  let messages = [];
  switch (dataId) {
    case "01":
      const temperature = dataValue.substring(0, 4);
      const humidity = dataValue.substring(4, 6);
      const illumination = dataValue.substring(6, 14);
      const uv = dataValue.substring(14, 16);
      const windSpeed = dataValue.substring(16, 20);
      messages = [
        {
          measurementValue: loraWANV2DataFormat(temperature, 10),
          measurementId: "4097",
          type: "Air Temperature",
        },
        {
          measurementValue: loraWANV2DataFormat(humidity),
          measurementId: "4098",
          type: "Air Humidity",
        },
        {
          measurementValue: loraWANV2DataFormat(illumination),
          measurementId: "4099",
          type: "Light Intensity",
        },
        {
          measurementValue: loraWANV2DataFormat(uv, 10),
          measurementId: "4190",
          type: "UV Index",
        },
        {
          measurementValue: loraWANV2DataFormat(windSpeed, 10),
          measurementId: "4105",
          type: "Wind Speed",
        },
      ];
      break;
    case "02":
      const windDirection = dataValue.substring(0, 4);
      const rainfall = dataValue.substring(4, 12);
      const airPressure = dataValue.substring(12, 16);
      messages = [
        {
          measurementValue: loraWANV2DataFormat(windDirection),
          measurementId: "4104",
          type: "Wind Direction Sensor",
        },
        {
          measurementValue: loraWANV2DataFormat(rainfall, 1000),
          measurementId: "4113",
          type: "Rain Gauge",
        },
        {
          measurementValue: loraWANV2DataFormat(airPressure, 0.1),
          measurementId: "4101",
          type: "Barometric Pressure",
        },
      ];
      break;
    case "03":
      const Electricity = dataValue;
      messages = [
        {
          "Battery(%)": loraWANV2DataFormat(Electricity),
        },
      ];
      break;
    case "04":
      const electricityWhether = dataValue.substring(0, 2);
      const hwv = dataValue.substring(2, 6);
      const bdv = dataValue.substring(6, 10);
      const sensorAcquisitionInterval = dataValue.substring(10, 14);
      const gpsAcquisitionInterval = dataValue.substring(14, 18);
      messages = [
        {
          "Battery(%)": loraWANV2DataFormat(electricityWhether),
          "Hardware Version": `${loraWANV2DataFormat(hwv.substring(0, 2))}.${loraWANV2DataFormat(hwv.substring(2, 4))}`,
          "Firmware Version": `${loraWANV2DataFormat(bdv.substring(0, 2))}.${loraWANV2DataFormat(bdv.substring(2, 4))}`,
          measureInterval: parseInt(loraWANV2DataFormat(sensorAcquisitionInterval)) * 60,
          gpsInterval: parseInt(loraWANV2DataFormat(gpsAcquisitionInterval)) * 60,
        },
      ];
      break;
    case "05":
      const sensorAcquisitionIntervalFive = dataValue.substring(0, 4);
      const gpsAcquisitionIntervalFive = dataValue.substring(4, 8);
      messages = [
        {
          measureInterval: parseInt(loraWANV2DataFormat(sensorAcquisitionIntervalFive)) * 60,
          gpsInterval: parseInt(loraWANV2DataFormat(gpsAcquisitionIntervalFive)) * 60,
        },
      ];
      break;
    case "06":
      const errorCode = dataValue;
      let descZh;
      switch (errorCode) {
        case "00":
          descZh = "CCL_SENSOR_ERROR_NONE";
          break;
        case "01":
          descZh = "CCL_SENSOR_NOT_FOUND";
          break;
        case "02":
          descZh = "CCL_SENSOR_WAKEUP_ERROR";
          break;
        case "03":
          descZh = "CCL_SENSOR_NOT_RESPONSE";
          break;
        case "04":
          descZh = "CCL_SENSOR_DATA_EMPTY";
          break;
        case "05":
          descZh = "CCL_SENSOR_DATA_HEAD_ERROR";
          break;
        case "06":
          descZh = "CCL_SENSOR_DATA_CRC_ERROR";
          break;
        case "07":
          descZh = "CCL_SENSOR_DATA_B1_NO_VALID";
          break;
        case "08":
          descZh = "CCL_SENSOR_DATA_B2_NO_VALID";
          break;
        case "09":
          descZh = "CCL_SENSOR_RANDOM_NOT_MATCH";
          break;
        case "0A":
          descZh = "CCL_SENSOR_PUBKEY_SIGN_VERIFY_FAILED";
          break;
        case "0B":
          descZh = "CCL_SENSOR_DATA_SIGN_VERIFY_FAILED";
          break;
        case "0C":
          descZh = "CCL_SENSOR_DATA_VALUE_HI";
          break;
        case "0D":
          descZh = "CCL_SENSOR_DATA_VALUE_LOW";
          break;
        case "0E":
          descZh = "CCL_SENSOR_DATA_VALUE_MISSED";
          break;
        case "0F":
          descZh = "CCL_SENSOR_ARG_INVAILD";
          break;
        case "10":
          descZh = "CCL_SENSOR_RS485_MASTER_BUSY";
          break;
        case "11":
          descZh = "CCL_SENSOR_RS485_REV_DATA_ERROR";
          break;
        case "12":
          descZh = "CCL_SENSOR_RS485_REG_MISSED";
          break;
        case "13":
          descZh = "CCL_SENSOR_RS485_FUN_EXE_ERROR";
          break;
        case "14":
          descZh = "CCL_SENSOR_RS485_WRITE_STRATEGY_ERROR";
          break;
        case "15":
          descZh = "CCL_SENSOR_CONFIG_ERROR";
          break;
        case "FF":
          descZh = "CCL_SENSOR_DATA_ERROR_UNKONW";
          break;
        default:
          descZh = "CC_OTHER_FAILED";
          break;
      }
      messages = [
        {
          measurementId: "4101",
          type: "sensor_error_event",
          errCode: errorCode,
          descZh,
        },
      ];
      break;
    case "10":
      const statusValue = dataValue.substring(0, 2);
      const { status, type } = loraWANV2BitDataFormat(statusValue);
      const sensecapId = dataValue.substring(2);
      messages = [
        {
          status,
          channelType: type,
          sensorEui: sensecapId,
        },
      ];
      break;
    case "4A":
      const temperaturee = dataValue.substring(0, 4);
      const humidityy = dataValue.substring(4, 6);
      const illuminationn = dataValue.substring(6, 14);
      const uvv = dataValue.substring(14, 16);
      const windSpeedd = dataValue.substring(16, 20);
      messages = [
        {
          measurementValue: loraWANV2DataFormat(temperaturee, 10),
          measurementId: "4097",
          type: "Air Temperature",
        },
        {
          measurementValue: loraWANV2DataFormat(humidityy),
          measurementId: "4098",
          type: "Air Humidity",
        },
        {
          measurementValue: loraWANV2DataFormat(illuminationn),
          measurementId: "4099",
          type: "Light Intensity",
        },
        {
          measurementValue: loraWANV2DataFormat(uvv, 10),
          measurementId: "4190",
          type: "UV Index",
        },
        {
          measurementValue: loraWANV2DataFormat(windSpeedd, 10),
          measurementId: "4105",
          type: "Wind Speed",
        },
      ];
      break;
    case "4B":
      const windDirectionn = dataValue.substring(0, 4);
      const rainfalll = dataValue.substring(4, 12);
      const airPressuree = dataValue.substring(12, 16);
      messages = [
        {
          measurementValue: loraWANV2DataFormat(windDirectionn),
          measurementId: "4104",
          type: "Wind Direction Sensor",
        },
        {
          measurementValue: loraWANV2DataFormat(rainfalll, 1000),
          measurementId: "4113",
          type: "Rain Gauge",
        },
        {
          measurementValue: loraWANV2DataFormat(airPressuree, 0.1),
          measurementId: "4101",
          type: "Barometric Pressure",
        },
      ];
      break;
    case "4C":
      const peakWind = dataValue.substring(0, 4);
      const rainAccumulation = dataValue.substring(4, 12);
      messages = [
        {
          measurementValue: loraWANV2DataFormat(peakWind, 10),
          measurementId: "4191",
          type: " Peak Wind Gust",
        },
        {
          measurementValue: loraWANV2DataFormat(rainAccumulation, 1000),
          measurementId: "4213",
          type: "Rain Accumulation",
        },
      ];
      break;
    default:
      break;
  }
  return messages;
}

/**
 *
 * data formatting
 * @param str
 * @param divisor
 * @returns {string|number}
 */
function loraWANV2DataFormat(str, divisor = 1) {
  const strReverse = bigEndianTransform(str);
  let str2 = toBinary(strReverse);
  if (str2.substring(0, 1) === "1") {
    const arr = str2.split("");
    const reverseArr = arr.map((item) => {
      if (parseInt(item) === 1) {
        return 0;
      }
      return 1;
    });
    str2 = parseInt(reverseArr.join(""), 2) + 1;
    return `-${str2 / divisor}`;
  }
  return parseInt(str2, 2) / divisor;
}

/**
 * Handling big-endian data formats
 * @param data
 * @returns {*[]}
 */
function bigEndianTransform(data) {
  const dataArray = [];
  for (let i = 0; i < data.length; i += 2) {
    dataArray.push(data.substring(i, i + 2));
  }
  // array of hex
  return dataArray;
}

/**
 * Convert to an 8-digit binary number with 0s in front of the number
 * @param arr
 * @returns {string}
 */
function toBinary(arr) {
  const binaryData = arr.map((item) => {
    let data = parseInt(item, 16).toString(2);
    const dataLength = data.length;
    if (data.length !== 8) {
      for (let i = 0; i < 8 - dataLength; i++) {
        data = `0${data}`;
      }
    }
    return data;
  });
  const ret = binaryData.toString().replace(/,/g, "");
  return ret;
}

/**
 * sensor
 * @param str
 * @returns {{channel: number, type: number, status: number}}
 */
function loraWANV2BitDataFormat(str) {
  const strReverse = bigEndianTransform(str);
  const str2 = toBinary(strReverse);
  const channel = parseInt(str2.substring(0, 4), 2);
  const status = parseInt(str2.substring(4, 5), 2);
  const type = parseInt(str2.substring(5), 2);
  return { channel, status, type };
}

/**
 * channel info
 * @param str
 * @returns {{channelTwo: number, channelOne: number}}
 */
function loraWANV2ChannelBitFormat(str) {
  const strReverse = bigEndianTransform(str);
  const str2 = toBinary(strReverse);
  const one = parseInt(str2.substring(0, 4), 2);
  const two = parseInt(str2.substring(4, 8), 2);
  const resultInfo = {
    one,
    two,
  };
  return resultInfo;
}

/**
 * data log status bit
 * @param str
 * @returns {{total: number, level: number, isTH: number}}
 */
function loraWANV2DataLogBitFormat(str) {
  const strReverse = bigEndianTransform(str);
  const str2 = toBinary(strReverse);
  const isTH = parseInt(str2.substring(0, 1), 2);
  const total = parseInt(str2.substring(1, 5), 2);
  const left = parseInt(str2.substring(5), 2);
  const resultInfo = {
    isTH,
    total,
    left,
  };
  return resultInfo;
}

function bytes2HexString(arrBytes) {
  var str = "";
  for (var i = 0; i < arrBytes.length; i++) {
    var tmp;
    var num = arrBytes[i];
    if (num < 0) {
      tmp = (255 + num + 1).toString(16);
    } else {
      tmp = num.toString(16);
    }
    if (tmp.length === 1) {
      tmp = `0${tmp}`;
    }
    str += tmp;
  }
  return str;
}

function toTagoFormat(result, group) {
  if (!result.data.messages.length) {
    return "Payload is not valid";
  }
  const arrayToTago = [];

  for (const messages of result.data.messages) {
    for (const x of messages) {
      arrayToTago.push({
        variable: String(x.type).toLowerCase().replace(/\s/g, "_"),
        value: x.measurementValue,
        group,
      });
    }
  }

  return arrayToTago;
}

const payload_raw = payload.find((x) => x.variable === "payload_raw" || x.variable === "payload" || x.variable === "data");
if (payload_raw) {
  try {
    // Convert the data from Hex to Javascript Buffer.
    const buffer = Buffer.from(payload_raw.value, "hex");
    const result = decodeUplink(buffer);
    const payload_aux = toTagoFormat(result, payload_raw.group || String(new Date().getTime()));
    payload = payload.concat(payload_aux.map((x) => ({ ...x })));
  } catch (e) {
    // Print the error to the Live Inspector.
    console.error(e);
    // Return the variable parse_error for debugging.
    payload = [{ variable: "parse_error", value: e.message }];
  }
}
