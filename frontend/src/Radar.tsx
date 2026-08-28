import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";

function CognitionCore({ online }: { online: boolean }) {
  const core = useRef<THREE.Group>(null);
  const orbitA = useRef<THREE.Group>(null);
  const orbitB = useRef<THREE.Group>(null);
  const pulse = useRef<THREE.Mesh>(null);
  const color = online ? "#65f7d1" : "#ff6b7a";

  useFrame(({ clock }, delta) => {
    const elapsed = clock.elapsedTime;
    if (core.current) {
      core.current.rotation.y += delta * 0.22;
      core.current.rotation.x = Math.sin(elapsed * 0.35) * 0.18;
    }
    if (orbitA.current) orbitA.current.rotation.z += delta * 0.17;
    if (orbitB.current) orbitB.current.rotation.x -= delta * 0.12;
    if (pulse.current) {
      const scale = 1 + Math.sin(elapsed * 1.8) * 0.055;
      pulse.current.scale.setScalar(scale);
    }
  });

  return <>
    <color attach="background" args={["#020910"]} />
    <fog attach="fog" args={["#020910", 7, 13]} />
    <ambientLight intensity={0.18} />
    <pointLight position={[2, 3, 4]} color={color} intensity={7} distance={12} />
    <gridHelper args={[14, 28, "#123e49", "#081d25"]} position={[0, -2.3, 0]} />

    <group ref={core}>
      <mesh ref={pulse}>
        <icosahedronGeometry args={[1.22, 2]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.65} roughness={0.22} metalness={0.78} wireframe />
      </mesh>
      <mesh><icosahedronGeometry args={[0.72, 2]} /><meshStandardMaterial color="#07171d" emissive={color} emissiveIntensity={1.6} roughness={0.18} metalness={0.85} /></mesh>
      <mesh><octahedronGeometry args={[0.34, 0]} /><meshBasicMaterial color="#e9ffff" /></mesh>
    </group>

    <group ref={orbitA} rotation={[Math.PI / 2.6, 0.2, 0]}>
      <mesh><torusGeometry args={[1.75, 0.012, 8, 160]} /><meshBasicMaterial color="#57e5ff" transparent opacity={0.7} /></mesh>
      {[0, 1, 2].map(index => <mesh key={index} position={[Math.cos(index * Math.PI * 2 / 3) * 1.75, Math.sin(index * Math.PI * 2 / 3) * 1.75, 0]}>
        <boxGeometry args={[0.12, 0.12, 0.12]} /><meshBasicMaterial color="#7aa7ff" />
      </mesh>)}
    </group>

    <group ref={orbitB} rotation={[0.3, Math.PI / 2, 0.5]}>
      <mesh><torusGeometry args={[2.25, 0.008, 8, 180, Math.PI * 1.55]} /><meshBasicMaterial color="#7aa7ff" transparent opacity={0.38} /></mesh>
    </group>

    {[2.7, 3.05, 3.4].map((radius, index) => <mesh key={radius} rotation={[Math.PI / 2, index * 0.34, 0]}>
      <torusGeometry args={[radius, 0.006, 6, 180, Math.PI * (1.15 + index * 0.18)]} />
      <meshBasicMaterial color="#24697a" transparent opacity={0.25 - index * 0.04} />
    </mesh>)}
  </>;
}

export default function Radar({ online }: { online: boolean }) {
  return <div className="digital-twin cognition-visual">
    <Canvas camera={{ position: [4.7, 3.2, 6.4], fov: 42 }} dpr={1} gl={{ antialias: true, powerPreference: "high-performance" }}>
      <CognitionCore online={online} />
    </Canvas>
    <div className="twin-readout cognition-readout">
      <span>CYPHER COGNITION MATRIX</span>
      <strong>{online ? "CORE SYNCHRONIZED" : "CORE DISCONNECTED"}</strong>
      <em>LOCAL // GUARDED // PERSISTENT</em>
    </div>
  </div>;
}
