import axios from 'axios';
import type {
  ChatMessage,
  Experiment,
  ExperimentResult,
  HardwareStatus,
  JobStatusResponse,
  Lesson,
} from '../types/api';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
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
): Promise<{ tracking_id: string; status: string }> {
  const idempotencyKey =
    globalThis.crypto?.randomUUID?.() ??
    `${Date.now()}-${Math.random().toString(16).slice(2)}`;

  const { data } = await api.post('/api/experiments/hardware', {
    experiment_id: experimentId,
    shots,
    idempotency_key: idempotencyKey,
  });
  return data;
}

export async function fetchJobStatus(trackingId: string): Promise<JobStatusResponse> {
  const { data } = await api.get(`/api/experiments/jobs/${trackingId}`);
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
): Promise<{ reply: string; source: 'llm' | 'fallback' }> {
  const { data } = await api.post('/api/assistant/chat', {
    messages,
    lesson_id: lessonId,
    experiment_id: experimentId,
    result_context: resultContext,
  });
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