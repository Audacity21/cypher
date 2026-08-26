#include <ArduinoJson.h>
#include <DHT.h>

// ============================================================
// CYPHER FIRMWARE
// Version 0.7.0
// ============================================================

// ============================================================
// PIN DEFINITIONS
// ============================================================

// Ultrasonic
const int TRIG_PIN = 9;
const int ECHO_PIN = 10;

// Light
const int LDR_PIN = A0;

// DHT11
#define DHT_PIN 7
#define DHT_TYPE DHT11

DHT dht(DHT_PIN, DHT_TYPE);

// RGB LED
// Verified physical mapping:
// RED   -> D6
// GREEN -> D3
// BLUE  -> D5
//
// LED type:
// Common cathode

const int RGB_RED_PIN = 3;
const int RGB_GREEN_PIN = 5;
const int RGB_BLUE_PIN = 6;


// ============================================================
// SENSOR HELPERS
// ============================================================

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(
    ECHO_PIN,
    HIGH,
    30000
  );

  if (duration == 0) {
    return -1;
  }

  return duration * 0.0343 / 2.0;
}


int readLightLevel() {
  return analogRead(LDR_PIN);
}


bool readClimate(
  float &temperature,
  float &humidity
) {
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();

  if (
    isnan(humidity) ||
    isnan(temperature)
  ) {
    return false;
  }

  return true;
}


// ============================================================
// OUTPUT HELPERS
// ============================================================

void setRgbColor(
  int red,
  int green,
  int blue
) {
  red = constrain(
    red,
    0,
    255
  );

  green = constrain(
    green,
    0,
    255
  );

  blue = constrain(
    blue,
    0,
    255
  );

  analogWrite(
    RGB_RED_PIN,
    red
  );

  analogWrite(
    RGB_GREEN_PIN,
    green
  );

  analogWrite(
    RGB_BLUE_PIN,
    blue
  );
}


// ============================================================
// RESPONSE HELPERS
// ============================================================

void sendError(
  const char* id,
  const char* cmd,
  const char* errorMessage
) {
  JsonDocument response;

  response["type"] = "resp";

  if (id != nullptr) {
    response["id"] = id;
  }

  if (cmd != nullptr) {
    response["cmd"] = cmd;
  }

  response["ok"] = false;
  response["error"] = errorMessage;

  serializeJson(
    response,
    Serial
  );

  Serial.println();
}


// ============================================================
// SETUP
// ============================================================

void setup() {
  Serial.begin(115200);

  // -------------------------
  // Ultrasonic
  // -------------------------

  pinMode(
    TRIG_PIN,
    OUTPUT
  );

  pinMode(
    ECHO_PIN,
    INPUT
  );

  // -------------------------
  // LDR
  // -------------------------

  pinMode(
    LDR_PIN,
    INPUT
  );

  // -------------------------
  // DHT11
  // -------------------------

  dht.begin();

  // -------------------------
  // RGB LED
  // -------------------------

  pinMode(
    RGB_RED_PIN,
    OUTPUT
  );

  pinMode(
    RGB_GREEN_PIN,
    OUTPUT
  );

  pinMode(
    RGB_BLUE_PIN,
    OUTPUT
  );

  // Start RGB off
  setRgbColor(
    0,
    0,
    0
  );

  // Allow board / sensors
  // to settle.
  delay(2000);

  Serial.println(
    "{\"type\":\"ready\",\"firmware\":\"0.7.0\"}"
  );
}


// ============================================================
// MAIN LOOP
// ============================================================

