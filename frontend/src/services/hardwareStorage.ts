import { useSyncExternalStore } from 'react';
import type { ExperimentId } from '../types/api';
import { isExperimentId } from './experimentUtils';

export interface HardwareSubmission {
  idempotencyKey: string;
  shots: number;
  trackingId: string | null;
}
type Submissions = Partial<Record<ExperimentId, HardwareSubmission>>;
const KEY = 'quantum-workshop-hardware-v1';
const listeners = new Set<() => void>();

function read(): Submissions {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(KEY) || '{}');
    if (!value || typeof value !== 'object') return {};
    return Object.fromEntries(Object.entries(value).filter(([id, entry]) =>
      isExperimentId(id) &&
      entry && typeof entry.idempotencyKey === 'string' && Number.isInteger(entry.shots) &&
      (entry.trackingId === null || typeof entry.trackingId === 'string'),
    ));
  } catch {
    return {};
  }
}
let snapshot = read();
window.addEventListener('storage', (event) => {
  if (event.key === KEY) {
    snapshot = read();
    listeners.forEach((listener) => listener());
  }
});

export function saveSubmission(id: ExperimentId, submission?: HardwareSubmission) {
  snapshot = { ...snapshot, [id]: submission };
  try { localStorage.setItem(KEY, JSON.stringify(snapshot)); } catch { /* Memory still works if storage is blocked. */ }
  listeners.forEach((listener) => listener());
}

export function useHardwareSubmissions() {
  return useSyncExternalStore((listener) => {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  }, () => snapshot);
}
