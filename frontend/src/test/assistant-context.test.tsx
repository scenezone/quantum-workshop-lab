import { StrictMode } from 'react';
import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, it, vi } from 'vitest';
import { AssistantProvider } from '../context/AssistantContext';
import Assistant from '../pages/Assistant';
import Learn from '../pages/Learn';
import Playground from '../pages/Playground';
import * as api from '../services/api';
import type { Experiment, ExperimentResult, Lesson } from '../types/api';

vi.mock('../services/api', () => ({
  fetchLessons: vi.fn(), fetchExperiments: vi.fn(), fetchPublicConfig: vi.fn(),
  fetchHardwareStatus: vi.fn(), fetchJobStatus: vi.fn(), simulateExperiment: vi.fn(),
  submitHardwareExperiment: vi.fn(), sendAssistantMessage: vi.fn(),
}));
vi.mock('../components/MeasurementHistogram', () => ({ default: () => null }));
vi.mock('../components/ProbabilityComparison', () => ({ default: () => null }));

const lesson: Lesson = {
  lesson_id: 'entanglement', title: 'Entanglement', description: 'Learn about Bell states.',
  content: 'Entangled qubits have joint states.', difficulty: 'beginner',
  learning_objectives: ['Explain Bell correlations'], related_experiments: ['bell_entanglement'], order: 1,
};
const advancedLesson: Lesson = {
  ...lesson, lesson_id: 'grover-search', title: 'Grover search', difficulty: 'advanced',
  description: 'Amplitude amplification.', content: 'Use an oracle and diffusion.', order: 2,
};
const experiment: Experiment = {
  experiment_id: 'bell_entanglement', title: 'Bell circuit', description: 'Create an entangled pair.',
  qubits: 2, classical_bits: 2, difficulty: 'beginner', lesson_id: 'entanglement',
  gates: [{ name: 'H', qubits: [0], explanation: 'Prepare a superposition.' }],
  qiskit_code: 'qc.h(0)', interpretation: 'Look for correlated measurements.',
  ideal_probabilities: { '00': 0.5, '11': 0.5 },
};
const result: ExperimentResult = {
  experiment_id: 'bell_entanglement', backend: 'aer_simulator', backend_name: 'Aer', shots: 128,
  counts: { '00': 60, '11': 68 }, observed_probabilities: { '00': 60 / 128, '11': 68 / 128 },
  ideal_probabilities: experiment.ideal_probabilities, provider_job_id: null, tracking_id: null,
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.fetchLessons).mockResolvedValue([lesson, advancedLesson]);
  vi.mocked(api.fetchExperiments).mockResolvedValue([experiment]);
  vi.mocked(api.fetchPublicConfig).mockResolvedValue({ hardware_enabled: false, default_shots: 128, max_simulator_shots: 1024, max_hardware_shots: 1024 });
  vi.mocked(api.fetchHardwareStatus).mockResolvedValue({ hardware_enabled: false, daily_limit: 1,
    submitted_today: 0, remaining_today: 1, active_jobs: 0, active_limit: 1, max_shots: 1024 });
  vi.mocked(api.simulateExperiment).mockResolvedValue(result);
  vi.mocked(api.sendAssistantMessage).mockResolvedValue({ reply: 'An overview of your selected topic.', source: 'llm' });
});

function show(path = '/learn?lesson=entanglement') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<StrictMode><QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}>
    <AssistantProvider>
      <nav><Link to="/learn?lesson=entanglement">Open learning page</Link><Link to="/assistant">Open assistant page</Link></nav>
      <Routes>
        <Route path="/learn" element={<Learn />} />
        <Route path="/playground" element={<Playground />} />
        <Route path="/assistant" element={<Assistant />} />
      </Routes>
    </AssistantProvider>
  </MemoryRouter></QueryClientProvider></StrictMode>);
}

it('automatically introduces the selected lesson once and retains it for follow-up questions and navigation', async () => {
  show();
  const user = userEvent.setup();
  await user.click(await screen.findByRole('link', { name: 'Discuss this lesson' }));
  expect(await screen.findByText('An overview of your selected topic.')).toBeInTheDocument();
  expect(within(screen.getByRole('region', { name: 'Current study topic' })).getByText('Entanglement')).toBeInTheDocument();
  expect(api.sendAssistantMessage).toHaveBeenCalledTimes(1);
  expect(vi.mocked(api.sendAssistantMessage).mock.calls[0].slice(1, 4)).toEqual(['entanglement', undefined, undefined]);
  await user.type(screen.getByRole('textbox'), 'Explain this more simply.');
  await user.click(screen.getByRole('button', { name: 'Send message' }));
  await waitFor(() => expect(api.sendAssistantMessage).toHaveBeenCalledTimes(2));
  expect(vi.mocked(api.sendAssistantMessage).mock.calls[1][1]).toBe('entanglement');
  await user.click(screen.getByRole('link', { name: 'Open learning page' }));
  await user.click(await screen.findByRole('link', { name: 'Discuss this lesson' }));
  expect(api.sendAssistantMessage).toHaveBeenCalledTimes(2);
});

