/** Statistics that help learners judge whether a histogram differs from the ideal by chance. */

export type Distribution = Record<string, number>;

function outcomes(...distributions: Distribution[]): string[] {
  return [...new Set(distributions.flatMap((item) => Object.keys(item)))].sort();
}

/** Binomial standard error of an observed frequency. */
export function standardError(probability: number, shots: number): number {
  return shots > 0 ? Math.sqrt(Math.max(0, probability * (1 - probability)) / shots) : 0;
}

/** Half the summed absolute differences: 0 for identical, 1 for disjoint distributions. */
export function totalVariationDistance(p: Distribution, q: Distribution): number {
  return outcomes(p, q).reduce((total, key) => total + Math.abs((p[key] ?? 0) - (q[key] ?? 0)), 0) / 2;
}

/** Classical fidelity (Σ√(pq))²: 1 for identical distributions. */
export function hellingerFidelity(p: Distribution, q: Distribution): number {
  const overlap = outcomes(p, q).reduce((total, key) => total + Math.sqrt((p[key] ?? 0) * (q[key] ?? 0)), 0);
  return overlap ** 2;
}

/** The distance finite sampling alone typically produces: ½ Σ √(2p(1−p)/(πN)). */
export function expectedSamplingDistance(ideal: Distribution, shots: number): number {
  if (shots <= 0) return 0;
  return Object.values(ideal).reduce(
    (total, p) => total + Math.sqrt((2 * p * (1 - p)) / (Math.PI * shots)), 0,
  ) / 2;
}

export interface SamplingVerdict {
  consistent: boolean;
  /** Largest |observed − ideal| in standard errors among outcomes the ideal circuit allows. */
  maxZScore: number;
  /** Fraction of shots on outcomes with zero ideal probability. */
  forbiddenShare: number;
  summary: string;
}

export function samplingVerdict(counts: Record<string, number>, ideal: Distribution, threshold = 3): SamplingVerdict {
  const shots = Object.values(counts).reduce((total, value) => total + value, 0);
  let maxZScore = 0;
  let forbidden = 0;
  for (const key of outcomes(counts, ideal)) {
    const p = ideal[key] ?? 0;
    const observed = shots ? (counts[key] ?? 0) / shots : 0;
    if (p <= 1e-12) {
      forbidden += counts[key] ?? 0;
      continue;
    }
    const error = standardError(p, shots);
    const z = error > 0 ? Math.abs(observed - p) / error : (Math.abs(observed - p) > 1e-12 ? Infinity : 0);
    maxZScore = Math.max(maxZScore, z);
  }
  const forbiddenShare = shots ? forbidden / shots : 0;
  const consistent = forbidden === 0 && maxZScore <= threshold;
  const summary = consistent
    ? `Consistent with sampling noise: every outcome is within ${threshold} standard errors of its ideal probability.`
    : forbidden > 0
      ? `${(forbiddenShare * 100).toFixed(1)}% of shots landed on outcomes the ideal circuit never produces. That points to gate or readout noise.`
      : `At least one outcome is ${Number.isFinite(maxZScore) ? maxZScore.toFixed(1) : 'many'} standard errors from its ideal probability. Sampling alone rarely explains a gap that large.`;
  return { consistent, maxZScore, forbiddenShare, summary };
}
