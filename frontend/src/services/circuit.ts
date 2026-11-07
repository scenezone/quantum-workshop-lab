import {
  ANGLE_LIMIT,
  CUSTOM_GATES,
  MAX_CUSTOM_GATES,
  MAX_CUSTOM_QUBITS,
  MEASUREMENT_BASES,
  NOISE_PROFILES,
} from '../types/catalog.generated';
import type {
  CircuitGateName,
  CustomCircuitGate,
  MeasurementBasis,
  NoiseProfile,
} from '../types/api';

export const GATE_NAMES = Object.keys(CUSTOM_GATES) as CircuitGateName[];
export const NOISE_PROFILE_IDS = NOISE_PROFILES.map((profile) => profile.id) as NoiseProfile[];
export const PARAMETER_NAMES = ['angle', 'phi', 'lam'] as const;

export function gateSpec(name: CircuitGateName) {
  return CUSTOM_GATES[name];
}

export function isGateName(value: unknown): value is CircuitGateName {
  return typeof value === 'string' && value in CUSTOM_GATES;
}

export function isNoiseProfile(value: unknown): value is NoiseProfile {
  return typeof value === 'string' && (NOISE_PROFILE_IDS as string[]).includes(value);
}

export function isMeasurementBasis(value: unknown): value is MeasurementBasis {
  return typeof value === 'string' && (MEASUREMENT_BASES as readonly string[]).includes(value);
}

function validAngle(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && Math.abs(value) <= ANGLE_LIMIT;
}

/** Mirrors the backend CustomGate validator, so bad links fail early with a clear message. */
export function isValidGate(candidate: unknown, qubitCount: number): candidate is CustomCircuitGate {
  if (!candidate || typeof candidate !== 'object') return false;
  const gate = candidate as Record<string, unknown>;
  if (!isGateName(gate.name)) return false;
  const spec = CUSTOM_GATES[gate.name];
  const qubits = gate.qubits;
  if (!Array.isArray(qubits) || qubits.length !== spec.qubits || new Set(qubits).size !== qubits.length
    || !qubits.every((qubit) => Number.isInteger(qubit) && qubit >= 0 && qubit < qubitCount)) {
    return false;
  }
  const expected = PARAMETER_NAMES.slice(0, spec.params === 3 ? 3 : spec.params);
  return PARAMETER_NAMES.every((name) => expected.includes(name)
    ? validAngle(gate[name])
    : gate[name] === undefined || gate[name] === null);
}

export interface CircuitDraft {
  qubits: number;
  gates: CustomCircuitGate[];
  shots: number;
  noise_profile: NoiseProfile;
  measurement_bases?: MeasurementBasis[];
}

export function isValidCircuitDraft(value: unknown, maxShots = 10000): value is CircuitDraft {
  if (!value || typeof value !== 'object') return false;
  const draft = value as Record<string, unknown>;
  const qubits = Number(draft.qubits);
  return Number.isInteger(draft.qubits) && qubits >= 1 && qubits <= MAX_CUSTOM_QUBITS
    && Array.isArray(draft.gates) && draft.gates.length <= MAX_CUSTOM_GATES
    && draft.gates.every((gate) => isValidGate(gate, qubits))
    && Number.isInteger(draft.shots) && Number(draft.shots) >= 1 && Number(draft.shots) <= maxShots
    && isNoiseProfile(draft.noise_profile)
    && (draft.measurement_bases === undefined || (Array.isArray(draft.measurement_bases)
      && draft.measurement_bases.length === qubits && draft.measurement_bases.every(isMeasurementBasis)));
}

/** Accepts numbers and simple π expressions such as "pi/2", "-3π/4", or "2*pi/3". */
export function parseAngle(input: string): number | null {
  const text = input.trim().toLowerCase().replace(/π/g, 'pi').replace(/\s+/g, '');
  if (!text) return null;
  if (/^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/.test(text)) return Number(text);
  const match = /^([-+])?(\d+\.?\d*|\.\d+)?\*?pi(?:\/(\d+\.?\d*))?$/.exec(text);
  if (!match) return null;
  const sign = match[1] === '-' ? -1 : 1;
  const multiplier = match[2] ? Number(match[2]) : 1;
  const divisor = match[3] ? Number(match[3]) : 1;
  if (!divisor) return null;
  return (sign * multiplier * Math.PI) / divisor;
}

/** Shows common multiples of π exactly, otherwise a rounded radian value. */
export function formatAngle(value: number): string {
  for (const divisor of [1, 2, 3, 4, 6, 8]) {
    const multiple = (value * divisor) / Math.PI;
    if (Math.abs(multiple - Math.round(multiple)) < 1e-9) {
      const count = Math.round(multiple);
      if (count === 0) return '0';
      const numerator = Math.abs(count) === 1 ? 'π' : `${Math.abs(count)}π`;
      return `${count < 0 ? '-' : ''}${numerator}${divisor === 1 ? '' : `/${divisor}`}`;
    }
  }
  return String(Number(value.toFixed(4)));
}

function params(gate: CustomCircuitGate): number[] {
  const spec = CUSTOM_GATES[gate.name];
  if (spec.params === 3) return [gate.angle ?? 0, gate.phi ?? 0, gate.lam ?? 0];
  if (spec.params === 1) return [gate.angle ?? 0];
  return [];
}

export function gateLabel(gate: CustomCircuitGate): string {
  const values = params(gate);
  return values.length ? `${gate.name}(${values.map(formatAngle).join(', ')})` : gate.name;
}

function basisRotation(basis: MeasurementBasis, qubit: number, style: 'qiskit' | 'qasm'): string[] {
  if (basis === 'X') return style === 'qiskit' ? [`qc.h(${qubit})`] : [`h q[${qubit}];`];
  if (basis === 'Y') {
    return style === 'qiskit' ? [`qc.sdg(${qubit})`, `qc.h(${qubit})`] : [`sdg q[${qubit}];`, `h q[${qubit}];`];
  }
  return [];
}

export function qiskitCode(qubits: number, gates: CustomCircuitGate[], bases?: MeasurementBasis[]): string {
  const lines = ['from qiskit import QuantumCircuit', `qc = QuantumCircuit(${qubits})`];
  for (const gate of gates) {
    const args = [...params(gate).map((value) => String(value)), ...gate.qubits.map(String)];
    lines.push(`qc.${CUSTOM_GATES[gate.name].params === 3 ? 'u' : gate.name.toLowerCase()}(${args.join(', ')})`);
  }
  const rotations = (bases ?? []).flatMap((basis, qubit) => basisRotation(basis, qubit, 'qiskit'));
  if (rotations.length) lines.push('# Rotate each qubit into its chosen measurement basis', ...rotations);
  lines.push('qc.measure_all()', 'print(qc.draw())');
  return lines.join('\n');
}

export function qasmCode(qubits: number, gates: CustomCircuitGate[], bases?: MeasurementBasis[]): string {
  const lines = ['OPENQASM 2.0;', 'include "qelib1.inc";', `qreg q[${qubits}];`, `creg c[${qubits}];`];
  for (const gate of gates) {
    const values = params(gate);
    const name = CUSTOM_GATES[gate.name].params === 3 ? 'u' : gate.name.toLowerCase();
    const call = values.length ? `${name}(${values.join(',')})` : name;
    lines.push(`${call} ${gate.qubits.map((qubit) => `q[${qubit}]`).join(',')};`);
  }
  lines.push(...(bases ?? []).flatMap((basis, qubit) => basisRotation(basis, qubit, 'qasm')));
  lines.push('measure q -> c;');
  return lines.join('\n');
}