it('carries the selected circuit and actual simulator results into the standalone assistant', async () => {
  show('/playground?experiment=bell_entanglement');
  const user = userEvent.setup();
  await waitFor(() => expect(screen.getByRole('button', { name: 'Run Simulator' })).toBeEnabled());
  expect(api.sendAssistantMessage).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: 'Run Simulator' }));
  await screen.findByText('Measurement Results: Simulator');
  await user.click(screen.getByRole('link', { name: 'Open assistant page' }));
  await screen.findByText('An overview of your selected topic.');
  const request = vi.mocked(api.sendAssistantMessage).mock.calls[0];
  expect(request[1]).toBe('entanglement');
  expect(request[2]).toBe('bell_entanglement');
  expect(request[3]).toMatchObject({ counts: { '00': 60, '11': 68 }, shots: 128, backend: 'aer_simulator' });
  expect(screen.getByText('Recorded results: 128 shots · Simulator')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Explain my recorded results/ })).toBeInTheDocument();
});

it('aborts an old topic request and starts a fresh conversation for the new lesson', async () => {
  let finish!: (value: { reply: string; source: 'llm' }) => void;
  vi.mocked(api.sendAssistantMessage).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }))
    .mockResolvedValueOnce({ reply: 'Grover amplifies the marked state.', source: 'llm' });
  show();
  const user = userEvent.setup();
  await user.click(await screen.findByRole('link', { name: 'Discuss this lesson' }));
  await screen.findByRole('status');
  const oldSignal = vi.mocked(api.sendAssistantMessage).mock.calls[0][4];
  await user.click(screen.getByRole('link', { name: 'Open learning page' }));
  await user.click(await screen.findByRole('button', { name: /Grover search/ }));
  expect(oldSignal?.aborted).toBe(true);
  await user.click(screen.getByRole('link', { name: 'Discuss this lesson' }));
  expect(await screen.findByText('Grover amplifies the marked state.')).toBeInTheDocument();
  const newRequest = vi.mocked(api.sendAssistantMessage).mock.calls[1];
  expect(newRequest[1]).toBe('grover-search');
  expect(newRequest[0]).toHaveLength(1);
  await act(async () => finish({ reply: 'Late reply about entanglement.', source: 'llm' }));
  expect(screen.queryByText('Late reply about entanglement.')).not.toBeInTheDocument();
});

it('keeps the topic when chat is cleared without issuing another automatic overview', async () => {
  show();
  const user = userEvent.setup();
  await user.click(await screen.findByRole('link', { name: 'Discuss this lesson' }));
  await screen.findByText('An overview of your selected topic.');
  await user.click(screen.getByRole('button', { name: 'Clear chat' }));
  expect(screen.getByRole('region', { name: 'Current study topic' })).toHaveTextContent('Entanglement');
  expect(screen.queryByText('An overview of your selected topic.')).not.toBeInTheDocument();
  expect(api.sendAssistantMessage).toHaveBeenCalledTimes(1);
});

it('retries a failed automatic overview with its original lesson context', async () => {
  vi.mocked(api.sendAssistantMessage).mockRejectedValueOnce(new Error('offline'))
    .mockResolvedValueOnce({ reply: 'Your lesson explains Bell correlations.', source: 'llm' });
  show();
  const user = userEvent.setup();
  await user.click(await screen.findByRole('link', { name: 'Discuss this lesson' }));
  await screen.findByRole('alert');
  await user.click(screen.getByRole('button', { name: 'Retry message' }));
  expect(await screen.findByText('Your lesson explains Bell correlations.')).toBeInTheDocument();
  expect(vi.mocked(api.sendAssistantMessage).mock.calls[1][1]).toBe('entanglement');
  expect(api.sendAssistantMessage).toHaveBeenCalledTimes(2);
});

it('opens without an unsolicited request when no lesson or experiment has been selected', () => {
  show('/assistant');
  expect(screen.getByRole('button', { name: 'What is a qubit?' })).toBeInTheDocument();
  expect(api.sendAssistantMessage).not.toHaveBeenCalled();
});
