#include <ArduinoJson.h>

void setup() {
  Serial.begin(115200);

  delay(2000);

  Serial.println(
    "{\"type\":\"ready\",\"firmware\":\"0.2.0\"}"
  );
}

void loop() {

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

  // -------------------------
  // PING
  // -------------------------

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

  // -------------------------
  // UNKNOWN COMMAND
  // -------------------------

  JsonDocument response;

  response["type"] = "resp";
  response["id"] = id;
  response["cmd"] = cmd;
  response["ok"] = false;
  response["error"] = "unknown_command";

  serializeJson(response, Serial);
  Serial.println();
}