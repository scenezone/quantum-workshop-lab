import axios from 'axios';
import type {
  ChatMessage,
  Experiment,
  ExperimentResult,
  HardwareStatus,
  JobStatusResponse,
  Lesson,
  PublicConfig,
  AssistantResponse,
  PracticeFeedback,
} from '../types/api';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL?.trim() || '',
  timeout: 30000,
});

export async function fetchLessons(): Promise<Lesson[]> {
  const { data } = await api.get('/api/lessons');
  return data.lessons;
}

export async function fetchLesson(lessonId: string): Promise<Lesson> {
  const { data } = await api.get(`/api/lessons/${lessonId}`);
  return data;
}

export async function checkPracticeAnswer(
  lessonId: string,
  attempt: { question_id: string; option_id?: string; answer?: string },
  signal?: AbortSignal,
): Promise<PracticeFeedback> {
  const { data } = await api.post(`/api/lessons/${encodeURIComponent(lessonId)}/practice/check`, attempt, { signal });
  return data;
}

export async function fetchExperiments(): Promise<Experiment[]> {
  const { data } = await api.get('/api/experiments');
  return data.experiments;
}

export async function simulateExperiment(
  experimentId: string,
  shots: number,
): Promise<ExperimentResult> {
  const { data } = await api.post('/api/experiments/simulate', {
    experiment_id: experimentId,
    shots,
  });
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
  const { data } = await api.get(`/api/experiments/jobs/${trackingId}`, { signal });
  return data;
}

export async function fetchHardwareStatus(): Promise<HardwareStatus> {
  const { data } = await api.get('/api/hardware/status');
  return data;
}

export async function sendAssistantMessage(
  messages: ChatMessage[],
  lessonId?: string,
  experimentId?: string,
  resultContext?: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<AssistantResponse> {
  const { data } = await api.post('/api/assistant/chat', {
    messages: messages.map(({ role, content }) => ({ role, content })),
    lesson_id: lessonId,
    experiment_id: experimentId,
    result_context: resultContext,
  }, { signal, timeout: 60000 });
  return data;
}

export async function submitFeedback(payload: {
  rating: number;
  clarity_rating: number;
  completed_workshop: boolean;
  comments?: string;
}): Promise<void> {
  await api.post('/api/feedback', payload);
}
export async function fetchPublicConfig(): Promise<PublicConfig> {
  const { data } = await api.get('/api/config/public');
  return data;
}
