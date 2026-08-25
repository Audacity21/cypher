import { useEffect, useState } from "react";

import Radar from "./Radar";

type SensorMessage = {
  type: string;

  data?: {
    distance_cm?: number;
    smoothed_distance_cm?: number;
    velocity_cm_s?: number;
    motion?: string;

    light?: number;
    light_state?: string;
  };
};

function App() {
  const [distance, setDistance] =
    useState<number | null>(null);

  const [velocity, setVelocity] =
    useState(0);

  const [motion, setMotion] =
    useState("UNKNOWN");

  const [light, setLight] =
    useState<number | null>(null);

  const [lightState, setLightState] =
    useState("UNKNOWN");

  const [connected, setConnected] =
    useState(false);

  useEffect(() => {
    const socket = new WebSocket(
      "ws://127.0.0.1:8000/ws/sensors"
    );

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onclose = () => {
      setConnected(false);
    };

    socket.onerror = () => {
      setConnected(false);
    };

    socket.onmessage = (event) => {
      const message: SensorMessage =
        JSON.parse(event.data);

      if (
        message.type !== "sensor_state" ||
        !message.data
      ) {
        return;
      }

      if (
        message.data.smoothed_distance_cm
        !== undefined
      ) {
        setDistance(
          message.data.smoothed_distance_cm
        );
      }

      if (
        message.data.velocity_cm_s
        !== undefined
      ) {
        setVelocity(
          message.data.velocity_cm_s
        );
      }

      if (
        message.data.motion
        !== undefined
      ) {
        setMotion(
          message.data.motion
        );
      }

      if (
        message.data.light
        !== undefined
      ) {
        setLight(
          message.data.light
        );
      }

      if (
        message.data.light_state
        !== undefined
      ) {
        setLightState(
          message.data.light_state
        );
      }
    };

    return () => {
      socket.close();
    };
  }, []);

  const motionClass =
    motion.toLowerCase();

  return (
    <main className="app-shell">

      <div className="background-grid" />

      <header className="topbar">
        <div>
          <div className="eyebrow">
            LOCAL INTELLIGENCE SYSTEM
          </div>

          <div className="brand">
            CYPHER
          </div>
        </div>

        <div
          className={
            connected
              ? "connection online"
              : "connection offline"
          }
        >
          <span className="status-dot" />

          {connected
            ? "PERCEPTION ONLINE"
            : "PERCEPTION OFFLINE"}
        </div>
      </header>

      <section className="workspace">

        <aside className="side-panel left-panel">

          <PanelBlock
            label="RANGE"
            value={
              distance !== null
                ? distance.toFixed(1)
                : "--.-"
            }
            unit="CM"
          />

          <PanelBlock
            label="MOTION"
            value={motion}
            className={motionClass}
          />

          <PanelBlock
            label="VELOCITY"
            value={Math.abs(
              velocity
            ).toFixed(1)}
            unit="CM/S"
          />

          <div className="divider" />

          <PanelBlock
            label="AMBIENT LIGHT"
            value={
              light !== null
                ? light.toString()
                : "---"
            }
          />

          <PanelBlock
            label="LIGHT STATE"
            value={lightState}
          />

        </aside>

        <section className="radar-zone">

          <div className="radar-title">
            PERCEPTION // ULTRASONIC
          </div>

          <div className="radar-frame">
            <Radar
              distanceCm={distance}
              motion={motion}
              velocity={velocity}
            />
          </div>

          <div className="radar-footer">

            <div>
              RANGE LIMIT
              <strong>200 CM</strong>
            </div>

            <div>
              LIGHT
              <strong>{lightState}</strong>
            </div>

            <div>
              TRACK
              <strong>
                {distance !== null
                  ? "LOCKED"
                  : "SEARCHING"}
              </strong>
            </div>

          </div>

        </section>

        <aside className="side-panel right-panel">

          <div className="panel-heading">
            TRACK ANALYSIS
          </div>

          <div className="analysis-row">
            <span>TARGET</span>

            <strong>
              {distance !== null
                ? "DETECTED"
                : "NONE"}
            </strong>
          </div>

          <div className="analysis-row">
            <span>VECTOR</span>

            <strong>
              {motion}
            </strong>
          </div>

          <div className="analysis-row">
            <span>LIGHT</span>

            <strong>
              {lightState}
            </strong>
          </div>

          <div className="divider" />

          <div className="panel-heading">
            SYSTEM
          </div>

          <SystemRow
            name="ARDUINO"
            online={connected}
          />

          <SystemRow
            name="SERIAL BUS"
            online={connected}
          />

          <SystemRow
            name="ULTRASONIC"
            online={distance !== null}
          />

          <SystemRow
            name="LIGHT SENSOR"
            online={light !== null}
          />

          <SystemRow
            name="AI CORE"
            online={false}
            text="PENDING"
          />

        </aside>

      </section>

      <footer className="bottom-bar">

        <div>
          CYPHER // PERCEPTION CORE
        </div>

        <div className="bottom-center">
          <span />
          MULTI-SENSOR FEED
          <span />
        </div>

        <div>
          BUILD 0.4
        </div>

      </footer>

    </main>
  );
}

type PanelBlockProps = {
  label: string;
  value: string;
  unit?: string;
  className?: string;
};

function PanelBlock({
  label,
  value,
  unit,
  className = "",
}: PanelBlockProps) {
  return (
    <div className="metric">

      <div className="metric-label">
        {label}
      </div>

      <div
        className={`metric-value ${className}`}
      >
        {value}

        {unit && (
          <span>
            {unit}
          </span>
        )}
      </div>

    </div>
  );
}

function SystemRow({
  name,
  online,
  text,
}: {
  name: string;
  online: boolean;
  text?: string;
}) {
  return (
    <div className="system-row">

      <span>
        {name}
      </span>

      <strong
        className={
          online
            ? "system-ok"
            : "system-pending"
        }
      >
        {text ??
          (
            online
              ? "ONLINE"
              : "OFFLINE"
          )}
      </strong>

    </div>
  );
}

export default App;