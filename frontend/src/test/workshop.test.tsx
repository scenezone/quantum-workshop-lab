import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { AssistantProvider, useAssistant } from '../context/AssistantContext';
import CircuitDiagram from '../components/CircuitDiagram';
import FeedbackForm from '../components/FeedbackForm';
import Learn from '../pages/Learn';
import Playground from '../pages/Playground';
import Markdown from '../components/Markdown';
import * as api from '../services/api';
import type { Experiment } from '../types/api';
import { saveSubmission } from '../services/hardwareStorage';

vi.mock('../services/api', () => ({
  fetchPublicConfig: vi.fn(), fetchExperiments: vi.fn(), fetchHardwareStatus: vi.fn(),
  fetchJobStatus: vi.fn(), simulateExperiment: vi.fn(), submitHardwareExperiment: vi.fn(),
  fetchLessons: vi.fn(), submitFeedback: vi.fn(),
  sendAssistantMessage: vi.fn(),
}));
vi.mock('../components/MeasurementHistogram', () => ({
  default: ({ counts }: { counts: Record<string, number> }) => <output aria-label="counts">{JSON.stringify(counts)}</output>,
}));
vi.mock('../components/ProbabilityComparison', () => ({ default: () => null }));
vi.mock('../components/AIChatPanel', () => ({ default: () => null }));

function ContextProbe() {
  const { lessonId, experimentId, resultContext } = useAssistant();
  return <output aria-label="assistant context">{JSON.stringify({ lessonId, experimentId, resultContext })}</output>;
}
function show(component: React.ReactNode, path = '/playground') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}>
    <AssistantProvider>{component}<ContextProbe /></AssistantProvider>
  </MemoryRouter></QueryClientProvider>);
}
const result = {
  experiment_id: 'superposition', backend: 'aer_simulator' as const, backend_name: 'Aer',
  shots: 512, counts: { '1': 512 }, observed_probabilities: { '1': 1 },
  ideal_probabilities: { '0': 0.5, '1': 0.5 }, provider_job_id: null, tracking_id: null,
};

const superposition: Experiment = {
  experiment_id: 'superposition', title: 'Superposition', description: 'One qubit', qubits: 1,
  classical_bits: 1, difficulty: 'beginner', lesson_id: 'superposition',
  gates: [{ name: 'H', qubits: [0], explanation: 'Prepare superposition.' },
    { name: 'Measure', qubits: [0], classical_bits: [0], explanation: 'Measure q0.' }],
  qiskit_code: 'qc.h(0)', interpretation: 'Equal probabilities.', ideal_probabilities: { '0': .5, '1': .5 },
};
const bell: Experiment = {
  ...superposition, experiment_id: 'bell_entanglement', title: 'Bell', qubits: 2, classical_bits: 2,
  gates: [{ name: 'H', qubits: [0], explanation: 'Prepare superposition.' },
    { name: 'CX', qubits: [0, 1], explanation: 'Entangle.' },
    { name: 'Measure', qubits: [0, 1], classical_bits: [0, 1], explanation: 'Measure both.' }],
};

beforeEach(() => {
  vi.mocked(api.fetchPublicConfig).mockResolvedValue({
    hardware_enabled: true, max_simulator_shots: 2000, max_hardware_shots: 2000, default_shots: 512,
  });
  vi.mocked(api.fetchExperiments).mockResolvedValue([superposition, bell]);
  vi.mocked(api.fetchHardwareStatus).mockResolvedValue({
    hardware_enabled: true, daily_limit: 25, submitted_today: 0, remaining_today: 25,
    active_jobs: 0, active_limit: 3, max_shots: 2000,
  });
});
afterEach(() => {
  act(() => {
    saveSubmission('superposition');
    saveSubmission('bell_entanglement');
    saveSubmission('interference');
  });
  vi.clearAllMocks();
});

