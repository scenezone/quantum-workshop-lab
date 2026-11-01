const STORAGE_KEY = 'quantum-workshop-progress-v1';

export interface LearningProgress {
  completedLessons: string[];
  completedChallenges: string[];
}

const emptyProgress: LearningProgress = { completedLessons: [], completedChallenges: [] };

export function getLearningProgress(): LearningProgress {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    if (!value || typeof value !== 'object') return emptyProgress;
    const record = value as Record<string, unknown>;
    return {
      completedLessons: Array.isArray(record.completedLessons)
        ? record.completedLessons.filter((item): item is string => typeof item === 'string') : [],
      completedChallenges: Array.isArray(record.completedChallenges)
        ? record.completedChallenges.filter((item): item is string => typeof item === 'string') : [],
    };
  } catch {
    return emptyProgress;
  }
}

function saveProgress(progress: LearningProgress): LearningProgress {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch {
    // Progress remains usable for the current page even when storage is unavailable.
  }
  return progress;
}

export function completeLesson(lessonId: string): LearningProgress {
  const current = getLearningProgress();
  return saveProgress({
    ...current,
    completedLessons: [...new Set([...current.completedLessons, lessonId])],
  });
}

export function completeChallenge(challengeId: string): LearningProgress {
  const current = getLearningProgress();
  return saveProgress({
    ...current,
    completedChallenges: [...new Set([...current.completedChallenges, challengeId])],
  });
}
