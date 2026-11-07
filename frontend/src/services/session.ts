import { useSyncExternalStore } from 'react';
import axios from 'axios';
import { syncSessionProgress } from './api';
import { getLearningProgress, practiceSummary, subscribeProgress } from './learningProgress';

const KEY = 'quantum-workshop-session-v1';

export interface SessionMembershipRecord {
  code: string;
  name: string;
  nickname: string;
  participantId: string;
  participantToken: string;
  expiresAt: string;
}

export type SyncState = 'idle' | 'syncing' | 'synced' | 'error' | 'ended';

function read(): SessionMembershipRecord | null {
  try {
    const value = JSON.parse(localStorage.getItem(KEY) || 'null') as SessionMembershipRecord | null;
    if (!value || typeof value.code !== 'string' || typeof value.participantToken !== 'string') return null;
    return Date.parse(value.expiresAt) > Date.now() ? value : null;
  } catch {
    return null;
  }
}

let membership = read();
let syncState: SyncState = 'idle';
let snapshot: { membership: SessionMembershipRecord | null; syncState: SyncState } = { membership, syncState };
const listeners = new Set<() => void>();
let timer: ReturnType<typeof setTimeout> | undefined;

function emit() {
  snapshot = { membership, syncState };
  listeners.forEach((listener) => listener());
}

export function getSessionMembership() {
  return snapshot;
}

export function useSessionMembership() {
  return useSyncExternalStore((listener) => {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  }, getSessionMembership);
}

export function setSessionMembership(record: SessionMembershipRecord | null) {
  membership = record;
  syncState = 'idle';
  try {
    if (record) localStorage.setItem(KEY, JSON.stringify(record));
    else localStorage.removeItem(KEY);
  } catch {
    // The session still works for this page when storage is unavailable.
  }
  emit();
  if (record) void syncNow();
}

export async function syncNow() {
  const current = membership;
  if (!current) return;
  const progress = getLearningProgress();
  const summary = practiceSummary(progress);
  syncState = 'syncing';
  emit();
  try {
    await syncSessionProgress(current.code, {
      participant_id: current.participantId,
      participant_token: current.participantToken,
      completed_lessons: progress.completedLessons,
      completed_challenges: progress.completedChallenges,
      practice_correct: summary.correct,
      practice_attempted: summary.attempted,
    });
    syncState = 'synced';
  } catch (cause) {
    const status = axios.isAxiosError(cause) ? cause.response?.status : undefined;
    syncState = status === 404 || status === 401 ? 'ended' : 'error';
  }
  emit();
}

/** Sends progress to the facilitator shortly after it changes. Returns a cleanup function. */
export function startSessionSync(): () => void {
  const unsubscribe = subscribeProgress(() => {
    if (!membership) return;
    clearTimeout(timer);
    timer = setTimeout(() => void syncNow(), 1500);
  });
  if (membership) void syncNow();
  return () => {
    clearTimeout(timer);
    unsubscribe();
  };
}
