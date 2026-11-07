import { isValidCircuitDraft, type CircuitDraft } from './circuit';

const STORAGE_KEY = 'quantum-workshop-circuit-library-v1';

export interface SavedCircuit extends CircuitDraft {
  id: string;
  name: string;
}

function isSavedCircuit(value: unknown): value is SavedCircuit {
  if (!value || typeof value !== 'object') return false;
  const item = value as Record<string, unknown>;
  return typeof item.id === 'string' && typeof item.name === 'string' && item.name.length <= 40
    && isValidCircuitDraft(item);
}

export function getSavedCircuits(): SavedCircuit[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    return Array.isArray(value) ? value.filter(isSavedCircuit) : [];
  } catch {
    return [];
  }
}

function store(circuits: SavedCircuit[]): SavedCircuit[] {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(circuits));
  } catch {
    // The editor remains usable when storage is full or unavailable.
  }
  return circuits;
}

export function saveCircuit(circuit: SavedCircuit): SavedCircuit[] {
  return store([circuit, ...getSavedCircuits().filter((item) => item.id !== circuit.id)].slice(0, 20));
}

export function deleteSavedCircuit(id: string): SavedCircuit[] {
  return store(getSavedCircuits().filter((item) => item.id !== id));
}
