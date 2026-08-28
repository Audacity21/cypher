# Build Cypher from scratch

Use the [circuit guide](CIRCUIT.md) for wiring and the [setup guide](SETUP.md) for commands.

## 1. Assemble incrementally

Start with the Arduino and HC-SR04, then add the LDR divider, DHT11, RGB channels, and passive buzzer. Validate one device at a time. Never omit RGB resistors or common ground.

## 2. Firmware and serial protocol

`arduino/cypher_firmware/cypher_firmware.ino` implements sensor reads, newline-framed JSON, request IDs, RGB commands, buzzer tones, and defensive validation. Confirm the protocol at `115200` baud before building higher layers.

## 3. Hardware adapter

`backend/hardware/serial_manager.py` owns the serial reader and separates events from command responses. `hardware.py` exposes typed operations. Pin knowledge stays in firmware.

## 4. Perception

The perception package converts samples into `WorldState`, smooths range, calculates motion, classifies light/climate, and emits transition events. Tune thresholds for the installation room.

## 5. Deterministic intelligence

Map safety-relevant events to semantic intents before adding an LLM. The deterministic engine remains the fallback when Ollama fails or AI output is rejected.

## 6. Guarded local AI

Qwen crosses JSON parsing, schema validation, `IntelligenceGuard`, and `AuthorityPolicy`. The LLM never receives pin control or unrestricted shell access.

## 7. Behavior and actions

`BehaviorEngine` translates decisions into behavior. `ActionEngine` is the only backend layer invoking physical effects. Keep additions allowlisted and idempotent.

## 8. Persistence and conversation tools

SQLite stores conversations, memories, alarms, and timers. Deterministic sensor/action commands run before Qwen, preventing live-state questions from hallucinating.

## 9. Unified HUD

The React UI consumes WebSocket state and events. Browser speech APIs provide voice, while Three.js visualizes cognition. Text, music, subsystem health, telemetry, and event traces share one viewport.

## 10. Failure tests

Test Ollama stopped, Arduino disconnected, invalid AI output, noisy sensors, restart persistence, identity/memory, repeated music commands, and alarm-stop behavior. Commit only after tests, frontend build/lint, and relevant hardware checks pass.
