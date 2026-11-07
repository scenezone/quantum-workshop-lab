import type { Difficulty } from '../types/api';
import { EXPERIMENT_CHALLENGE_IDS } from '../types/catalog.generated';
import { practiceSummary, type LearningProgress } from './learningProgress';

export interface Badge {
  id: string;
  title: string;
  description: string;
  earned: boolean;
  /** Progress toward the badge, such as "3 / 5". */
  progress: string;
}

const ENTANGLEMENT_CHALLENGES = ['bell-correlations', 'bell-phi-minus', 'bell-psi-plus', 'ghz-three'];

function goal(id: string, title: string, description: string, current: number, target: number): Badge {
  return {
    id, title, description,
    earned: target > 0 && current >= target,
    progress: `${Math.min(current, target)} / ${target}`,
  };
}

export function computeBadges(
  progress: LearningProgress,
  lessons: { lesson_id: string; difficulty: Difficulty }[],
  buildChallengeIds: string[],
): Badge[] {
  const done = new Set(progress.completedLessons);
  const challenges = new Set(progress.completedChallenges);
  const practice = practiceSummary(progress);
  const allChallenges = [...EXPERIMENT_CHALLENGE_IDS, ...buildChallengeIds];
  const count = (items: { lesson_id: string }[]) => items.filter((lesson) => done.has(lesson.lesson_id)).length;
  const level = (difficulty: Difficulty) => lessons.filter((lesson) => lesson.difficulty === difficulty);
  return [
    goal('first-steps', 'First steps', 'Complete your first lesson.', done.size, 1),
    goal('foundations', 'Foundations', 'Complete every beginner lesson.', count(level('beginner')), level('beginner').length),
    goal('algorithmist', 'Algorithmist', 'Complete every advanced lesson.', count(level('advanced')), level('advanced').length),
    goal('full-path', 'Full learning path', 'Complete all lessons.', count(lessons), lessons.length),
    goal('experimenter', 'Experimenter', 'Complete your first challenge.', challenges.size, 1),
    goal('entangler', 'Entangler', 'Complete an entanglement challenge.',
      ENTANGLEMENT_CHALLENGES.filter((id) => challenges.has(id)).length, 1),
    goal('state-builder', 'State builder', 'Complete three circuit-building challenges.',
      buildChallengeIds.filter((id) => challenges.has(id)).length, 3),
    goal('sharp-shooter', 'Sharp shooter', 'Answer 10 practice questions correctly on the first try.',
      practice.firstTryCorrect, 10),
    goal('reflective', 'Reflective learner', 'Answer three written practice questions.', practice.written, 3),
    goal('completionist', 'Completionist', 'Complete every challenge.',
      allChallenges.filter((id) => challenges.has(id)).length, allChallenges.length),
  ];
}