void loop() {

  if (!Serial.available()) {
    return;
  }

  String input =
    Serial.readStringUntil('\n');

  input.trim();

  if (
    input.length() == 0
  ) {
    return;
  }


  // ==========================================================
  // PARSE JSON
  // ==========================================================

  JsonDocument request;

  DeserializationError error =
    deserializeJson(
      request,
      input
    );

  if (error) {
    Serial.println(
      "{\"type\":\"error\",\"ok\":false,\"error\":\"invalid_json\"}"
    );

    return;
  }


  // ==========================================================
  // EXTRACT REQUIRED FIELDS
  // ==========================================================

  const char* type =
    request["type"];

  const char* id =
    request["id"];

  const char* cmd =
    request["cmd"];


  // ==========================================================
  // VALIDATE REQUEST
  // ==========================================================

  if (
    type == nullptr ||
    id == nullptr ||
    cmd == nullptr
  ) {
    Serial.println(
      "{\"type\":\"error\",\"ok\":false,\"error\":\"missing_fields\"}"
    );

    return;
  }

  if (
    strcmp(
      type,
      "cmd"
    ) != 0
  ) {
    Serial.println(
      "{\"type\":\"error\",\"ok\":false,\"error\":\"invalid_type\"}"
    );

    return;
  }


  // ==========================================================
  // COMMAND: PING
  // ==========================================================

  if (
    strcmp(
      cmd,
      "PING"
    ) == 0
  ) {
    JsonDocument response;

    response["type"] = "resp";
    response["id"] = id;
    response["cmd"] = "PING";
    response["ok"] = true;

    serializeJson(
      response,
      Serial
    );

    Serial.println();

    return;
  }


  // ==========================================================
  // COMMAND: GET_DISTANCE
  // ==========================================================

  if (
    strcmp(
      cmd,
      "GET_DISTANCE"
    ) == 0
  ) {
    float distance =
      readDistanceCm();

    JsonDocument response;

    response["type"] = "resp";
    response["id"] = id;
    response["cmd"] =
      "GET_DISTANCE";

    if (
      distance >= 0
    ) {
      response["ok"] = true;

      response["data"]
              ["distance_cm"] =
        distance;
    }
    else {
      response["ok"] = false;

      response["error"] =
        "no_echo";
    }

    serializeJson(
      response,
      Serial
    );

    Serial.println();

    return;
  }


  // ==========================================================
  // COMMAND: GET_LIGHT
  // ==========================================================

  if (
    strcmp(
      cmd,
      "GET_LIGHT"
    ) == 0
  ) {
    int lightLevel =
      readLightLevel();

    JsonDocument response;

    response["type"] = "resp";
    response["id"] = id;
    response["cmd"] =
      "GET_LIGHT";
    response["ok"] = true;

    response["data"]
            ["light"] =
      lightLevel;

    serializeJson(
      response,
      Serial
    );

    Serial.println();

    return;
  }


  // ==========================================================
  // COMMAND: GET_TEMP
  // ==========================================================

  if (
    strcmp(
      cmd,
      "GET_TEMP"
    ) == 0
  ) {
    float temperature;
    float humidity;

    bool success =
      readClimate(
        temperature,
        humidity
      );

    if (!success) {
      sendError(
        id,
        cmd,
        "dht_read_failed"
      );

      return;
    }

    JsonDocument response;

    response["type"] = "resp";
    response["id"] = id;
    response["cmd"] =
      "GET_TEMP";
    response["ok"] = true;

    response["data"]
            ["temperature_c"] =
      temperature;

    serializeJson(
      response,
      Serial
    );

    Serial.println();

    return;
  }


  // ==========================================================
  // COMMAND: GET_HUMIDITY
  // ==========================================================

  if (
    strcmp(
      cmd,
      "GET_HUMIDITY"
    ) == 0
  ) {
    float temperature;
    float humidity;

    bool success =
      readClimate(
        temperature,
        humidity
      );

    if (!success) {
      sendError(
        id,
        cmd,
        "dht_read_failed"
      );

      return;
    }

    JsonDocument response;

    response["type"] = "resp";
    response["id"] = id;
    response["cmd"] =
      "GET_HUMIDITY";
    response["ok"] = true;

    response["data"]
            ["humidity_percent"] =
      humidity;

    serializeJson(
      response,
      Serial
    );

    Serial.println();

    return;
  }


  // ==========================================================
  // COMMAND: GET_CLIMATE
  // ==========================================================

  if (
    strcmp(
      cmd,
      "GET_CLIMATE"
    ) == 0
  ) {
    float temperature;
    float humidity;

    bool success =
      readClimate(
        temperature,
        humidity
      );

    if (!success) {
      sendError(
        id,
        cmd,
        "dht_read_failed"
      );

      return;
    }

    JsonDocument response;

    response["type"] = "resp";
    response["id"] = id;
    response["cmd"] =
      "GET_CLIMATE";
    response["ok"] = true;

    response["data"]
            ["temperature_c"] =
      temperature;

    response["data"]
            ["humidity_percent"] =
      humidity;

    serializeJson(
      response,
      Serial
    );

    Serial.println();

    return;
  }


  // ==========================================================
  // COMMAND: SET_RGB
  // ==========================================================

  if (
    strcmp(
      cmd,
      "SET_RGB"
    ) == 0
  ) {
    if (
      !request["args"].is<JsonObject>()
    ) {
      sendError(
        id,
        cmd,
        "missing_args"
      );

      return;
    }

    JsonObject args =
      request["args"];

    if (
      !args["r"].is<int>() ||
      !args["g"].is<int>() ||
      !args["b"].is<int>()
    ) {
      sendError(
        id,
        cmd,
        "invalid_rgb"
      );

      return;
    }

    int red =
      args["r"];

    int green =
      args["g"];

    int blue =
      args["b"];


    // Arduino-side safety validation.
    if (
      red < 0 ||
      red > 255 ||
      green < 0 ||
      green > 255 ||
      blue < 0 ||
      blue > 255
    ) {
      sendError(
        id,
        cmd,
        "rgb_out_of_range"
      );

      return;
    }


    setRgbColor(
      red,
      green,
      blue
    );


    JsonDocument response;

    response["type"] = "resp";
    response["id"] = id;
    response["cmd"] =
      "SET_RGB";
    response["ok"] = true;

    response["data"]["r"] =
      red;

    response["data"]["g"] =
      green;

    response["data"]["b"] =
      blue;

    serializeJson(
      response,
      Serial
    );

    Serial.println();

    return;
  }


  // ==========================================================
  // UNKNOWN COMMAND
  // ==========================================================

  sendError(
    id,
    cmd,
    "unknown_command"
  );
}