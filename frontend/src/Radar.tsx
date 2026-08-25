import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

type RadarProps = {
  distanceCm: number | null;
};

function RadarScene({ distanceCm }: RadarProps) {
  const sweepRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (sweepRef.current) {
      sweepRef.current.rotation.z -= delta * 0.8;
    }
  });

  const normalizedDistance = useMemo(() => {
    if (distanceCm === null) return null;

    const maxDistance = 200;
    const clamped = Math.min(Math.max(distanceCm, 0), maxDistance);

    return clamped / maxDistance;
  }, [distanceCm]);

  const targetY =
    normalizedDistance !== null
      ? -2.2 + normalizedDistance * 4.4
      : 0;

  return (
    <>
      <ambientLight intensity={0.5} />

      <gridHelper
        args={[6, 12]}
        rotation={[Math.PI / 2, 0, 0]}
      />

      {[1, 2, 3].map((radius) => (
        <mesh key={radius}>
          <ringGeometry args={[radius - 0.01, radius, 96]} />
          <meshBasicMaterial
            color="#20e3ff"
            transparent
            opacity={0.2}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}

      <group ref={sweepRef}>
        <mesh position={[0, 1.5, 0]}>
          <planeGeometry args={[0.035, 3]} />
          <meshBasicMaterial
            color="#20e3ff"
            transparent
            opacity={0.65}
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>

      {distanceCm !== null && (
        <mesh position={[0, targetY, 0.05]}>
          <sphereGeometry args={[0.12, 24, 24]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
      )}

      <mesh position={[0, -2.9, 0.05]}>
        <circleGeometry args={[0.12, 32]} />
        <meshBasicMaterial color="#20e3ff" />
      </mesh>
    </>
  );
}

export default function Radar({ distanceCm }: RadarProps) {
  return (
    <div
      style={{
        width: "min(70vw, 700px)",
        height: "min(70vw, 700px)",
      }}
    >
      <Canvas
        orthographic
        camera={{
          position: [0, 0, 10],
          zoom: 80,
        }}
      >
        <RadarScene distanceCm={distanceCm} />
      </Canvas>
    </div>
  );
}