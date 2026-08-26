import { useEffect, useState } from "react";

import Radar from "./Radar";

type SensorMessage = {
  type: string;
  event?: string;
  timestamp?: number;

  data?: {
    distance_cm?: number;
    smoothed_distance_cm?: number;
    velocity_cm_s?: number;
    motion?: string;

    light_raw?: number;
    light_percent?: number;
    light_state?: string;

    temperature_c?: number;
    temperature_state?: string;

    humidity_percent?: number;
    humidity_state?: string;

    total?: number;
    agreements?: number;
    disagreements?: number;
    agreement_rate?: number;

    last_authoritative_intent?: string | null;
    last_shadow_intent?: string | null;
    last_shadow_confidence?: number | null;
    last_agreement?: boolean | null;
  };

  decision?: {
    intent?: string;
    reason?: string;
    confidence?: number;
    valid?: boolean;
    agreement?: boolean;
    model?: string;
  };
};

type CypherEvent = {
  event: string;
  timestamp: number;
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

  const [lightPercent, setLightPercent] =
    useState<number | null>(null);

  const [lightState, setLightState] =
    useState("UNKNOWN");

  const [temperature, setTemperature] =
    useState<number | null>(null);

  const [
    temperatureState,
    setTemperatureState,
  ] = useState("UNKNOWN");

  const [humidity, setHumidity] =
    useState<number | null>(null);

  const [
    humidityState,
    setHumidityState,
  ] = useState("UNKNOWN");

  const [connected, setConnected] =
    useState(false);

  const [events, setEvents] =
    useState<CypherEvent[]>([]);

  const [shadowTotal, setShadowTotal] =
    useState(0);

  const [
    shadowAgreements,
    setShadowAgreements,
  ] = useState(0);

  const [
    shadowDisagreements,
    setShadowDisagreements,
  ] = useState(0);

  const [
    shadowAgreementRate,
    setShadowAgreementRate,
  ] = useState(0);

  const [
    shadowAuthoritative,
    setShadowAuthoritative,
  ] = useState<string | null>(null);

  const [
    shadowIntent,
    setShadowIntent,
  ] = useState<string | null>(null);

  const [
    shadowConfidence,
    setShadowConfidence,
  ] = useState<number | null>(null);

  const [
    shadowAgreement,
    setShadowAgreement,
  ] = useState<boolean | null>(null);

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

      // ----------------------------------
      // WORLD STATE
      // ----------------------------------

      if (
        message.type === "world_state" &&
        message.data
      ) {
        const data = message.data;

        if (
          data.smoothed_distance_cm !==
          undefined
        ) {
          setDistance(
            data.smoothed_distance_cm
          );
        }

        if (
          data.velocity_cm_s !==
          undefined
        ) {
          setVelocity(
            data.velocity_cm_s
          );
        }

        if (
          data.motion !== undefined
        ) {
          setMotion(
            data.motion
          );
        }

        if (
          data.light_raw !== undefined
        ) {
          setLight(
            data.light_raw
          );
        }

        if (
          data.light_percent !== undefined
        ) {
          setLightPercent(
            data.light_percent
          );
        }

        if (
          data.light_state !== undefined
        ) {
          setLightState(
            data.light_state
          );
        }

        if (
          data.temperature_c !== undefined
        ) {
          setTemperature(
            data.temperature_c
          );
        }

        if (
          data.temperature_state !==
          undefined
        ) {
          setTemperatureState(
            data.temperature_state
          );
        }

        if (
          data.humidity_percent !== undefined
        ) {
          setHumidity(
            data.humidity_percent
          );
        }

        if (
          data.humidity_state !== undefined
        ) {
          setHumidityState(
            data.humidity_state
          );
        }

        return;
      }

      // ----------------------------------
      // EVENT STREAM
      // ----------------------------------

      if (
        message.type === "event" &&
        message.event &&
        message.timestamp
      ) {
        const newEvent: CypherEvent = {
          event: message.event,
          timestamp: message.timestamp,
        };

        setEvents(
          (previous) => [
            newEvent,
            ...previous,
          ].slice(0, 6)
        );

        return;
      }

      // ----------------------------------
      // SHADOW METRICS
      // ----------------------------------

      if (
        message.type === "shadow_metrics" &&
        message.data
      ) {
        const data = message.data;

        setShadowTotal(
          data.total ?? 0
        );

        setShadowAgreements(
          data.agreements ?? 0
        );

        setShadowDisagreements(
          data.disagreements ?? 0
        );

        setShadowAgreementRate(
          data.agreement_rate ?? 0
        );

        setShadowAuthoritative(
          data.last_authoritative_intent
          ?? null
        );

        setShadowIntent(
          data.last_shadow_intent
          ?? null
        );

        setShadowConfidence(
          data.last_shadow_confidence
          ?? null
        );

        setShadowAgreement(
          data.last_agreement
          ?? null
        );

        return;
      }

      // ----------------------------------
      // SHADOW DECISION
      // ----------------------------------

      if (
        message.type ===
          "shadow_intelligence" &&
        message.decision
      ) {
        if (
          message.decision.intent !==
          undefined
        ) {
          setShadowIntent(
            message.decision.intent
          );
        }

        if (
          message.decision.confidence !==
          undefined
        ) {
          setShadowConfidence(
            message.decision.confidence
          );
        }

        if (
          message.decision.agreement !==
          undefined
        ) {
          setShadowAgreement(
            message.decision.agreement
          );
        }

        return;
      }
    };

    return () => {
      socket.close();
    };
  }, []);

  const motionClass =
    motion.toLowerCase();

  const agreementClass =
    shadowAgreement === null
      ? ""
      : shadowAgreement
        ? "ai-agree"
        : "ai-disagree";

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
            value={
              Math.abs(
                velocity
              ).toFixed(1)
            }
            unit="CM/S"
          />

          <div className="divider" />

          <PanelBlock
            label="AMBIENT LIGHT"
            value={
              lightPercent !== null
                ? lightPercent.toString()
                : "---"
            }
            unit="%"
          />

          <PanelBlock
            label="LIGHT STATE"
            value={lightState}
          />

          <div className="divider" />

          <div className="mini-label">
            RAW LIGHT
          </div>

          <div className="sensor-name">
            {light !== null
              ? light
              : "---"}
          </div>

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
              <strong>
                200 CM
              </strong>
            </div>

            <div>
              LIGHT
              <strong>
                {lightState}
              </strong>
            </div>

            <div>
              AI SHADOW
              <strong>
                {shadowAgreementRate.toFixed(1)}%
              </strong>
            </div>

          </div>

        </section>

        <aside className="side-panel right-panel">

          <div className="panel-heading">
            ENVIRONMENT
          </div>

          <div className="analysis-row">
            <span>
              TEMPERATURE
            </span>

            <strong>
              {temperature !== null
                ? `${temperature.toFixed(1)}°C`
                : "---"}
            </strong>
          </div>

          <div className="analysis-row">
            <span>
              HUMIDITY
            </span>

            <strong>
              {humidity !== null
                ? `${humidity.toFixed(1)}%`
                : "---"}
            </strong>
          </div>

          <div className="divider" />

          <div className="panel-heading">
            AI SHADOW // QWEN
          </div>

          <div className="analysis-row">
            <span>
              MODE
            </span>

            <strong>
              SHADOW
            </strong>
          </div>

          <div className="analysis-row">
            <span>
              DECISIONS
            </span>

            <strong>
              {shadowTotal}
            </strong>
          </div>

          <div className="analysis-row">
            <span>
              AGREEMENT
            </span>

            <strong>
              {shadowAgreementRate.toFixed(1)}%
            </strong>
          </div>

          <div className="analysis-row">
            <span>
              AGREE / DISAGREE
            </span>

            <strong>
              {shadowAgreements}
              {" / "}
              {shadowDisagreements}
            </strong>
          </div>

          <div className="divider" />

          <div className="panel-heading">
            LAST DECISION
          </div>

          <div className="analysis-row">
            <span>
              RULE ENGINE
            </span>

            <strong>
              {shadowAuthoritative ?? "---"}
            </strong>
          </div>

          <div className="analysis-row">
            <span>
              QWEN
            </span>

            <strong>
              {shadowIntent ?? "---"}
            </strong>
          </div>

          <div className="analysis-row">
            <span>
              CONFIDENCE
            </span>

            <strong>
              {shadowConfidence !== null
                ? `${(
                    shadowConfidence * 100
                  ).toFixed(0)}%`
                : "---"}
            </strong>
          </div>

          <div className="analysis-row">
            <span>
              RESULT
            </span>

            <strong
              className={
                agreementClass
              }
            >
              {shadowAgreement === null
                ? "---"
                : shadowAgreement
                  ? "AGREE"
                  : "DISAGREE"}
            </strong>
          </div>

          <div className="divider" />

          <div className="panel-heading">
            LIVE EVENT STREAM
          </div>

          <div className="event-stream">

            {events.length === 0 ? (
              <div className="event-empty">
                NO EVENTS
              </div>
            ) : (
              events.map(
                (item, index) => (
                  <div
                    className="event-row"
                    key={
                      `${item.timestamp}-${index}`
                    }
                  >
                    <span className="event-time">
                      {formatTime(
                        item.timestamp
                      )}
                    </span>

                    <strong>
                      {formatEventName(
                        item.event
                      )}
                    </strong>
                  </div>
                )
              )
            )}

          </div>

        </aside>

      </section>

      <footer className="bottom-bar">

        <div>
          CYPHER // INTELLIGENCE CORE
        </div>

        <div className="bottom-center">
          <span />

          QWEN SHADOW EVALUATION

          <span />
        </div>

        <div>
          BUILD 0.8
        </div>

      </footer>

    </main>
  );
}

function formatTime(
  timestamp: number
) {
  return new Date(
    timestamp * 1000
  ).toLocaleTimeString(
    [],
    {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }
  );
}

function formatEventName(
  event: string
) {
  return event.replaceAll(
    "_",
    " "
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
        className={
          `metric-value ${className}`
        }
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

export default App;