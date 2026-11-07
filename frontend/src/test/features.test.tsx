import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { sendAssistantMessage } from '../services/api';

function sse(events: object[], status = 200): Response {
  const body = events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join('');
  const bytes = new TextEncoder().encode(body);
  // Split mid-event to exercise buffering across chunks.
  const chunks = [bytes.slice(0, 20), bytes.slice(20)];
  const stream = new ReadableStream({
    start(controller) {
      chunks.forEach((chunk) => controller.enqueue(chunk));
      controller.close();
    },
  });
  return new Response(stream, { status, headers: { 'Content-Type': 'text/event-stream' } });
}

function wrap(node: React.ReactNode, path = '/') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}>{node}</MemoryRouter></QueryClientProvider>);
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('assistant streaming', () => {
  it('reports partial text and resolves with the full reply', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(sse([
      { type: 'meta', source: 'llm', notice: null },
      { type: 'delta', text: 'A Bell ' },
      { type: 'delta', text: 'state.' },
      { type: 'done', notice: null },
    ])));
    const seen: string[] = [];
    const reply = await sendAssistantMessage([{ role: 'user', content: 'Hi' }], undefined, undefined, undefined,
      undefined, 'explain', { onDelta: (text) => seen.push(text) });
    expect(seen).toEqual(['A Bell ', 'A Bell state.']);
    expect(reply).toEqual({ reply: 'A Bell state.', source: 'llm', notice: null });
  });

  it('surfaces rate limits as HTTP 429 errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 429 })));
    await expect(sendAssistantMessage([{ role: 'user', content: 'Hi' }], undefined, undefined, undefined, undefined,
      'explain', { onDelta: () => undefined })).rejects.toMatchObject({ response: { status: 429 } });
  });
});

describe('labs, facilitator, and progress pages', () => {
  it('runs the CHSH test and explains a violation', async () => {
    const api = await import('../services/api');
    vi.spyOn(api, 'fetchPublicConfig').mockResolvedValue({ hardware_enabled: false, max_simulator_shots: 4096, max_hardware_shots: 1, default_shots: 512 });
    vi.spyOn(api, 'runChsh').mockResolvedValue({
      shots: 1024, noise_profile: 'ideal', backend_name: 'Qiskit Aer', s_value: 2.79, s_standard_error: 0.04,
      ideal_s_value: 2.828, classical_bound: 2, quantum_bound: 2.828,
      settings: [{ alice_angle: 0, bob_angle: Math.PI / 4, counts: { '00': 900, '01': 124 }, correlation: 0.75, ideal_correlation: 0.707 }],
    });
    const { default: Labs } = await import('../pages/Labs');
    wrap(<Labs />, '/labs');
    await userEvent.setup().click(screen.getByRole('button', { name: /Run the Bell test/ }));
    expect(await screen.findByText(/S = 2.790/)).toBeInTheDocument();
    expect(screen.getByText(/violates the classical bound of 2 by 19.8 standard errors/)).toBeInTheDocument();
    expect(vi.mocked(api.runChsh).mock.calls[0][0]).toEqual(expect.objectContaining({ alice: [0, Math.PI / 2], bob: [Math.PI / 4, -Math.PI / 4] }));
  });

  it('signs a facilitator in, creates a session, and shows the dashboard', async () => {
    const api = await import('../services/api');
    const session = { code: 'QK7P2M', name: 'Friday lab', created_at: '2026-11-07T10:00:00Z', expires_at: '2026-11-10T10:00:00Z' };
    const feedback = { count: 0, average_rating: null, average_clarity: null, completion_rate: null, rating_distribution: {}, recent_comments: [] };
    vi.spyOn(api, 'verifyAdminToken').mockResolvedValue();
    vi.spyOn(api, 'fetchWorkshopSessions').mockResolvedValue([]);
    vi.spyOn(api, 'fetchFeedbackSummary').mockResolvedValue(feedback);
    vi.spyOn(api, 'createWorkshopSession').mockResolvedValue(session);
    vi.spyOn(api, 'fetchSessionDashboard').mockResolvedValue({
      session, participant_count: 1, challenge_completion: {}, feedback,
      participants: [{ participant_id: 'p1', nickname: 'Ada', completed_lessons: 3, completed_challenges: 1,
        practice_correct: 5, practice_attempted: 6, last_seen: '2026-11-07T10:05:00Z' }],
      lesson_completion: [{ lesson_id: 'superposition', title: 'Superposition', completed: 1 }],
    });
    const { default: Facilitator } = await import('../pages/Facilitator');
    const user = userEvent.setup();
    wrap(<Facilitator />, '/facilitator');
    await user.type(screen.getByLabelText('Facilitator token'), 'secret-token-123456');
    await user.click(screen.getByRole('button', { name: 'Open dashboard' }));
    await user.click(await screen.findByRole('button', { name: 'Create session code' }));
    expect(await screen.findByText('Ada')).toBeInTheDocument();
    expect(screen.getByText('QK7P2M', { selector: 'p' })).toBeInTheDocument();
    expect(screen.getByLabelText('Participant join link')).toHaveValue(`${window.location.origin}/progress?session=QK7P2M`);
    expect(sessionStorage.getItem('quantum-workshop-admin-token')).toBe('secret-token-123456');
  });

  it('joins a workshop session from the progress page', async () => {
    const api = await import('../services/api');
    vi.spyOn(api, 'fetchLessons').mockResolvedValue([]);
    vi.spyOn(api, 'fetchBuildChallenges').mockResolvedValue([]);
    vi.spyOn(api, 'joinSession').mockResolvedValue({
      session: { code: 'QK7P2M', name: 'Friday lab', created_at: '', expires_at: new Date(Date.now() + 3600000).toISOString() },
      participant_id: 'abcdef0123456789', participant_token: 'token-token-token-token',
    });
    const sync = vi.spyOn(api, 'syncSessionProgress').mockResolvedValue();
    const { default: Progress } = await import('../pages/Progress');
    const { setSessionMembership } = await import('../services/session');
    const user = userEvent.setup();
    wrap(<Progress />, '/progress?session=qk7p2m');
    expect(screen.getByLabelText('Session code')).toHaveValue('QK7P2M');
    await user.type(screen.getByLabelText('Nickname'), 'Ada');
    await user.click(screen.getByRole('button', { name: 'Join session' }));
    expect(await screen.findByText(/You joined/)).toHaveTextContent('Friday lab');
    await waitFor(() => expect(sync).toHaveBeenCalledWith('QK7P2M', expect.objectContaining({ participant_id: 'abcdef0123456789' })));
    expect(await screen.findByText('Progress shared with your facilitator')).toBeInTheDocument();
    setSessionMembership(null);
  });
});
