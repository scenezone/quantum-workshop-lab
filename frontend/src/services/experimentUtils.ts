import type { ExperimentId } from '../types/api';
import { EXPERIMENT_IDS } from '../types/api';

export function isExperimentId(value: string | null): value is ExperimentId {
  return value !== null && (EXPERIMENT_IDS as readonly string[]).includes(value);
}

export function createSubmissionKey(): string {
  const bytes = new Uint8Array(32);
  globalThis.crypto.getRandomValues(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
}
