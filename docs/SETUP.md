# Cypher setup and run guide

This guide installs an existing Cypher checkout on Windows. Current defaults are Arduino `COM5`, backend port `8000`, frontend port `5173`, and Ollama at `127.0.0.1:11434`.

## Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- Arduino IDE 2.x
- Ollama
- Chrome or Edge
- The assembled [Cypher circuit](CIRCUIT.md)

## 1. Firmware

In Arduino IDE, install **ArduinoJson**, **DHT sensor library** by Adafruit, and **Adafruit Unified Sensor** if requested. Open `arduino/cypher_firmware/cypher_firmware.ino`, select **Arduino UNO R4 Minima**, choose the serial port, and upload. Close Serial Monitor afterward.

## 2. Backend

```powershell
Set-Location E:\cypher
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the Arduino is not `COM5`, update `CypherHardware(port=...)` in `backend/app.py`.
Cypher uses the operating system timezone by default. To pin it explicitly, set `$env:CYPHER_TIMEZONE="Asia/Kolkata"` before starting the backend.

## 3. Local model

```powershell
ollama pull qwen2.5:1.5b
```

## 4. Frontend

```powershell
Set-Location E:\cypher\frontend
npm install
```

## 5. Start Cypher

Use three terminals:

```powershell
ollama serve
```

```powershell
Set-Location E:\cypher
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

```powershell
Set-Location E:\cypher\frontend
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/` in Chrome or Edge, allow microphone access, and hard-refresh if an older HUD is cached.

## Verification

1. Confirm **SYSTEM ONLINE**.
2. Move an object near the HC-SR04 and verify range changes.
3. Cover the LDR and verify light classification changes.
4. Ask “Cypher, what is the temperature?” and compare the reply with the HUD.
5. Ask for yellow lights and run a sound check.
6. Set a ten-second timer.
7. Ask Cypher to play a song; autoplay may require one initial player interaction.

## Tests

The hardware tests open the serial port; do not run them while the backend owns the Arduino.

```powershell
Set-Location E:\cypher
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

For mocked checks while the backend is running:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q `
  --ignore=backend/tests/test_action_engine.py `
  --ignore=backend/tests/test_rgb.py `
  --ignore=backend/tests/test_serial_manager.py
```

```powershell
Set-Location E:\cypher\frontend
npm run build
npm run lint
```

## Troubleshooting

- **COM5 access denied:** close Serial Monitor and duplicate backend processes.
- **Wake word unavailable:** use Chrome or Edge and allow microphone access.
- **Ollama unavailable:** run `ollama serve` and confirm the model appears in `ollama list`.
- **Stale interface:** press `Ctrl+F5`.
- **Music does not autoplay:** interact with the HUD player once.
- **No readings:** verify `115200` baud, port, 5 V, and common ground.
