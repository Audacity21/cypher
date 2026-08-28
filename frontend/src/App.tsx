import { useEffect, useState } from "react";
import Radar from "./Radar";

type WorldData = {
  smoothed_distance_cm?: number; velocity_cm_s?: number; motion?: string;
  light?: number; light_raw?: number; light_percent?: number; light_state?: string;
  temperature_c?: number; temperature_state?: string;
  humidity_percent?: number; humidity_state?: string;
};
type StreamMessage = { type: string; event?: string; timestamp?: number; data?: WorldData };
type CypherEvent = { event: string; timestamp: number };

const value = (number: number | null, digits = 1) => number === null ? "---" : number.toFixed(digits);

export default function App() {
  const [connected, setConnected] = useState(false);
  const [distance, setDistance] = useState<number | null>(null);
  const [velocity, setVelocity] = useState<number | null>(null);
  const [motion, setMotion] = useState("UNKNOWN");
  const [lightRaw, setLightRaw] = useState<number | null>(null);
  const [lightPercent, setLightPercent] = useState<number | null>(null);
  const [lightState, setLightState] = useState("UNKNOWN");
  const [temperature, setTemperature] = useState<number | null>(null);
  const [temperatureState, setTemperatureState] = useState("UNKNOWN");
  const [humidity, setHumidity] = useState<number | null>(null);
  const [humidityState, setHumidityState] = useState("UNKNOWN");
  const [events, setEvents] = useState<CypherEvent[]>([]);

  useEffect(() => {
    let socket: WebSocket;
    let retry: number;
    const connect = () => {
      socket = new WebSocket("ws://127.0.0.1:8000/ws/sensors");
      socket.onopen = () => setConnected(true);
      socket.onerror = () => setConnected(false);
      socket.onclose = () => { setConnected(false); retry = window.setTimeout(connect, 1500); };
      socket.onmessage = ({ data: raw }) => {
        const message = JSON.parse(raw) as StreamMessage;
        if (message.type === "world_state" && message.data) {
          const data = message.data;
          if (data.smoothed_distance_cm !== undefined) setDistance(data.smoothed_distance_cm);
          if (data.velocity_cm_s !== undefined) setVelocity(data.velocity_cm_s);
          if (data.motion !== undefined) setMotion(data.motion);
          if (data.light_raw !== undefined) setLightRaw(data.light_raw);
          else if (data.light !== undefined) setLightRaw(data.light);
          if (data.light_percent !== undefined) setLightPercent(data.light_percent);
          if (data.light_state !== undefined) setLightState(data.light_state);
          if (data.temperature_c !== undefined) setTemperature(data.temperature_c);
          if (data.temperature_state !== undefined) setTemperatureState(data.temperature_state);
          if (data.humidity_percent !== undefined) setHumidity(data.humidity_percent);
          if (data.humidity_state !== undefined) setHumidityState(data.humidity_state);
        }
        if (message.type === "event" && message.event && message.timestamp) {
          setEvents(previous => [{ event: message.event!, timestamp: message.timestamp! }, ...previous].slice(0, 5));
        }
      };
    };
    connect();
    return () => { window.clearTimeout(retry); socket?.close(); };
  }, []);

  return <main className="command-shell">
    <div className="command-grid-bg" />
    <header className="command-header">
      <div><span>LOCAL ROOM INTELLIGENCE</span><h1>CYPHER</h1></div>
      <div className={connected ? "system-live" : "system-down"}><i />{connected ? "SYSTEM ONLINE" : "RECONNECTING"}</div>
    </header>

    <section className="command-layout">
      <aside className="telemetry-rail">
        <div className="rail-title">ROOM TELEMETRY</div>
        <Metric label="ULTRASONIC RANGE" reading={value(distance)} unit="CM" accent />
        <Metric label="MOTION" reading={motion} />
        <Metric label="VELOCITY" reading={value(velocity)} unit="CM/S" />
        <div className="rail-rule" />
        <Metric label="AMBIENT LIGHT" reading={lightPercent === null ? "---" : `${lightPercent}`} unit="%" />
        <Metric label="LIGHT CLASS" reading={lightState} />
        <Metric label="RAW // A0" reading={lightRaw === null ? "---" : `${lightRaw}`} />
        <div className="rail-rule" />
        <Metric label="TEMPERATURE" reading={value(temperature)} unit="°C" accent />
        <Metric label="THERMAL CLASS" reading={temperatureState} />
        <Metric label="HUMIDITY" reading={value(humidity)} unit="%" />
        <Metric label="AIR CLASS" reading={humidityState} />
      </aside>

      <section className="spatial-stage">
        <div className="stage-heading"><span>COGNITION CORE</span><strong>THREE.JS SYSTEM MATRIX</strong></div>
        <Radar online={connected} />
        <div className="stage-strip">
          <span>REASONING <b>LOCAL QWEN</b></span><span>CONTEXT <b>PERSISTENT</b></span><span>ENVIRONMENT <b>{lightState}</b></span>
        </div>
      </section>

      <aside className="interaction-rail">
        <div className="rail-title">CYPHER INTERFACE</div>
        <iframe className="unified-voice" src="/voice.html?embedded=1" title="Cypher voice interface" allow="microphone" />
        <MusicDock />
        <SystemMatrix
          connected={connected}
          sensorsOnline={distance !== null || lightRaw !== null || temperature !== null}
        />
        <div className="event-heading"><span>EVENT TRACE</span><b>{events.length.toString().padStart(2, "0")}</b></div>
        <div className="compact-events">
          {events.length === 0 ? <p>AWAITING ROOM EVENT</p> : events.map(item => <div key={`${item.timestamp}-${item.event}`}><time>{new Date(item.timestamp * 1000).toLocaleTimeString([], { hour12: false })}</time><strong>{item.event.replaceAll("_", " ")}</strong></div>)}
        </div>
      </aside>
    </section>

    <footer className="command-footer"><span>CYPHER // BUILD 1.0</span><strong>VOICE · MEMORY · PERCEPTION · CONTROL</strong><span>LOCAL AUTHORITY</span></footer>
  </main>;
}

