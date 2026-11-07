import { useSyncExternalStore } from 'react';

const STORAGE_KEY = 'quantum-workshop-progress-v1';
const EXPORT_FORMAT = 'quantum-workshop-progress';

export interface PracticeRecord {
  attempts: number;
  correct: boolean;
  firstTryCorrect: boolean;
}

export interface LearningProgress {
  completedLessons: string[];
  completedChallenges: string[];
  /** Multiple-choice results keyed by question ID. */
  practice: Record<string, PracticeRecord>;
  /** Written questions the learner answered before viewing the sample. */
  writtenAnswered: string[];
}

const emptyProgress: LearningProgress = { completedLessons: [], completedChallenges: [], practice: {}, writtenAnswered: [] };
const listeners = new Set<() => void>();

function strings(value: unknown): string[] {
  return Array.isArray(value) ? [...new Set(value.filter((item): item is string => typeof item === 'string' && item.length <= 100))] : [];
}

function normalize(value: unknown): LearningProgress {
  if (!value || typeof value !== 'object') return emptyProgress;
  const record = value as Record<string, unknown>;
  const practice: Record<string, PracticeRecord> = {};
  if (record.practice && typeof record.practice === 'object') {
    for (const [id, entry] of Object.entries(record.practice as Record<string, unknown>)) {
      if (!entry || typeof entry !== 'object' || id.length > 100) continue;
      const item = entry as Record<string, unknown>;
      if (Number.isInteger(item.attempts) && Number(item.attempts) > 0) {
        practice[id] = {
          attempts: Number(item.attempts),
          correct: item.correct === true,
          firstTryCorrect: item.firstTryCorrect === true,
        };
      }
    }
  }
  return {
    completedLessons: strings(record.completedLessons),
    completedChallenges: strings(record.completedChallenges),
    practice,
    writtenAnswered: strings(record.writtenAnswered),
  };
}

function read(): LearningProgress {
  try {
    return normalize(JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null'));
  } catch {
    return emptyProgress;
  }
}

let snapshot = read();
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key === STORAGE_KEY) {
      snapshot = read();
      listeners.forEach((listener) => listener());
    }
  });
}

export function getLearningProgress(): LearningProgress {
  return snapshot;
}

function saveProgress(progress: LearningProgress): LearningProgress {
  snapshot = progress;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch {
    // Progress remains usable for the current page even when storage is unavailable.
  }
  listeners.forEach((listener) => listener());
  return progress;
}

export function subscribeProgress(listener: () => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

export function useLearningProgress(): LearningProgress {
  return useSyncExternalStore(subscribeProgress, getLearningProgress);
}

export function completeLesson(lessonId: string): LearningProgress {
  return saveProgress({ ...snapshot, completedLessons: [...new Set([...snapshot.completedLessons, lessonId])] });
}

export function uncompleteLesson(lessonId: string): LearningProgress {
  return saveProgress({ ...snapshot, completedLessons: snapshot.completedLessons.filter((id) => id !== lessonId) });
}

export function completeChallenge(challengeId: string): LearningProgress {
  return saveProgress({
    ...snapshot,
    completedChallenges: [...new Set([...snapshot.completedChallenges, challengeId])],
  });
}

export function recordPracticeAttempt(questionId: string, correct: boolean): LearningProgress {
  const previous = snapshot.practice[questionId];
  return saveProgress({
    ...snapshot,
    practice: {
      ...snapshot.practice,
      [questionId]: {
        attempts: (previous?.attempts ?? 0) + 1,
        correct: previous?.correct || correct,
        firstTryCorrect: previous ? previous.firstTryCorrect : correct,
      },
    },
  });
}

export function recordWrittenAnswer(questionId: string): LearningProgress {
  if (snapshot.writtenAnswered.includes(questionId)) return snapshot;
  return saveProgress({ ...snapshot, writtenAnswered: [...snapshot.writtenAnswered, questionId] });
}

export function practiceSummary(progress: LearningProgress) {
  const records = Object.values(progress.practice);
  return {
    attempted: records.length,
    correct: records.filter((record) => record.correct).length,
    firstTryCorrect: records.filter((record) => record.firstTryCorrect).length,
    written: progress.writtenAnswered.length,
  };
}

export function exportProgress(progress = snapshot): string {
  return JSON.stringify({ format: EXPORT_FORMAT, version: 1, exported_at: new Date().toISOString(), progress }, null, 2);
}

/** Imports an exported file. Merging keeps the best result from both copies. */
export function importProgress(text: string, mode: 'merge' | 'replace' = 'merge'): LearningProgress {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error('This file is not valid JSON.');
  }
  const file = parsed as Record<string, unknown> | null;
  if (!file || file.format !== EXPORT_FORMAT || file.version !== 1) {
    throw new Error('This file is not a Quantum Workshop Lab progress export.');
  }
  const incoming = normalize(file.progress);
  if (mode === 'replace') return saveProgress(incoming);
  const practice = { ...snapshot.practice };
  for (const [id, record] of Object.entries(incoming.practice)) {
    const current = practice[id];
    practice[id] = current ? {
      attempts: Math.max(current.attempts, record.attempts),
      correct: current.correct || record.correct,
      firstTryCorrect: current.firstTryCorrect || record.firstTryCorrect,
    } : record;
  }
  return saveProgress({
    completedLessons: [...new Set([...snapshot.completedLessons, ...incoming.completedLessons])],
    completedChallenges: [...new Set([...snapshot.completedChallenges, ...incoming.completedChallenges])],
    practice,
    writtenAnswered: [...new Set([...snapshot.writtenAnswered, ...incoming.writtenAnswered])],
  });
}

export function resetProgress(): LearningProgress {
  return saveProgress(emptyProgress);
}
