interface CircuitDiagramProps {
  experimentId: 'superposition' | 'bell_entanglement' | 'interference';
}

const circuits = {
  superposition: {
    qubits: 1,
    gates: [
      { qubit: 0, x: 120, label: 'H', color: 'text-cyan-300' },
      { qubit: 0, x: 260, label: 'M', color: 'text-purple-300' },
    ],
  },
  bell_entanglement: {
    qubits: 2,
    gates: [
      { qubit: 0, x: 120, label: 'H', color: 'text-cyan-300' },
      { qubit: 0, x: 220, label: '●', color: 'text-purple-300' },
      { qubit: 1, x: 220, label: '⊕', color: 'text-purple-300' },
      { qubit: 0, x: 330, label: 'M', color: 'text-purple-300' },
      { qubit: 1, x: 330, label: 'M', color: 'text-purple-300' },
    ],
  },
  interference: {
    qubits: 1,
    gates: [
      { qubit: 0, x: 100, label: 'H', color: 'text-cyan-300' },
      { qubit: 0, x: 200, label: 'H', color: 'text-cyan-300' },
      { qubit: 0, x: 300, label: 'M', color: 'text-purple-300' },
    ],
  },
};

export default function CircuitDiagram({ experimentId }: CircuitDiagramProps) {
  const circuit = circuits[experimentId];

  return (
    <div className="glass p-4">
      <svg viewBox="0 0 420 {circuit.qubits * 80 + 60}" className="w-full" role="img" aria-label="Quantum circuit diagram">
        {Array.from({ length: circuit.qubits }).map((_, qubit) => (
          <g key={qubit}>
            <text x={20} y={55 + qubit * 80} className="fill-slate-300 text-sm">
              q[{qubit}]
            </text>
            <line
              x1={60}
              y1={50 + qubit * 80}
              x2={390}
              y2={50 + qubit * 80}
              stroke="rgba(148,163,184,0.5)"
              strokeWidth={2}
            />
          </g>
        ))}

        {circuit.gates.map((gate, index) => (
          <g key={index}>
            <rect
              x={gate.x - 22}
              y={28 + gate.qubit * 80}
              width={44}
              height={44}
              rx={10}
              className="fill-navy-800 stroke-white/20"
            />
            <text
              x={gate.x}
              y={56 + gate.qubit * 80}
              textAnchor="middle"
              className={`${gate.color} text-lg font-semibold`}
            >
              {gate.label}
            </text>
          </g>
        ))}

        {experimentId === 'bell_entanglement' && (
          <line x1={220} y1={50} x2={220} y2={130} stroke="#a855f7" strokeWidth={2} />
        )}
      </svg>
    </div>
  );
}