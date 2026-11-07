import { ANGLE_LIMIT } from '../../types/catalog.generated';
import { GATE_NAMES, gateSpec, parseAngle } from '../../services/circuit';
import type { CircuitGateName } from '../../types/api';
import { PARAMETER_LABELS, parameterNames, type ParameterText } from './gateParameters';

export function ParameterFields({ name, text, onChange, idPrefix }: {
  name: CircuitGateName;
  text: ParameterText;
  onChange: (text: ParameterText) => void;
  idPrefix: string;
}) {
  const names = parameterNames(name);
  if (!names.length) return null;
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {names.map((key) => {
        const parsed = parseAngle(text[key]);
        const id = `${idPrefix}-${key}`;
        return (
          <div key={key} className="text-sm">
            <label htmlFor={id}>{PARAMETER_LABELS[key]}</label>
            <input id={id} className="input mt-2 font-mono" value={text[key]} aria-describedby={`${id}-hint`}
              aria-invalid={parsed === null || Math.abs(parsed) > ANGLE_LIMIT}
              onChange={(event) => onChange({ ...text, [key]: event.target.value })} />
            <span id={`${id}-hint`} className="mt-1 block text-xs text-slate-400">
              {parsed === null ? 'Try 1.047, pi/3, or -3π/4' : `${parsed.toFixed(4)} rad`}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default function GatePalette({ active, onSelect, qubits, allowed }: {
  active: CircuitGateName;
  onSelect: (name: CircuitGateName) => void;
  qubits: number;
  allowed?: CircuitGateName[];
}) {
  return (
    <div role="radiogroup" aria-label="Gate palette" className="flex flex-wrap gap-2">
      {GATE_NAMES.filter((name) => gateSpec(name).qubits <= qubits && (!allowed || allowed.includes(name))).map((name) => {
        const spec = gateSpec(name);
        return (
          <button key={name} type="button" role="radio" aria-checked={active === name} title={spec.label}
            onClick={() => onSelect(name)}
            className={`min-w-14 rounded-lg border px-3 py-2 text-sm font-semibold transition ${active === name
              ? 'border-cyan-400 bg-cyan-400/15 text-cyan-100' : 'border-white/10 bg-white/5 text-slate-200 hover:bg-white/10'}`}>
            {name}
            <span className="sr-only">: {spec.label}</span>
          </button>
        );
      })}
    </div>
  );
}
