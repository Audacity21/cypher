#include <ArduinoJson.h>

// ============================================================
// CYPHER FIRMWARE
// Version 0.3.0
// ============================================================

const int TRIG_PIN = 9;
const int ECHO_PIN = 10;


// ============================================================
// Read Ultrasonic Distance
// ============================================================

float readDistanceCm() {

  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(
    ECHO_PIN,
    HIGH,
    30000
  );

  if (duration == 0) {
    return -1;
  }

  return duration * 0.0343 / 2.0;
}


// ============================================================
// Setup
// ============================================================

void setup() {

  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  delay(2000);

  Serial.println(
    "{\"type\":\"ready\",\"firmware\":\"0.3.0\"}"
  );
}


// ============================================================
// Main Loop
// ============================================================

void loop() {

  if (!Serial.available()) {
    return;
  }

  String input = Serial.readStringUntil('\n');
  input.trim();

  if (input.length() == 0) {
    return;
  }


  // ----------------------------------------------------------
  // Parse JSON
  // ----------------------------------------------------------

  JsonDocument request;

  DeserializationError error =
      deserializeJson(request, input);

  if (error) {

    Serial.println(
      "{\"type\":\"error\",\"ok\":false,\"error\":\"invalid_json\"}"
    );

    return;
  }


  // ----------------------------------------------------------
  // Extract Fields
  // ----------------------------------------------------------

  const char* type = request["type"];
  const char* id = request["id"];
  const char* cmd = request["cmd"];


  // ----------------------------------------------------------
  // Validate Fields
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

  if (strcmp(type, "cmd") != 0) {

    Serial.println(
      "{\"type\":\"error\",\"ok\":false,\"error\":\"invalid_type\"}"
    );

    return;
  }


  // ==========================================================
  // PING
  // ==========================================================

  if (strcmp(cmd, "PING") == 0) {

    JsonDocument response;

    response["type"] = "resp";
    response["id"] = id;
    response["cmd"] = "PING";
    response["ok"] = true;

    serializeJson(response, Serial);
    Serial.println();

    return;
  }


  // ==========================================================
  // GET_DISTANCE
  // ==========================================================

  if (strcmp(cmd, "GET_DISTANCE") == 0) {

    float distance = readDistanceCm();

    JsonDocument response;

    response["type"] = "resp";
    response["id"] = id;
    response["cmd"] = "GET_DISTANCE";

    if (distance >= 0) {

      response["ok"] = true;
      response["data"]["distance_cm"] = distance;

    } else {

      response["ok"] = false;
      response["error"] = "no_echo";
    }

    serializeJson(response, Serial);
    Serial.println();

    return;
  }


  // ==========================================================
  // UNKNOWN COMMAND
  // ==========================================================

  JsonDocument response;

  response["type"] = "resp";
  response["id"] = id;
  response["cmd"] = cmd;
  response["ok"] = false;
  response["error"] = "unknown_command";

  serializeJson(response, Serial);
  Serial.println();
}