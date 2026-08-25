import {
  Canvas,
  useFrame,
} from "@react-three/fiber";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import * as THREE from "three";

type RadarProps = {
  distanceCm: number | null;
  motion: string;
  velocity: number;
};

type TrailPoint = {
  y: number;
  opacity: number;
};

const MAX_DISTANCE = 200;

function RadarScene({
  distanceCm,
  motion,
}: RadarProps) {
  const sweepRef =
    useRef<THREE.Group>(null);

  const pulseRef =
    useRef<THREE.Mesh>(null);

  const [trail, setTrail] =
    useState<TrailPoint[]>([]);

  const normalizedDistance =
    useMemo(() => {
      if (distanceCm === null) {
        return null;
      }

      const clamped =
        Math.min(
          Math.max(
            distanceCm,
            0
          ),
          MAX_DISTANCE
        );

      return (
        clamped /
        MAX_DISTANCE
      );
    }, [distanceCm]);

  /*
   * Origin is near the bottom.
   * 0 cm   -> y = -2.5
   * 200 cm -> y =  2.5
   */
  const targetY =
    normalizedDistance === null
      ? null
      : -2.5 +
        normalizedDistance * 5;

  useEffect(() => {
    if (targetY === null) {
      return;
    }

    setTrail(
      (previous) => {
        const updated =
          previous.map(
            (point) => ({
              ...point,
              opacity:
                point.opacity *
                0.72,
            })
          );

        return [
          {
            y: targetY,
            opacity: 0.7,
          },
          ...updated,
        ].slice(0, 9);
      }
    );
  }, [targetY]);

  useFrame(
    ({ clock }, delta) => {

      if (
        sweepRef.current
      ) {
        sweepRef.current.rotation.z -=
          delta * 0.45;
      }

      if (
        pulseRef.current
      ) {
        const pulse =
          1 +
          Math.sin(
            clock.elapsedTime * 5
          ) *
            0.12;

        pulseRef.current.scale.set(
          pulse,
          pulse,
          pulse
        );
      }
    }
  );

  const targetColor =
    motion === "APPROACHING"
      ? "#ffb454"
      : motion === "RECEDING"
        ? "#7aa7ff"
        : "#65f7d1";

  return (
    <>

      <ambientLight
        intensity={0.5}
      />

      {/* Main range rings */}

      {[0.75, 1.5, 2.25, 3].map(
        (radius) => (
          <mesh key={radius}>
            <ringGeometry
              args={[
                radius - 0.008,
                radius,
                128,
              ]}
            />

            <meshBasicMaterial
              color="#4de8ff"
              transparent
              opacity={
                radius === 3
                  ? 0.26
                  : 0.13
              }
              side={
                THREE.DoubleSide
              }
            />
          </mesh>
        )
      )}

      {/* Crosshair */}

      <mesh>
        <planeGeometry
          args={[0.012, 6]}
        />

        <meshBasicMaterial
          color="#4de8ff"
          transparent
          opacity={0.09}
        />
      </mesh>

      <mesh>
        <planeGeometry
          args={[6, 0.012]}
        />

        <meshBasicMaterial
          color="#4de8ff"
          transparent
          opacity={0.09}
        />
      </mesh>

      {/* Diagonal HUD guides */}

      <mesh
        rotation={[
          0,
          0,
          Math.PI / 4,
        ]}
      >
        <planeGeometry
          args={[0.008, 6]}
        />

        <meshBasicMaterial
          color="#4de8ff"
          transparent
          opacity={0.035}
        />
      </mesh>

      <mesh
        rotation={[
          0,
          0,
          -Math.PI / 4,
        ]}
      >
        <planeGeometry
          args={[0.008, 6]}
        />

        <meshBasicMaterial
          color="#4de8ff"
          transparent
          opacity={0.035}
        />
      </mesh>

      {/* Sweep */}

      <group ref={sweepRef}>

        <mesh
          position={[
            0,
            1.5,
            0.01,
          ]}
        >
          <planeGeometry
            args={[0.025, 3]}
          />

          <meshBasicMaterial
            color="#4de8ff"
            transparent
            opacity={0.62}
          />
        </mesh>

        <mesh
          position={[
            -0.1,
            1.4,
            -0.01,
          ]}
          rotation={[
            0,
            0,
            0.07,
          ]}
        >
          <planeGeometry
            args={[0.15, 2.8]}
          />

          <meshBasicMaterial
            color="#4de8ff"
            transparent
            opacity={0.035}
          />
        </mesh>

      </group>

      {/* Trail */}

      {trail.map(
        (point, index) => (
          <mesh
            key={
              `${index}-${point.y}`
            }
            position={[
              0,
              point.y,
              0.025,
            ]}
          >
            <circleGeometry
              args={[
                0.05,
                24,
              ]}
            />

            <meshBasicMaterial
              color={targetColor}
              transparent
              opacity={
                point.opacity
              }
            />
          </mesh>
        )
      )}

      {/* Target */}

      {targetY !== null && (
        <group
          position={[
            0,
            targetY,
            0.08,
          ]}
        >

          <mesh
            ref={pulseRef}
          >
            <ringGeometry
              args={[
                0.13,
                0.16,
                48,
              ]}
            />

            <meshBasicMaterial
              color={targetColor}
              transparent
              opacity={0.7}
              side={
                THREE.DoubleSide
              }
            />
          </mesh>

          <mesh>
            <circleGeometry
              args={[
                0.055,
                32,
              ]}
            />

            <meshBasicMaterial
              color="#ffffff"
            />
          </mesh>

        </group>
      )}

      {/* Sensor origin */}

      <group
        position={[
          0,
          -2.82,
          0.1,
        ]}
      >

        <mesh>
          <circleGeometry
            args={[0.1, 32]}
          />

          <meshBasicMaterial
            color="#4de8ff"
          />
        </mesh>

        <mesh>
          <ringGeometry
            args={[
              0.15,
              0.17,
              48,
            ]}
          />

          <meshBasicMaterial
            color="#4de8ff"
            transparent
            opacity={0.5}
          />
        </mesh>

      </group>

    </>
  );
}

export default function Radar(
  props: RadarProps
) {
  return (
    <div className="radar-canvas">
      <Canvas
        orthographic
        dpr={[1, 2]}
        camera={{
          position: [
            0,
            0,
            10,
          ],
          zoom: 82,
        }}
      >
        <RadarScene
          {...props}
        />
      </Canvas>

      <div className="radar-overlay">

        <span className="range-label range-50">
          50
        </span>

        <span className="range-label range-100">
          100
        </span>

        <span className="range-label range-150">
          150
        </span>

        <span className="range-label range-200">
          200 CM
        </span>

      </div>
    </div>
  );
}