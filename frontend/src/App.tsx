import { useEffect, useState } from "react";

import Radar from "./Radar";

type SensorMessage = {
  type: string;
  sensor?: string;
  data?: {
    distance_cm?: number;
  };
};

function App() {
  const [distance, setDistance] = useState<number | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socket = new WebSocket(
      "ws://127.0.0.1:8000/ws/sensors"
    );

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const message: SensorMessage = JSON.parse(event.data);

      if (
        message.type === "sensor" &&
        message.sensor === "distance" &&
        message.data?.distance_cm !== undefined
      ) {
        setDistance(message.data.distance_cm);
      }
    };

    socket.onclose = () => {
      setConnected(false);
    };

    return () => {
      socket.close();
    };
  }, []);

  return (
    <main
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at center, #0b1530 0%, #050816 50%, #02030a 100%)",
        color: "white",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "Inter, system-ui, sans-serif",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 24,
          left: 32,
          letterSpacing: "0.35em",
          fontWeight: 600,
        }}
      >
        CYPHER
      </div>

      <div
        style={{
          position: "absolute",
          top: 24,
          right: 32,
          fontSize: "0.8rem",
          letterSpacing: "0.18em",
          opacity: 0.7,
        }}
      >
        {connected ? "PERCEPTION // ONLINE" : "PERCEPTION // OFFLINE"}
      </div>

      <Radar distanceCm={distance} />

      <div
        style={{
          position: "absolute",
          bottom: 46,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontSize: "3rem",
            fontWeight: 700,
          }}
        >
          {distance !== null
            ? `${distance.toFixed(1)} cm`
            : "--.- cm"}
        </div>

        <div
          style={{
            marginTop: 8,
            fontSize: "0.75rem",
            letterSpacing: "0.25em",
            opacity: 0.5,
          }}
        >
          TARGET RANGE
        </div>
      </div>
    </main>
  );
}

export default App;