import type { CustomCircuitGate } from '../types/api';

const STORAGE_KEY = 'quantum-workshop-circuit-library-v1';

export interface SavedCircuit {
  id: string;
  name: string;
  qubits: number;
  gates: CustomCircuitGate[];
  shots: number;
  noise_profile: 'ideal' | 'low' | 'medium' | 'high';
}

const allowedGates = new Set(['H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ', 'CX', 'CZ', 'SWAP']);
const allowedNoise = new Set(['ideal', 'low', 'medium', 'high']);
const rotatingGates = new Set(['RX', 'RY', 'RZ']);
const twoQubitGates = new Set(['CX', 'CZ', 'SWAP']);

function isSavedCircuit(value: unknown): value is SavedCircuit {
  if (!value || typeof value !== 'object') return false;
  const item = value as Record<string, unknown>;
  if (typeof item.id !== 'string' || typeof item.name !== 'string' || item.name.length > 40
    || !Number.isInteger(item.qubits) || Number(item.qubits) < 1 || Number(item.qubits) > 3
    || !Number.isInteger(item.shots) || Number(item.shots) < 1 || Number(item.shots) > 10000
    || !allowedNoise.has(String(item.noise_profile)) || !Array.isArray(item.gates) || item.gates.length > 30) {
    return false;
  }
  return item.gates.every((candidate) => {
    if (!candidate || typeof candidate !== 'object') return false;
    const gate = candidate as Record<string, unknown>;
    const qubits = gate.qubits;
    const name = typeof gate.name === 'string' ? gate.name : '';
    return typeof gate.name === 'string' && allowedGates.has(gate.name)
      && Array.isArray(qubits) && qubits.length === (twoQubitGates.has(name) ? 2 : 1)
      && new Set(qubits).size === qubits.length
      && qubits.every((qubit) => Number.isInteger(qubit) && Number(qubit) >= 0 && Number(qubit) < Number(item.qubits))
      && (rotatingGates.has(name)
        ? typeof gate.angle === 'number' && Number.isFinite(gate.angle)
          && gate.angle >= -Math.PI * 2 && gate.angle <= Math.PI * 2
        : gate.angle === undefined);
  });
}

export function getSavedCircuits(): SavedCircuit[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    return Array.isArray(value) ? value.filter(isSavedCircuit) : [];
  } catch {
    return [];
  }
}

export function saveCircuit(circuit: SavedCircuit): SavedCircuit[] {
  const circuits = getSavedCircuits().filter((item) => item.id !== circuit.id);
  const next = [circuit, ...circuits].slice(0, 20);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // The current editor remains usable when storage is full or unavailable.
  }
  return next;
}

export function deleteSavedCircuit(id: string): SavedCircuit[] {
  const next = getSavedCircuits().filter((item) => item.id !== id);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // The editor can still continue without persistence.
  }
  return next;
}
