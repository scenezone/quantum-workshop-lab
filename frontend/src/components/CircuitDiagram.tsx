import type { Experiment } from '../types/api';

export default function CircuitDiagram({ experiment }: { experiment: Experiment }) {
  const width = Math.max(420, 150 + experiment.gates.length * 80);
  const height = 80 + experiment.qubits * 80;
  const y = (qubit: number) => 50 + qubit * 80;
  return (
    <section className="glass min-w-0 p-4" aria-label="Circuit and gate walkthrough">
      <h2 className="mb-3 font-semibold">Circuit: {experiment.title}</h2>
      <div className="max-w-full overflow-x-auto overscroll-x-contain" tabIndex={0} role="region" aria-label="Scrollable quantum circuit">
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}
          className="min-w-full" role="img" aria-label="Quantum circuit diagram">
          {Array.from({ length: experiment.qubits }, (_, qubit) => (
            <g key={qubit}>
              <text x={10} y={y(qubit) + 5} fill="#cbd5e1" fontSize={13}>q[{qubit}]</text>
              <line x1={65} y1={y(qubit)} x2={width - 20} y2={y(qubit)} stroke="#64748b" strokeWidth={2} />
            </g>
          ))}
          {experiment.gates.map((gate, index) => {
            const x = 105 + index * 80;
            const controls = ['CX', 'CP', 'CCX'].includes(gate.name) ? gate.qubits.slice(0, -1) : [];
            const target = gate.qubits[gate.qubits.length - 1];
            const connected = ['CX', 'CZ', 'CP', 'CCX', 'SWAP'].includes(gate.name);
            return (
              <g key={index}>
                <title>{`Step ${index + 1}: ${gate.explanation}`}</title>
                {connected && <line x1={x} y1={y(Math.min(...gate.qubits))} x2={x} y2={y(Math.max(...gate.qubits))}
                  stroke="#c084fc" strokeWidth={2} />}
                {gate.qubits.map((qubit, bit) => {
                  const dot = controls.includes(qubit) || gate.name === 'CZ';
                  if (dot) return <circle key={qubit} cx={x} cy={y(qubit)} r={6} fill="#c084fc" />;
                  if (gate.name === 'SWAP') return <text key={qubit} x={x} y={y(qubit) + 7}
                    textAnchor="middle" fill="#c084fc" fontSize={26}>x</text>;
                  const label = ['CX', 'CCX'].includes(gate.name) && qubit === target ? '+' : gate.name === 'Measure' ? 'M' : gate.label ?? gate.name;
                  return <g key={qubit}>
                    <rect x={x - 29} y={y(qubit) - 23} width={58} height={46} rx={8} fill="#111a33" stroke="#64748b" />
                    <text x={x} y={y(qubit) + 5} textAnchor="middle"
                      className="fill-current text-cyan-300" fontSize={label.length > 4 ? 11 : 17}>{label}</text>
                    {gate.name === 'Measure' && <text x={x} y={y(qubit) + 40} textAnchor="middle" fill="#cbd5e1" fontSize={11}>
                      c[{gate.classical_bits?.[bit] ?? qubit}]
                    </text>}
                  </g>;
                })}
              </g>
            );
          })}
        </svg>
      </div>
      <p className="mt-2 text-xs text-slate-400">
        Gates run left to right. Measurement labels identify the classical result bits. Scroll horizontally for longer circuits.
      </p>
      <details className="mt-4">
        <summary className="cursor-pointer text-sm text-cyan-300">Gate-by-gate walkthrough ({experiment.gates.length} steps)</summary>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-slate-300">
          {experiment.gates.map((gate, index) => <li key={index}>
            <strong>{gate.name} on {gate.qubits.map((qubit) => `q${qubit}`).join(', ')}:</strong> {gate.explanation}
          </li>)}
        </ol>
      </details>
    </section>
  );
}
