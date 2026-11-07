import { describe, expect, it } from 'vitest';
import { pollInterval } from '../hooks/useExperimentJob';
import { computeBadges } from '../services/badges';
import { challenges } from '../services/challenges';
import {
  formatAngle, isValidCircuitDraft, isValidGate, parseAngle, qasmCode, qiskitCode,
} from '../services/circuit';
import { csv } from '../services/download';
import {
  completeChallenge, completeLesson, exportProgress, getLearningProgress, importProgress, practiceSummary,
  recordPracticeAttempt, recordWrittenAnswer, resetProgress,
} from '../services/learningProgress';
import {
  expectedSamplingDistance, hellingerFidelity, samplingVerdict, standardError, totalVariationDistance,
} from '../services/stats';
import { EXPERIMENT_CHALLENGE_IDS } from '../types/catalog.generated';
import type { JobStatusResponse } from '../types/api';

describe('angles', () => {
  it.each([
    ['pi/2', Math.PI / 2], ['π/3', Math.PI / 3], ['-3pi/4', -3 * Math.PI / 4], ['2*pi/3', 2 * Math.PI / 3],
    ['1.047', 1.047], ['  -0.5 ', -0.5], ['pi', Math.PI], ['1e-3', 0.001],
  ])('parses %s', (input, expected) => {
    expect(parseAngle(input)).toBeCloseTo(expected);
  });

  it.each(['', 'pi/0', 'abc', '2pi pi', 'alert(1)'])('rejects %j', (input) => {
    expect(parseAngle(input)).toBeNull();
  });

  it('formats common multiples of π exactly', () => {
    expect(formatAngle(Math.PI / 2)).toBe('π/2');
    expect(formatAngle(-3 * Math.PI / 4)).toBe('-3π/4');
    expect(formatAngle(0)).toBe('0');
    expect(formatAngle(1.2345678)).toBe('1.2346');
    expect(parseAngle(formatAngle(2 * Math.PI / 3))).toBeCloseTo(2 * Math.PI / 3);
  });
});

describe('circuit validation', () => {
  it('rejects shared links the backend would reject', () => {
    const base = { qubits: 2, shots: 128, noise_profile: 'ideal' };
    expect(isValidCircuitDraft({ ...base, gates: [{ name: 'H', qubits: [0] }] })).toBe(true);
    expect(isValidCircuitDraft({ ...base, gates: [{ name: 'RX', qubits: [0] }] })).toBe(false); // Missing angle.
    expect(isValidCircuitDraft({ ...base, gates: [{ name: 'CX', qubits: [0] }] })).toBe(false); // Missing target.
    expect(isValidCircuitDraft({ ...base, gates: [{ name: 'CX', qubits: [1, 1] }] })).toBe(false);
    expect(isValidCircuitDraft({ ...base, gates: [{ name: 'H', qubits: [0], angle: 1 }] })).toBe(false);
    expect(isValidCircuitDraft({ ...base, gates: [{ name: 'H', qubits: [2] }] })).toBe(false);
    expect(isValidCircuitDraft({ ...base, noise_profile: 'device_manila', gates: [] })).toBe(true);
    expect(isValidCircuitDraft({ ...base, noise_profile: 'loud', gates: [] })).toBe(false);
    expect(isValidCircuitDraft({ ...base, gates: [], measurement_bases: ['X'] })).toBe(false);
  });

  it('accepts the new gates with their parameters', () => {
    expect(isValidGate({ name: 'U', qubits: [0], angle: 1, phi: 0, lam: 2 }, 1)).toBe(true);
    expect(isValidGate({ name: 'U', qubits: [0], angle: 1 }, 1)).toBe(false);
    expect(isValidGate({ name: 'CCX', qubits: [0, 1, 2] }, 3)).toBe(true);
    expect(isValidGate({ name: 'CP', qubits: [0, 1], angle: 10 }, 2)).toBe(false); // Beyond 2π.
  });

  it('exports Qiskit and OpenQASM, including measurement-basis rotations', () => {
    const gates = [
      { name: 'H' as const, qubits: [0] },
      { name: 'CP' as const, qubits: [0, 1], angle: Math.PI / 2 },
      { name: 'U' as const, qubits: [1], angle: 1, phi: 2, lam: 3 },
    ];
    const python = qiskitCode(2, gates, ['X', 'Y']);
    expect(python).toContain('qc.cp(1.5707963267948966, 0, 1)');
    expect(python).toContain('qc.u(1, 2, 3, 1)');
    expect(python).toContain('qc.sdg(1)');
    const qasm = qasmCode(2, gates, ['Z', 'X']);
    expect(qasm).toContain('cp(1.5707963267948966) q[0],q[1];');
    expect(qasm).toContain('h q[1];');
    expect(qasm.endsWith('\nmeasure q -> c;')).toBe(true);
  });
});

