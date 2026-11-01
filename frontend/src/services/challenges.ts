import type { ExperimentResult } from '../types/api';

export interface WorkshopChallenge {
  id: string;
  title: string;
  objective: string;
  experimentId: string;
  minimumShots: number;
  check: (result: ExperimentResult) => boolean;
}

export const challenges: WorkshopChallenge[] = [
  {
    id: 'balanced-superposition',
    title: 'Build a balanced superposition',
    objective: 'Run the Hadamard experiment and observe both outcomes between 35% and 65%.',
    experimentId: 'superposition',
    minimumShots: 128,
    check: (result) => (result.observed_probabilities['0'] ?? 0) >= 0.35
      && (result.observed_probabilities['0'] ?? 0) <= 0.65
      && (result.observed_probabilities['1'] ?? 0) >= 0.35
      && (result.observed_probabilities['1'] ?? 0) <= 0.65,
  },
  {
    id: 'bell-correlations',
    title: 'Find the Bell-state correlation',
    objective: 'Run the Bell circuit with at least 128 shots. Every result should be 00 or 11, and both should appear.',
    experimentId: 'bell_entanglement',
    minimumShots: 128,
    check: (result) => Object.keys(result.counts).every((outcome) => outcome === '00' || outcome === '11')
      && Boolean(result.counts['00']) && Boolean(result.counts['11']),
  },
  {
    id: 'interference-cancellation',
    title: 'Cancel the |1⟩ amplitude',
    objective: 'Run the interference circuit and measure only 0.',
    experimentId: 'interference',
    minimumShots: 128,
    check: (result) => Object.keys(result.counts).every((outcome) => outcome === '0'),
  },
];

export function getChallenge(id: string | null): WorkshopChallenge | undefined {
  return challenges.find((challenge) => challenge.id === id);
}

export function evaluateChallenge(id: string, result: ExperimentResult): boolean {
  const challenge = getChallenge(id);
  return Boolean(challenge && result.experiment_id === challenge.experimentId
    && result.noise_profile === 'ideal'
    && result.shots >= challenge.minimumShots && challenge.check(result));
}
