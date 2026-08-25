#include <ArduinoJson.h>

unsigned long lastEventTime = 0;

const unsigned long EVENT_INTERVAL = 5000;

void setup() {
  Serial.begin(115200);

  delay(2000);

  Serial.println(
    "{\"type\":\"ready\",\"firmware\":\"0.2.0\"}"
  );
}

void loop() {

  // ---------------------------------
  // TEST ASYNCHRONOUS EVENT
  // ---------------------------------

  unsigned long now = millis();

  if (now - lastEventTime >= EVENT_INTERVAL) {

    lastEventTime = now;

    JsonDocument event;

    event["type"] = "event";
    event["event"] = "test_event";
    event["data"]["value"] = 1;

    serializeJson(event, Serial);
    Serial.println();
  }


  // ---------------------------------
  // SERIAL COMMAND PROCESSING
  // ---------------------------------

  if (!Serial.available()) {
    return;
  }

  String input = Serial.readStringUntil('\n');
  input.trim();

  if (input.length() == 0) {
    return;
  }

  JsonDocument request;

  DeserializationError error =
      deserializeJson(request, input);

  if (error) {
    Serial.println(
      "{\"type\":\"error\",\"ok\":false,\"error\":\"invalid_json\"}"
    );
    return;
  }

  const char* type = request["type"];
  const char* id = request["id"];
  const char* cmd = request["cmd"];

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

  JsonDocument response;

  response["type"] = "resp";
  response["id"] = id;
  response["cmd"] = cmd;
  response["ok"] = false;
  response["error"] = "unknown_command";

  serializeJson(response, Serial);
  Serial.println();
}