function SystemMatrix({ connected, sensorsOnline }: { connected: boolean; sensorsOnline: boolean }) {
  const systems = [
    ["BACKEND", connected ? "ONLINE" : "OFFLINE", connected],
    ["ARDUINO", sensorsOnline ? "STREAMING" : "WAITING", sensorsOnline],
    ["PERCEPTION", sensorsOnline ? "ACTIVE" : "STANDBY", sensorsOnline],
    ["VOICE", "WAKE ARMED", true],
    ["MEMORY", "SQLITE ACTIVE", true],
    ["MUSIC", "SINGLE TAB", true],
    ["REASONING", "QWEN LOCAL", true],
    ["AUTHORITY", "GUARDED", true],
  ] as const;
  return <section className="system-matrix">
    <div className="system-matrix-title">ACTIVE SYSTEMS <b>{systems.filter(item => item[2]).length}/{systems.length}</b></div>
    <div className="system-matrix-grid">
      {systems.map(([name, status, active]) => <div className={active ? "active" : "inactive"} key={name}><i /><span>{name}</span><strong>{status}</strong></div>)}
    </div>
  </section>;
}

function MusicDock() {
  const [source, setSource] = useState("");
  const [embed, setEmbed] = useState("");
  const [nowPlaying, setNowPlaying] = useState("STANDBY");

  useEffect(() => {
    const receiveCommand = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "CYPHER_STOP_MUSIC") {
        setSource("");
        setEmbed("");
        setNowPlaying("STANDBY");
        return;
      }
      if (event.data?.type !== "CYPHER_PLAY_MUSIC") return;
      const videoId = typeof event.data.videoId === "string" ? event.data.videoId : "";
      if (!/^[A-Za-z0-9_-]{11}$/.test(videoId)) return;
      const title = typeof event.data.title === "string" ? event.data.title : "TRACK";
      const watchUrl = typeof event.data.watchUrl === "string" ? event.data.watchUrl : `https://music.youtube.com/watch?v=${videoId}`;
      setSource(watchUrl);
      setNowPlaying(title.toUpperCase());
      setEmbed(`https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?autoplay=1&controls=1&playsinline=1&rel=0&origin=${encodeURIComponent(window.location.origin)}`);
    };
    window.addEventListener("message", receiveCommand);
    return () => window.removeEventListener("message", receiveCommand);
  }, []);
  return <section className="music-dock">
    <div><span>YOUTUBE MUSIC // {nowPlaying}</span>{source && <a href={source} target="_blank" rel="noreferrer">OPEN TRACK</a>}</div>
    {embed ? <iframe key={embed} src={embed} title="Cypher music player" allow="autoplay; encrypted-media" referrerPolicy="strict-origin-when-cross-origin" /> : <p>ASK CYPHER TO PLAY A SONG</p>}
  </section>;
}

function Metric({ label, reading, unit, accent = false }: { label: string; reading: string; unit?: string; accent?: boolean }) {
  return <div className={`rail-metric${accent ? " accent" : ""}`}><span>{label}</span><strong>{reading}{unit && <small>{unit}</small>}</strong></div>;
}