describe('workshop regressions', () => {
  it('renders a valid circuit viewBox and visible SVG label fills', () => {
    render(<CircuitDiagram experiment={bell} />);
    const svg = screen.getByRole('img', { name: 'Quantum circuit diagram' });
    expect(svg).toHaveAttribute('viewBox', '0 0 420 240');
    expect(screen.getByText('H')).toHaveClass('fill-current');
  });

  it('renders lesson math using KaTeX', () => {
    const { container } = render(<Markdown>{'$\\frac{1}{2}$'}</Markdown>);
    expect(container.querySelector('.katex')).not.toBeNull();
  });

  it('reports feedback failure and permits a successful retry', async () => {
    const user = userEvent.setup();
    vi.mocked(api.submitFeedback).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(undefined);
    render(<FeedbackForm />);
    await user.click(screen.getByRole('button', { name: 'Submit feedback' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('could not be submitted');
    await user.click(screen.getByRole('button', { name: 'Submit feedback' }));
    expect(await screen.findByText(/Thank you/)).toBeInTheDocument();
  });

  it('passes the selected lesson to the assistant and links to its experiment', async () => {
    vi.mocked(api.fetchLessons).mockResolvedValue([{
      lesson_id: 'entanglement', title: 'Entanglement', description: 'Learn Bell states', content: 'A Bell state',
      difficulty: 'beginner', learning_objectives: [], related_experiments: ['bell_entanglement'], order: 1,
    }]);
    show(<Learn />, '/learn');
    expect(await screen.findByRole('link', { name: 'Try bell entanglement' }))
      .toHaveAttribute('href', '/playground?experiment=bell_entanglement');
    await waitFor(() => expect(screen.getByLabelText('assistant context')).toHaveTextContent('"lessonId":"entanglement"'));
  });

  it('honors related-experiment URLs and configured shot defaults', async () => {
    show(<Playground />, '/playground?experiment=bell_entanglement');
    await waitFor(() => expect(screen.getByLabelText('Shots')).toHaveValue('512'));
    expect(screen.getByRole('img')).toHaveAttribute('viewBox', '0 0 420 240');
    expect(screen.queryByRole('option', { name: '4096' })).not.toBeInTheDocument();
  });

  it('prevents switching experiments during a simulation', async () => {
    const user = userEvent.setup();
    let resolve!: (value: typeof result) => void;
    vi.mocked(api.simulateExperiment).mockImplementation(() => new Promise((done) => { resolve = done; }));
    show(<Playground />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Run Simulator' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: 'Run Simulator' }));
    expect(screen.getByRole('button', { name: /Bell/ })).toBeDisabled();
    await act(async () => resolve(result));
    expect(await screen.findByLabelText('counts')).toHaveTextContent('512');
  });

  it('shows new simulator results after completed hardware and updates assistant context', async () => {
    saveSubmission('superposition', { trackingId: 'saved-token', idempotencyKey: 'saved-key', shots: 100 });
    vi.mocked(api.fetchJobStatus).mockResolvedValue({
      tracking_id: 'saved-token', experiment_id: 'superposition', status: 'completed', backend_name: 'IBM',
      provider_job_id: 'provider', shots: 100, counts: { '0': 100 }, observed_probabilities: { '0': 1 },
      ideal_probabilities: { '0': .5, '1': .5 }, error: null,
    });
    vi.mocked(api.simulateExperiment).mockResolvedValue(result);
    show(<Playground />);
    expect(await screen.findByLabelText('counts')).toHaveTextContent('100');
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Run Simulator' }));
    await waitFor(() => expect(screen.getByLabelText('counts')).toHaveTextContent('512'));
    await waitFor(() => expect(screen.getByLabelText('assistant context')).toHaveTextContent('aer_simulator'));
  });

  it('reuses a pending submission key even when no quota remains', async () => {
    saveSubmission('superposition', { trackingId: null, idempotencyKey: 'original-submission-key', shots: 128 });
    vi.mocked(api.fetchHardwareStatus).mockResolvedValue({
      hardware_enabled: true, daily_limit: 1, submitted_today: 1, remaining_today: 0,
      active_jobs: 3, active_limit: 3, max_shots: 2000,
    });
    vi.mocked(api.submitHardwareExperiment).mockResolvedValue({ tracking_id: 'recovered-token', status: 'queued' });
    vi.mocked(api.fetchJobStatus).mockResolvedValue({
      tracking_id: 'recovered-token', experiment_id: 'superposition', status: 'queued', backend_name: null,
      provider_job_id: null, shots: 128, counts: null, observed_probabilities: null,
      ideal_probabilities: {}, error: null,
    });
    show(<Playground />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'Retry submission' }));
    expect(api.submitHardwareExperiment).toHaveBeenCalledWith('superposition', 128, 'original-submission-key');
  });

  it('renders nonmatching quantum-to-classical measurement indices', () => {
    render(<CircuitDiagram experiment={{ ...superposition, qubits: 3, gates: [
      { name: 'CCX', qubits: [1, 2, 0], explanation: 'Recover the data using syndrome controls.' },
      { name: 'Measure', qubits: [2], classical_bits: [0], explanation: 'Read receiver q2 into c0.' },
    ] }} />);
    expect(screen.getByText('c[0]')).toBeInTheDocument();
    expect(screen.queryByText('c[2]')).not.toBeInTheDocument();
    expect(screen.getByRole('img').querySelectorAll('circle')).toHaveLength(2);
  });

  it('filters advanced lessons and follows prerequisite links', async () => {
    vi.mocked(api.fetchLessons).mockResolvedValue([
      { lesson_id: 'complex-amplitudes', title: 'Complex amplitudes', description: 'Study phases', content: 'Complex statevectors',
        difficulty: 'intermediate', learning_objectives: ['Normalize amplitudes'], related_experiments: ['qft_phase'], order: 6 },
      { lesson_id: 'grover-search', title: 'Grover search', description: 'Amplitude amplification', content: 'A phase oracle',
        difficulty: 'advanced', learning_objectives: ['Explain diffusion'], related_experiments: ['grover_search'],
        prerequisites: ['complex-amplitudes'], order: 10 },
    ]);
    show(<Learn />, '/learn?lesson=grover-search');
    await screen.findByRole('heading', { name: 'Grover search' });
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /advanced \(1\)/i }));
    expect(screen.getByRole('heading', { name: 'Grover search' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Complex amplitudes' }));
    expect(await screen.findByRole('heading', { name: 'Complex amplitudes' })).toBeInTheDocument();
    await user.type(screen.getByRole('textbox', { name: 'Search lessons' }), 'nonexistent concept');
    expect(screen.getByText(/No lessons match/)).toBeInTheDocument();
  });

  it('shows QFT phases and connects the advanced circuit to its theory', async () => {
    const qft: Experiment = { ...superposition, experiment_id: 'qft_phase', title: 'QFT', qubits: 2,
      classical_bits: 2, difficulty: 'advanced', lesson_id: 'quantum-fourier-transform',
      interpretation: 'Equal magnitudes with distinct phases.',
    };
    vi.mocked(api.fetchExperiments).mockResolvedValue([superposition, qft]);
    vi.mocked(api.simulateExperiment).mockResolvedValue({ ...result, experiment_id: 'qft_phase',
      amplitudes: [
        { outcome: '00', real: .5, imag: 0, probability: .25, phase_degrees: 0 },
        { outcome: '01', real: 0, imag: .5, probability: .25, phase_degrees: 90 },
        { outcome: '10', real: -.5, imag: 0, probability: .25, phase_degrees: 180 },
        { outcome: '11', real: 0, imag: -.5, probability: .25, phase_degrees: -90 },
      ],
    });
    show(<Playground />, '/playground?experiment=qft_phase');
    await waitFor(() => expect(screen.getByRole('button', { name: 'Run Simulator' })).toBeEnabled());
    await userEvent.setup().click(screen.getByRole('button', { name: 'Run Simulator' }));
    expect(await screen.findByText('90.0 deg')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Study the theory' })).toHaveAttribute('href', '/learn?lesson=quantum-fourier-transform');
    expect(screen.getAllByText('25.00%')).toHaveLength(4);
    await waitFor(() => expect(screen.getByLabelText('assistant context')).toHaveTextContent('phase_degrees'));
  });
});