describe('statistics', () => {
  it('measures distance and fidelity', () => {
    expect(totalVariationDistance({ '0': 1 }, { '1': 1 })).toBe(1);
    expect(totalVariationDistance({ '0': 0.5, '1': 0.5 }, { '0': 0.5, '1': 0.5 })).toBe(0);
    expect(hellingerFidelity({ '0': 1 }, { '0': 0.5, '1': 0.5 })).toBeCloseTo(0.5);
    expect(standardError(0.5, 100)).toBeCloseTo(0.05);
    expect(expectedSamplingDistance({ '0': 0.5, '1': 0.5 }, 1000)).toBeGreaterThan(0);
  });

  it('separates sampling noise from impossible outcomes and large deviations', () => {
    expect(samplingVerdict({ '0': 520, '1': 504 }, { '0': 0.5, '1': 0.5 }).consistent).toBe(true);
    const noisy = samplingVerdict({ '00': 480, '11': 470, '01': 74 }, { '00': 0.5, '11': 0.5 });
    expect(noisy.consistent).toBe(false);
    expect(noisy.forbiddenShare).toBeCloseTo(74 / 1024);
    expect(noisy.summary).toMatch(/never produces/);
    expect(samplingVerdict({ '0': 900, '1': 124 }, { '0': 0.5, '1': 0.5 }).summary).toMatch(/standard errors/);
  });
});

describe('progress', () => {
  it('records practice results, exports, and merges imports', () => {
    resetProgress();
    completeLesson('superposition');
    recordPracticeAttempt('q1', false);
    recordPracticeAttempt('q1', true);
    recordPracticeAttempt('q2', true);
    recordWrittenAnswer('w1');
    expect(practiceSummary(getLearningProgress())).toEqual({ attempted: 2, correct: 2, firstTryCorrect: 1, written: 1 });

    const file = exportProgress();
    resetProgress();
    completeChallenge('ghz-three');
    importProgress(file, 'merge');
    expect(getLearningProgress().completedLessons).toEqual(['superposition']);
    expect(getLearningProgress().completedChallenges).toEqual(['ghz-three']);
    importProgress(file, 'replace');
    expect(getLearningProgress().completedChallenges).toEqual([]);
    expect(() => importProgress('{"format":"other"}')).toThrow(/not a Quantum Workshop Lab/);
    expect(() => importProgress('not json')).toThrow(/not valid JSON/);
    resetProgress();
  });

  it('awards badges from progress', () => {
    resetProgress();
    completeLesson('intro');
    completeChallenge('bell-phi-minus');
    const badges = computeBadges(getLearningProgress(),
      [{ lesson_id: 'intro', difficulty: 'beginner' }, { lesson_id: 'grover', difficulty: 'advanced' }], ['bell-phi-minus']);
    const earned = badges.filter((badge) => badge.earned).map((badge) => badge.id);
    expect(earned).toEqual(expect.arrayContaining(['first-steps', 'foundations', 'experimenter', 'entangler']));
    expect(earned).not.toContain('algorithmist');
    resetProgress();
  });
});

describe('shared catalog', () => {
  it('keeps frontend experiment challenges in sync with the backend list', () => {
    expect(challenges.map((challenge) => challenge.id).sort()).toEqual([...EXPERIMENT_CHALLENGE_IDS].sort());
  });
});

describe('job polling', () => {
  const job = (minutesAgo: number) => ({ created_at: new Date(Date.now() - minutesAgo * 60000).toISOString() }) as JobStatusResponse;
  it('backs off as a hardware job ages', () => {
    expect(pollInterval(job(0.5), 0)).toBe(5000);
    expect(pollInterval(job(5), 0)).toBe(15000);
    expect(pollInterval(job(30), 0)).toBe(60000);
    expect(pollInterval(job(120), 0)).toBe(300000);
    expect(pollInterval(undefined, 0)).toBe(5000);
  });
});

describe('csv', () => {
  it('neutralizes spreadsheet formulas but keeps negative numbers', () => {
    expect(csv([['=1+1', '-0.5', '@x']])).toBe(`"'=1+1","-0.5","'@x"`);
  });
});
