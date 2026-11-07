import type { KeyboardEvent } from 'react';

export interface CanvasGate {
  name: string;
  qubits: number[];
  label?: string;
  classical_bits?: number[];
  explanation?: string;
}

interface Props {
  qubits: number;
  gates: CanvasGate[];
  ariaLabel?: string;
  /** Interactive editing: click a gate to select it, or a "+" slot to place a gate. */
  selectedIndex?: number | null;
  onSelectGate?: (index: number) => void;
  onAddSlot?: (qubit: number) => void;
  /** Operands already chosen for a multi-qubit gate that is being placed. */
  pendingQubits?: number[];
  /** Shown after the last gate when measurement is not in the Z basis. */
  measurementBases?: string[];
}

const CONTROLLED = new Set(['CX', 'CP', 'CCX']);
const CONNECTED = new Set(['CX', 'CZ', 'CP', 'CCX', 'SWAP']);

function activate(handler: () => void) {
  return (event: KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handler();
    }
  };
}

export default function CircuitCanvas({
  qubits, gates, ariaLabel = 'Quantum circuit diagram', selectedIndex = null,
  onSelectGate, onAddSlot, pendingQubits = [], measurementBases,
}: Props) {
  const interactive = Boolean(onAddSlot || onSelectGate);
  const showBases = measurementBases?.some((basis) => basis !== 'Z');
  const extraColumns = (interactive ? 1 : 0) + (showBases ? 1 : 0);
  const width = Math.max(420, 150 + (gates.length + extraColumns) * 80);
  const height = 80 + qubits * 80;
  const y = (qubit: number) => 50 + qubit * 80;
  const x = (index: number) => 105 + index * 80;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="min-w-full"
      role={interactive ? 'group' : 'img'} aria-label={ariaLabel}>
      {Array.from({ length: qubits }, (_, qubit) => (
        <g key={qubit}>
          <text x={10} y={y(qubit) + 5} fill="#cbd5e1" fontSize={13}>q[{qubit}]</text>
          <line x1={65} y1={y(qubit)} x2={width - 20} y2={y(qubit)} stroke="#64748b" strokeWidth={2} />
        </g>
      ))}
      {gates.map((gate, index) => {
        const cx = x(index);
        const controls = CONTROLLED.has(gate.name) ? gate.qubits.slice(0, -1) : [];
        const target = gate.qubits[gate.qubits.length - 1];
        const selected = selectedIndex === index;
        const operands = gate.qubits.map((qubit) => `q${qubit}`).join(', ');
        const select = onSelectGate ? () => onSelectGate(index) : undefined;
        return (
          <g key={index} {...(select ? {
            role: 'button', tabIndex: 0, onClick: select, onKeyDown: activate(select),
            'aria-label': `Gate ${index + 1}: ${gate.label ?? gate.name} on ${operands}`,
            'aria-pressed': selected, className: 'cursor-pointer focus:outline-none',
          } : {})}>
            <title>{gate.explanation ? `Step ${index + 1}: ${gate.explanation}` : `Step ${index + 1}: ${gate.label ?? gate.name} on ${operands}`}</title>
            {selected && <rect x={cx - 36} y={y(Math.min(...gate.qubits)) - 31} width={72}
              height={y(Math.max(...gate.qubits)) - y(Math.min(...gate.qubits)) + 62} rx={10}
              fill="rgba(34,211,238,.08)" stroke="#22d3ee" strokeDasharray="4 3" />}
            {CONNECTED.has(gate.name) && <line x1={cx} y1={y(Math.min(...gate.qubits))} x2={cx}
              y2={y(Math.max(...gate.qubits))} stroke="#c084fc" strokeWidth={2} />}
            {gate.qubits.map((qubit, bit) => {
              const dot = controls.includes(qubit) || gate.name === 'CZ' || (gate.name === 'CP' && qubit !== target);
              if (dot) return <circle key={qubit} cx={cx} cy={y(qubit)} r={6} fill="#c084fc" />;
              if (gate.name === 'SWAP') {
                return <text key={qubit} x={cx} y={y(qubit) + 7} textAnchor="middle" fill="#c084fc" fontSize={26}>x</text>;
              }
              const label = ['CX', 'CCX'].includes(gate.name) && qubit === target ? '+'
                : gate.name === 'Measure' ? 'M' : gate.label ?? gate.name;
              const fontSize = label.length > 7 ? 9 : label.length > 4 ? 11 : 17;
              return <g key={qubit}>
                <rect x={cx - 29} y={y(qubit) - 23} width={58} height={46} rx={8} fill="#111a33"
                  stroke={selected ? '#22d3ee' : '#64748b'} />
                <text x={cx} y={y(qubit) + 5} textAnchor="middle" className="fill-current text-cyan-300"
                  fontSize={fontSize}>{label}</text>
                {gate.name === 'Measure' && <text x={cx} y={y(qubit) + 40} textAnchor="middle" fill="#cbd5e1" fontSize={11}>
                  c[{gate.classical_bits?.[bit] ?? qubit}]
                </text>}
              </g>;
            })}
          </g>
        );
      })}
      {showBases && measurementBases!.map((basis, qubit) => (
        <g key={`basis-${qubit}`} aria-hidden="true">
          <rect x={x(gates.length) - 29} y={y(qubit) - 23} width={58} height={46} rx={8} fill="#1e1336" stroke="#a855f7" />
          <text x={x(gates.length)} y={y(qubit) + 5} textAnchor="middle" fill="#e9d5ff" fontSize={12}>M{basis}</text>
        </g>
      ))}
      {onAddSlot && Array.from({ length: qubits }, (_, qubit) => {
        const slotX = x(gates.length + (showBases ? 1 : 0));
        const order = pendingQubits.indexOf(qubit);
        const add = () => onAddSlot(qubit);
        return (
          <g key={`slot-${qubit}`} role="button" tabIndex={0} onClick={add} onKeyDown={activate(add)}
            aria-label={order >= 0 ? `q${qubit} selected as operand ${order + 1}` : `Place gate on q${qubit}`}
            className="cursor-pointer focus:outline-none">
            <circle cx={slotX} cy={y(qubit)} r={16} fill={order >= 0 ? 'rgba(168,85,247,.25)' : '#0b1328'}
              stroke={order >= 0 ? '#a855f7' : '#22d3ee'} strokeDasharray={order >= 0 ? undefined : '4 3'} />
            <text x={slotX} y={y(qubit) + 6} textAnchor="middle" fill={order >= 0 ? '#f5d0fe' : '#67e8f9'} fontSize={order >= 0 ? 13 : 18}>
              {order >= 0 ? order + 1 : '+'}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
