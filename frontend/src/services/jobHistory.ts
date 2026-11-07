import { useSyncExternalStore } from 'react';
import type { ExperimentId } from '../types/api';
import { isExperimentId } from './experimentUtils';

const KEY = 'quantum-workshop-hardware-history-v1';
const LIMIT = 25;

export interface HardwareHistoryEntry {
  trackingId: string;
  experimentId: ExperimentId;
  shots: number;
  submittedAt: string;
}

const listeners = new Set<() => void>();

function read(): HardwareHistoryEntry[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(KEY) || '[]');
    if (!Array.isArray(value)) return [];
    return value.filter((entry): entry is HardwareHistoryEntry => Boolean(entry)
      && typeof entry.trackingId === 'string' && isExperimentId(entry.experimentId)
      && Number.isInteger(entry.shots) && typeof entry.submittedAt === 'string').slice(0, LIMIT);
  } catch {
    return [];
  }
}

let snapshot = read();

function write(entries: HardwareHistoryEntry[]) {
  snapshot = entries.slice(0, LIMIT);
  try {
    localStorage.setItem(KEY, JSON.stringify(snapshot));
  } catch {
    // History remains available for this page when storage is unavailable.
  }
  listeners.forEach((listener) => listener());
}

export function addHardwareHistory(entry: HardwareHistoryEntry) {
  write([entry, ...snapshot.filter((item) => item.trackingId !== entry.trackingId)]);
}

export function removeHardwareHistory(trackingId: string) {
  write(snapshot.filter((item) => item.trackingId !== trackingId));
}

export function useHardwareHistory() {
  return useSyncExternalStore((listener) => {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  }, () => snapshot);
}
