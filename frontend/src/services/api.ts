import axios, { AxiosError, type AxiosResponse } from 'axios';
import type {
  AssistantMode,
  AssistantResponse,
  BuildChallenge,
  ChallengeCheckResult,
  ChatMessage,
  ChshResult,
  CustomCircuitDefinition,
  CustomCircuitInput,
  Experiment,
  ExperimentEvolution,
  ExperimentResult,
  FeedbackSummary,
  HardwareStatus,
  JobStatusResponse,
  Lesson,
  MeasurementBasis,
  NoiseProfile,
  PracticeFeedback,
  PublicConfig,
  SessionDashboard,
  SessionMembership,
  VqeHamiltonian,
  VqeResult,
  WorkshopSession,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim() || '';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

export async function fetchLessons(): Promise<Lesson[]> {
  const { data } = await api.get('/api/lessons');
  return data.lessons;
}

export async function fetchLesson(lessonId: string): Promise<Lesson> {
  const { data } = await api.get(`/api/lessons/${encodeURIComponent(lessonId)}`);
  return data;
}

export async function checkPracticeAnswer(
  lessonId: string,
  attempt: { question_id: string; option_id?: string; answer?: string },
  signal?: AbortSignal,
): Promise<PracticeFeedback> {
  const { data } = await api.post(`/api/lessons/${encodeURIComponent(lessonId)}/practice/check`, attempt, {
    signal, timeout: 45000,
  });
  return data;
}

export async function fetchExperiments(): Promise<Experiment[]> {
  const { data } = await api.get('/api/experiments');
  return data.experiments;
}

export async function fetchExperimentEvolution(experimentId: string): Promise<ExperimentEvolution> {
  const { data } = await api.get(`/api/experiments/${encodeURIComponent(experimentId)}/evolution`);
  return data;
}

export async function simulateExperiment(
  experimentId: string,
  shots: number,
  noiseProfile: NoiseProfile = 'ideal',
  measurementBases?: MeasurementBasis[],
): Promise<ExperimentResult> {
  const { data } = await api.post('/api/experiments/simulate', {
    experiment_id: experimentId,
    shots,
    noise_profile: noiseProfile,
    ...(measurementBases?.some((basis) => basis !== 'Z') ? { measurement_bases: measurementBases } : {}),
  });
  return data;
}

export async function simulateCustomCircuit(circuit: CustomCircuitInput): Promise<ExperimentResult> {
  const { data } = await api.post('/api/experiments/custom/simulate', circuit);
  return data;
}

export async function fetchCustomEvolution(circuit: CustomCircuitDefinition, signal?: AbortSignal): Promise<ExperimentEvolution> {
  const { data } = await api.post('/api/experiments/custom/evolution', circuit, { signal });
  return data;
}

export async function importQasm(source: string): Promise<CustomCircuitDefinition> {
  const { data } = await api.post('/api/experiments/custom/qasm', { source });
  return data;
}

export async function submitHardwareExperiment(
  experimentId: string,
  shots: number,
  idempotencyKey: string,
): Promise<{ tracking_id: string; status: string }> {
  const { data } = await api.post('/api/experiments/hardware', {
    experiment_id: experimentId,
    shots,
    idempotency_key: idempotencyKey,
  });
  return data;
}

export async function fetchJobStatus(trackingId: string, signal?: AbortSignal): Promise<JobStatusResponse> {
  const { data } = await api.get(`/api/experiments/jobs/${encodeURIComponent(trackingId)}`, { signal });
  return data;
}

export async function fetchHardwareStatus(): Promise<HardwareStatus> {
  const { data } = await api.get('/api/hardware/status');
  return data;
}

export async function fetchSavedHardwareResult(experimentId: string): Promise<ExperimentResult | null> {
  const { data } = await api.get(`/api/hardware/saved/${encodeURIComponent(experimentId)}`);
  return data;
}

export async function fetchBuildChallenges(): Promise<BuildChallenge[]> {
  const { data } = await api.get('/api/challenges');
  return data.challenges;
}

export async function checkBuildChallenge(
  challengeId: string,
  circuit: CustomCircuitDefinition,
): Promise<ChallengeCheckResult> {
  const { data } = await api.post(`/api/challenges/${encodeURIComponent(challengeId)}/check`, circuit);
  return data;
}

export async function runChsh(input: {
  shots: number; noise_profile: NoiseProfile; alice?: [number, number]; bob?: [number, number];
}): Promise<ChshResult> {
  const { data } = await api.post('/api/labs/chsh', input);
  return data;
}

export async function runVqe(input: {
  hamiltonian: VqeHamiltonian; iterations: number; learning_rate: number; shots: number;
  noise_profile: NoiseProfile; initial_parameters?: number[];
}): Promise<VqeResult> {
  const { data } = await api.post('/api/labs/vqe', input, { timeout: 90000 });
  return data;
}

export interface StreamHandlers {
  /** Called with the reply text received so far. */
  onDelta: (text: string) => void;
}

function chatBody(
  messages: ChatMessage[], lessonId?: string, experimentId?: string,
  resultContext?: Record<string, unknown>, mode: AssistantMode = 'explain',
) {
  return {
    messages: messages.map(({ role, content }) => ({ role, content })),
    lesson_id: lessonId,
    experiment_id: experimentId,
    result_context: resultContext,
    mode,
  };
}

/** Reads the backend's server-sent events and resolves with the complete reply. */
async function streamAssistantMessage(
  body: ReturnType<typeof chatBody>, signal: AbortSignal | undefined, handlers: StreamHandlers,
): Promise<AssistantResponse | null> {
  if (typeof fetch !== 'function' || typeof TextDecoder === 'undefined') return null;
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/api/assistant/chat/stream`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal,
    });
  } catch {
    if (signal?.aborted) throw new axios.CanceledError();
    return null; // Network failure before streaming: let the regular request decide.
  }
  if (response.status === 429) {
    throw new AxiosError('Too many requests', 'ERR_BAD_REQUEST', undefined, undefined,
      { status: 429, data: null, headers: {}, statusText: 'Too Many Requests', config: {} } as AxiosResponse);
  }
  if (!response.ok || !response.body) return null;

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let reply = '';
  let source: AssistantResponse['source'] = 'llm';
  let notice: string | null = null;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() ?? '';
      for (const event of events) {
        const line = event.split('\n').find((item) => item.startsWith('data:'));
        if (!line) continue;
        const payload = JSON.parse(line.slice(5)) as { type: string; text?: string; source?: 'llm' | 'fallback'; notice?: string | null };
        if (payload.type === 'meta') {
          source = payload.source ?? source;
          notice = payload.notice ?? null;
        } else if (payload.type === 'delta' && payload.text) {
          reply += payload.text;
          handlers.onDelta(reply);
        } else if (payload.type === 'done' && payload.notice) {
          notice = payload.notice;
        }
      }
    }
  } catch {
    if (signal?.aborted) throw new axios.CanceledError();
    if (!reply) return null;
    notice = 'The live response was interrupted. Ask again to continue.';
  }
  return reply.trim() ? { reply: reply.trim(), source, notice } : null;
}

export async function sendAssistantMessage(
  messages: ChatMessage[],
  lessonId?: string,
  experimentId?: string,
  resultContext?: Record<string, unknown>,
  signal?: AbortSignal,
  mode: AssistantMode = 'explain',
  stream?: StreamHandlers,
): Promise<AssistantResponse> {
  const body = chatBody(messages, lessonId, experimentId, resultContext, mode);
  if (stream) {
    const streamed = await streamAssistantMessage(body, signal, stream);
    if (streamed) return streamed;
  }
  const { data } = await api.post('/api/assistant/chat', body, { signal, timeout: 60000 });
  return data;
}

export async function submitFeedback(payload: {
  rating: number;
  clarity_rating: number;
  completed_workshop: boolean;
  comments?: string;
  session_code?: string;
}): Promise<void> {
  await api.post('/api/feedback', payload);
}

export async function fetchPublicConfig(): Promise<PublicConfig> {
  const { data } = await api.get('/api/config/public');
  return data;
}

export async function fetchSession(code: string): Promise<WorkshopSession> {
  const { data } = await api.get(`/api/sessions/${encodeURIComponent(code)}`);
  return data;
}

export async function joinSession(code: string, nickname: string): Promise<SessionMembership> {
  const { data } = await api.post(`/api/sessions/${encodeURIComponent(code)}/join`, { nickname });
  return data;
}

export async function syncSessionProgress(code: string, progress: {
  participant_id: string; participant_token: string; completed_lessons: string[];
  completed_challenges: string[]; practice_correct: number; practice_attempted: number;
}): Promise<void> {
  await api.put(`/api/sessions/${encodeURIComponent(code)}/progress`, progress);
}

function admin(token: string) {
  return { headers: { Authorization: `Bearer ${token}` } };
}

export async function verifyAdminToken(token: string): Promise<void> {
  await api.get('/api/admin/status', admin(token));
}

export async function createWorkshopSession(token: string, name: string): Promise<WorkshopSession> {
  const { data } = await api.post('/api/admin/sessions', { name }, admin(token));
  return data;
}

export async function fetchWorkshopSessions(token: string): Promise<WorkshopSession[]> {
  const { data } = await api.get('/api/admin/sessions', admin(token));
  return data.sessions;
}

export async function fetchSessionDashboard(token: string, code: string): Promise<SessionDashboard> {
  const { data } = await api.get(`/api/admin/sessions/${encodeURIComponent(code)}`, admin(token));
  return data;
}

export async function fetchFeedbackSummary(token: string): Promise<FeedbackSummary> {
  const { data } = await api.get('/api/admin/feedback', admin(token));
  return data;
}

export async function fetchFeedbackCsv(token: string, sessionCode?: string): Promise<string> {
  const { data } = await api.get('/api/admin/feedback/export', {
    ...admin(token), params: sessionCode ? { session_code: sessionCode } : undefined, responseType: 'text',
  });
  return data;
}
