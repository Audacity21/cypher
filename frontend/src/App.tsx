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

    guard_accepted?: number;
    guard_blocked?: number;
    guard_acceptance_rate?: number;

    authority_granted?: number;
    authority_denied?: number;
    authority_grant_rate?: number;

    last_authoritative_intent?: string | null;
    last_shadow_intent?: string | null;
    last_shadow_confidence?: number | null;
    last_agreement?: boolean | null;

    last_guard_allowed?: boolean | null;
    last_guard_reason?: string | null;

    last_authority_allowed?: boolean | null;
    last_authority_reason?: string | null;
    last_decision_source?: string;
  };

  decision?: {
    intent?: string;
    reason?: string;
    confidence?: number;
    valid?: boolean;
    agreement?: boolean;
    model?: string;

    guard_allowed?: boolean;
    guard_reason?: string;
    authority_allowed?: boolean;
    authority_reason?: string;
  };
};


type CypherEvent = {
  event: string;
  timestamp: number;
};


function App() {
  // =========================================================
  // WORLD STATE
  // =========================================================

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


  // =========================================================
  // CONNECTION
  // =========================================================

  const [connected, setConnected] =
    useState(false);


  // =========================================================
  // EVENT STREAM
  // =========================================================

  const [events, setEvents] =
    useState<CypherEvent[]>([]);


  // =========================================================
  // SHADOW AI METRICS
  // =========================================================

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


  // =========================================================
  // LAST SHADOW DECISION
  // =========================================================

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


  // =========================================================
  // GUARD METRICS
  // =========================================================

  const [
    guardAccepted,
    setGuardAccepted,
  ] = useState(0);

  const [
    guardBlocked,
    setGuardBlocked,
  ] = useState(0);

  const [
    guardAcceptanceRate,
    setGuardAcceptanceRate,
  ] = useState(0);

  const [
    lastGuardAllowed,
    setLastGuardAllowed,
  ] = useState<boolean | null>(null);

  const [
    lastGuardReason,
    setLastGuardReason,
  ] = useState<string | null>(null);

  const [authorityGranted, setAuthorityGranted] =
    useState(0);

  const [authorityDenied, setAuthorityDenied] =
    useState(0);

  const [authorityGrantRate, setAuthorityGrantRate] =
    useState(0);

  const [lastAuthorityAllowed, setLastAuthorityAllowed] =
    useState<boolean | null>(null);

  const [lastAuthorityReason, setLastAuthorityReason] =
    useState<string | null>(null);

  const [lastDecisionSource, setLastDecisionSource] =
    useState("DETERMINISTIC");


  // =========================================================
  // WEBSOCKET
  // =========================================================

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


      // =====================================================
      // WORLD STATE
      // =====================================================

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


      // =====================================================
      // EVENTS
      // =====================================================

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


      // =====================================================
      // SHADOW METRICS
      // =====================================================

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


        setGuardAccepted(
          data.guard_accepted ?? 0
        );

        setGuardBlocked(
          data.guard_blocked ?? 0
        );

        setGuardAcceptanceRate(
          data.guard_acceptance_rate ?? 0
        );

        setAuthorityGranted(
          data.authority_granted ?? 0
        );

        setAuthorityDenied(
          data.authority_denied ?? 0
        );

        setAuthorityGrantRate(
          data.authority_grant_rate ?? 0
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


        setLastGuardAllowed(
          data.last_guard_allowed
          ?? null
        );

        setLastGuardReason(
          data.last_guard_reason
          ?? null
        );

        setLastAuthorityAllowed(
          data.last_authority_allowed
          ?? null
        );

        setLastAuthorityReason(
          data.last_authority_reason
          ?? null
        );

        setLastDecisionSource(
          (data.last_decision_source ?? "deterministic").toUpperCase()
        );

        return;
      }


      // =====================================================
      // SHADOW DECISION
      // =====================================================

      if (
        message.type ===
          "shadow_intelligence" &&
        message.decision
      ) {
        const decision =
          message.decision;


        if (
          decision.intent !== undefined
        ) {
          setShadowIntent(
            decision.intent
          );
        }


        if (
          decision.confidence !==
          undefined
        ) {
          setShadowConfidence(
            decision.confidence
          );
        }


        if (
          decision.agreement !==
          undefined
        ) {
          setShadowAgreement(
            decision.agreement
          );
        }


        if (
          decision.guard_allowed !==
          undefined
        ) {
          setLastGuardAllowed(
            decision.guard_allowed
          );
        }


        if (
          decision.guard_reason !==
          undefined
        ) {
          setLastGuardReason(
            decision.guard_reason
          );
        }

        if (
          decision.authority_allowed !== undefined
        ) {
          setLastAuthorityAllowed(
            decision.authority_allowed
          );
          setLastDecisionSource(
            decision.authority_allowed
              ? "AI"
              : "DETERMINISTIC"
          );
        }

        if (
          decision.authority_reason !== undefined
        ) {
          setLastAuthorityReason(
            decision.authority_reason
          );
        }

        return;
      }
    };


    return () => {
      socket.close();
    };
  }, []);


  // =========================================================
  // DISPLAY HELPERS
  // =========================================================

  const motionClass =
    motion.toLowerCase();


  const agreementClass =
    shadowAgreement === null
      ? ""
      : shadowAgreement
        ? "ai-agree"
        : "ai-disagree";


  const guardClass =
    lastGuardAllowed === null
      ? ""
      : lastGuardAllowed
        ? "ai-agree"
        : "ai-disagree";

  const authorityClass =
    lastAuthorityAllowed === null
      ? ""
      : lastAuthorityAllowed
        ? "ai-agree"
        : "ai-disagree";


  return (
    <main className="app-shell">

      <div className="background-grid" />


      {/* ====================================================
          HEADER
          ==================================================== */}

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


      {/* ====================================================
          MAIN WORKSPACE
          ==================================================== */}

      <section className="workspace">


        {/* ==================================================
            LEFT — SENSOR STATE
            ================================================== */}

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


          <div className="mini-label top-gap">
            LIGHT SENSOR
          </div>

          <div className="sensor-name">
            LDR // A0
          </div>

        </aside>


        {/* ==================================================
            CENTER — RADAR
            ================================================== */}

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
              AI AUTHORITY

              <strong>
                {authorityGrantRate.toFixed(1)}%
              </strong>
            </div>

          </div>

        </section>


        {/* ==================================================
            RIGHT — AI / ENVIRONMENT
            ================================================== */}

        <aside className="side-panel right-panel">


          {/* =================================================
              ENVIRONMENT
              ================================================= */}

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
              TEMP STATE
            </span>

            <strong>
              {temperatureState}
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


          <div className="analysis-row">
            <span>
              HUMIDITY STATE
            </span>

            <strong>
              {humidityState}
            </strong>
          </div>


          <div className="divider" />


          {/* =================================================
              AI SHADOW
              ================================================= */}

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


          {/* =================================================
              GUARD METRICS
              ================================================= */}

          <div className="analysis-row">
            <span>
              GUARD PASS
            </span>

            <strong>
              {guardAcceptanceRate.toFixed(1)}%
            </strong>
          </div>


          <div className="analysis-row">
            <span>
              ACCEPT / BLOCK
            </span>

            <strong>
              {guardAccepted}
              {" / "}
              {guardBlocked}
            </strong>
          </div>


          <div className="analysis-row">
            <span>
              AUTHORITY RATE
            </span>

            <strong>
              {authorityGrantRate.toFixed(1)}%
            </strong>
          </div>


          <div className="analysis-row">
            <span>
              GRANT / DENY
            </span>

            <strong>
              {authorityGranted}
              {" / "}
              {authorityDenied}
            </strong>
          </div>


          <div className="divider" />


          {/* =================================================
              LAST DECISION
              ================================================= */}

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


          <div className="analysis-row">
            <span>
              GUARD
            </span>

            <strong
              className={
                guardClass
              }
            >
              {lastGuardAllowed === null
                ? "---"
                : lastGuardAllowed
                  ? "ACCEPTED"
                  : "BLOCKED"}
            </strong>
          </div>


          <div className="analysis-row">
            <span>
              GUARD REASON
            </span>

            <strong>
              {lastGuardReason ?? "---"}
            </strong>
          </div>


          <div className="analysis-row">
            <span>
              AUTHORITY
            </span>

            <strong className={authorityClass}>
              {lastAuthorityAllowed === null
                ? "---"
                : lastAuthorityAllowed
                  ? "GRANTED"
                  : "FALLBACK"}
            </strong>
          </div>


          <div className="analysis-row">
            <span>
              ACTIVE SOURCE
            </span>

            <strong>
              {lastDecisionSource}
            </strong>
          </div>


          <div className="analysis-row">
            <span>
              POLICY REASON
            </span>

            <strong>
              {lastAuthorityReason ?? "---"}
            </strong>
          </div>


          <div className="divider" />


          {/* =================================================
              EVENTS
              ================================================= */}

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


      {/* ====================================================
          FOOTER
          ==================================================== */}

      <footer className="bottom-bar">

        <div>
          CYPHER // INTELLIGENCE CORE
        </div>


        <div className="bottom-center">
          <span />

          LIMITED QWEN AUTHORITY

          <span />
        </div>


        <div>
          BUILD 0.9
        </div>

      </footer>

    </main>
  );
}


// ============================================================
// HELPERS
// ============================================================

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


// ============================================================
// PANEL BLOCK
// ============================================================

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
