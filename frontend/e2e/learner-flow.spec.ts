import { expect, test } from '@playwright/test';

const lesson = {
  lesson_id: 'introduction',
  title: 'Introduction to quantum computing',
  description: 'Learn the basic idea of a qubit.',
  content: 'A qubit can be in a superposition of basis states.',
  difficulty: 'beginner',
  learning_objectives: ['Describe a qubit'],
  related_experiments: ['superposition'],
  order: 1,
  practice_questions: [{
    question_id: 'what-is-a-qubit',
    kind: 'multiple_choice',
    prompt: 'Which gate creates an equal superposition from |0>?',
    options: [
      { option_id: 'hadamard', text: 'The Hadamard gate' },
      { option_id: 'x', text: 'The X gate' },
    ],
  }],
};

const experiment = {
  experiment_id: 'superposition',
  title: 'Superposition',
  description: 'Prepare and measure a qubit in an equal superposition.',
  qubits: 1,
  classical_bits: 1,
  difficulty: 'beginner',
  lesson_id: 'introduction',
  gates: [
    { name: 'H', qubits: [0], explanation: 'Create equal amplitudes.' },
    { name: 'Measure', qubits: [0], classical_bits: [0], explanation: 'Measure the qubit.' },
  ],
  qiskit_code: 'qc.h(0)\nqc.measure(0, 0)',
  interpretation: 'The outcomes 0 and 1 are equally likely.',
  ideal_probabilities: { '0': 0.5, '1': 0.5 },
};

test('learner can open a lesson, check an answer, and run a simulation', async ({ page }) => {
  await page.route('**/api/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    let body: unknown;

    if (path === '/api/lessons' && request.method() === 'GET') {
      body = { lessons: [lesson] };
    } else if (path === '/api/config/public') {
      body = {
        hardware_enabled: false,
        max_simulator_shots: 10000,
        max_hardware_shots: 4096,
        default_shots: 512,
      };
    } else if (path === '/api/hardware/status') {
      body = {
        hardware_enabled: false,
        daily_limit: 25,
        submitted_today: 0,
        remaining_today: 25,
        active_jobs: 0,
        active_limit: 3,
        max_shots: 4096,
      };
    } else if (path === '/api/experiments') {
      body = { experiments: [experiment] };
    } else if (path === '/api/experiments/superposition/evolution') {
      body = {
        experiment_id: 'superposition',
        qubits: 1,
        steps: [
          { step: 0, gate: 'Start', explanation: 'All qubits start in |0>.', qubits: [{ qubit: 0, x: 0, y: 0, z: 1 }] },
          { step: 1, gate: 'H', explanation: 'Create equal amplitudes.', qubits: [{ qubit: 0, x: 1, y: 0, z: 0 }] },
        ],
      };
    } else if (path === '/api/lessons/introduction/practice/check') {
      body = {
        question_id: 'what-is-a-qubit',
        kind: 'multiple_choice',
        correct: true,
        correct_option_id: 'hadamard',
        explanation: 'A Hadamard gate maps |0> to an equal superposition.',
      };
    } else if (path === '/api/experiments/simulate') {
      body = {
        experiment_id: 'superposition',
        backend: 'aer_simulator',
        backend_name: 'Aer',
        shots: 512,
        counts: { '0': 254, '1': 258 },
        observed_probabilities: { '0': 254 / 512, '1': 258 / 512 },
        ideal_probabilities: { '0': 0.5, '1': 0.5 },
        amplitudes: [
          { outcome: '0', real: 0.7071, imag: 0, probability: 0.5, phase_degrees: 0 },
          { outcome: '1', real: 0.7071, imag: 0, probability: 0.5, phase_degrees: 0 },
        ],
      };
    } else {
      await route.fulfill({ status: 404, json: { detail: 'No browser-test fixture for this endpoint.' } });
      return;
    }

    await route.fulfill({ json: body });
  });

  await page.goto('/');
  await page.getByRole('link', { name: 'Start Learning' }).click();
  await expect(page.getByRole('heading', { name: lesson.title })).toBeVisible();

  await page.getByRole('radio').first().check();
  await page.getByRole('button', { name: 'Check answer' }).click();
  await expect(page.getByRole('status')).toContainText('Correct!');

  await page.getByRole('link', { name: 'Try superposition' }).click();
  await page.getByRole('button', { name: 'Run Simulator' }).click();
  await expect(page.getByRole('heading', { name: 'Measurement Results: Simulator' })).toBeVisible();
});
