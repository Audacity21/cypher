#include <ArduinoJson.h>
#include <DHT.h>

// ============================================================
// CYPHER FIRMWARE
// Version 0.5.0
// ============================================================

// -------------------------
// Pins
// -------------------------

const int TRIG_PIN = 9;
const int ECHO_PIN = 10;
const int LDR_PIN = A0;

#define DHT_PIN 7
#define DHT_TYPE DHT11

DHT dht(DHT_PIN, DHT_TYPE);


// ============================================================
// Sensor Helpers
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
// Response Helpers
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

  serializeJson(response, Serial);
  Serial.println();
}


// ============================================================
// Setup
// ============================================================

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  pinMode(LDR_PIN, INPUT);

  dht.begin();

  delay(2000);

  Serial.println(
    "{\"type\":\"ready\",\"firmware\":\"0.5.0\"}"
  );
}


// ============================================================
// Main Loop
// ============================================================

void loop() {

  if (!Serial.available()) {
    return;
  }

  String input =
    Serial.readStringUntil('\n');

  input.trim();

  if (input.length() == 0) {
    return;
  }


  // ----------------------------------------------------------
  // Parse JSON
  // ----------------------------------------------------------

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


  // ----------------------------------------------------------
  // Extract Fields
  // ----------------------------------------------------------

  const char* type =
    request["type"];

  const char* id =
    request["id"];

  const char* cmd =
    request["cmd"];


  // ----------------------------------------------------------
  // Validate Request
  // ----------------------------------------------------------

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
    strcmp(type, "cmd") != 0
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
    strcmp(cmd, "PING") == 0
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

    if (distance >= 0) {
      response["ok"] = true;

      response["data"]
              ["distance_cm"] =
        distance;
    } else {
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
  // UNKNOWN COMMAND
  // ==========================================================

  sendError(
    id,
    cmd,
    "unknown_command"
  );
}