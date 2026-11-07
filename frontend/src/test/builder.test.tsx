import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CircuitBuilder from '../pages/CircuitBuilder';
import * as api from '../services/api';
import { getLearningProgress, resetProgress } from '../services/learningProgress';

vi.mock('../services/api', () => ({
  fetchPublicConfig: vi.fn(), simulateCustomCircuit: vi.fn(), fetchCustomEvolution: vi.fn(),
  importQasm: vi.fn(), fetchBuildChallenges: vi.fn(), checkBuildChallenge: vi.fn(),
}));
vi.mock('../components/MeasurementHistogram', () => ({
  default: ({ counts }: { counts: Record<string, number> }) => <output aria-label="counts">{JSON.stringify(counts)}</output>,
}));
vi.mock('../components/ProbabilityComparison', () => ({ default: () => null }));

function show(path = '/builder') {
  window.history.replaceState({}, '', path);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><CircuitBuilder /></MemoryRouter></QueryClientProvider>);
}

const code = () => screen.getByText(/from qiskit import QuantumCircuit/).textContent ?? '';

beforeEach(() => {
  vi.mocked(api.fetchPublicConfig).mockResolvedValue({
    hardware_enabled: false, max_simulator_shots: 4096, max_hardware_shots: 1024, default_shots: 512,
  });
  vi.mocked(api.fetchCustomEvolution).mockResolvedValue({ experiment_id: 'custom', qubits: 2, steps: [] });
  vi.mocked(api.fetchBuildChallenges).mockResolvedValue([{
    challenge_id: 'bell-psi-plus', title: 'Prepare the Ψ⁺ Bell state', objective: 'Prepare (|01⟩ + |10⟩)/√2.',
    difficulty: 'intermediate', qubits: 2, allowed_gates: ['H', 'X', 'CX'], max_gates: 4, hint: 'Flip one qubit.', kind: 'state',
  }]);
});
afterEach(() => {
  vi.clearAllMocks();
  resetProgress();
  window.history.replaceState({}, '', '/');
});

describe('circuit builder', () => {
  it('places single and two-qubit gates by clicking wires, then undoes', async () => {
    const user = userEvent.setup();
    show();
    await user.click(screen.getByRole('button', { name: 'Place gate on q0' }));
    expect(code()).toContain('qc.h(0)');

    await user.click(screen.getByRole('radio', { name: /^CX/ }));
    await user.click(screen.getByRole('button', { name: 'Place gate on q0' }));
    expect(screen.getByRole('button', { name: 'q0 selected as operand 1' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Place gate on q1' }));
    expect(code()).toContain('qc.cx(0, 1)');

    await user.click(screen.getByRole('button', { name: 'Undo' }));
    expect(code()).not.toContain('qc.cx');
    await user.click(screen.getByRole('button', { name: 'Redo' }));
    expect(code()).toContain('qc.cx(0, 1)');
  });

  it('accepts π expressions for rotations and edits a selected gate', async () => {
    const user = userEvent.setup();
    show();
    await user.click(screen.getByRole('radio', { name: /^RY/ }));
    const angle = screen.getByLabelText('θ (theta)');
    await user.clear(angle);
    await user.type(angle, 'pi/3');
    await user.click(screen.getByRole('button', { name: 'Place gate on q1' }));
    expect(code()).toContain('qc.ry(1.0471975511965976, 1)');

    await user.click(screen.getByRole('button', { name: /Gate 1: RY\(π\/3\) on q1/ }));
    const editor = screen.getByLabelText('Selected gate');
    const editAngle = within(editor).getByLabelText('θ (theta)');
    await user.clear(editAngle);
    await user.type(editAngle, 'pi');
    await user.click(within(editor).getByRole('button', { name: 'Apply angles' }));
    expect(code()).toContain('qc.ry(3.141592653589793, 1)');
  });

  it('ignores an invalid shared link instead of failing on the server', () => {
    const bad = encodeURIComponent(JSON.stringify({ qubits: 2, gates: [{ name: 'RX', qubits: [0] }], shots: 128, noise_profile: 'ideal' }));
    show(`/builder?circuit=${bad}`);
    expect(screen.getByText(/Add a gate to begin/)).toBeInTheDocument();
  });

  it('runs with chosen measurement bases', async () => {
    const user = userEvent.setup();
    vi.mocked(api.simulateCustomCircuit).mockResolvedValue({
      experiment_id: 'custom', backend: 'aer_simulator', backend_name: 'Qiskit Aer', shots: 512, noise_profile: 'ideal',
      measurement_bases: ['X', 'Z'], counts: { '00': 512 }, observed_probabilities: { '00': 1 },
      ideal_probabilities: { '00': 1 }, provider_job_id: null, tracking_id: null, amplitudes: [],
    });
    show();
    await user.click(screen.getByRole('button', { name: 'Place gate on q0' }));
    await user.selectOptions(screen.getByLabelText('Measurement basis for q0'), 'X');
    await waitFor(() => expect(screen.getByRole('button', { name: 'Run circuit' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: 'Run circuit' }));
    expect(vi.mocked(api.simulateCustomCircuit).mock.calls[0][0]).toEqual(expect.objectContaining({ measurement_bases: ['X', 'Z'] }));
    expect(await screen.findByText(/measured in the XZ basis/)).toBeInTheDocument();
  });

  it('checks a build challenge and records completion', async () => {
    const user = userEvent.setup();
    vi.mocked(api.checkBuildChallenge).mockResolvedValue({
      challenge_id: 'bell-psi-plus', passed: true, score: 1, metric: 'fidelity', message: 'Your circuit prepares the target state.',
    });
    show('/builder?challenge=bell-psi-plus');
    expect(await screen.findByRole('heading', { name: 'Prepare the Ψ⁺ Bell state' })).toBeInTheDocument();
    expect(screen.queryByRole('radio', { name: /^RY/ })).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Place gate on q0' }));
    await user.click(screen.getByRole('button', { name: 'Check my circuit' }));
    expect(await screen.findByText(/Challenge complete!/)).toBeInTheDocument();
    expect(api.checkBuildChallenge).toHaveBeenCalledWith('bell-psi-plus', { qubits: 2, gates: [{ name: 'H', qubits: [0] }] });
    expect(getLearningProgress().completedChallenges).toContain('bell-psi-plus');
  });
});
