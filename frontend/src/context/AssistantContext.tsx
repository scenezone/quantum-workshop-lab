import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import axios from 'axios';
import { sendAssistantMessage } from '../services/api';
import type { ChatMessage, Experiment, Lesson } from '../types/api';

type StudyContext = { kind: 'lesson'; lesson: Lesson } | { kind: 'experiment'; experiment: Experiment };

function topicKey(context?: StudyContext) {
  return context?.kind === 'lesson' ? `lesson:${context.lesson.lesson_id}`
    : context ? `experiment:${context.experiment.experiment_id}` : undefined;
}

interface PendingRequest {
  messages: ChatMessage[];
  lessonId?: string;
  experimentId?: string;
  resultContext?: Record<string, unknown>;
}

interface AssistantContextValue {
  messages: ChatMessage[];
  lessonId?: string;
  experimentId?: string;
  resultContext?: Record<string, unknown>;
  loading: boolean;
  error: string | null;
  studyContext?: StudyContext;
  setStudyContext: (context: StudyContext) => void;
  setResultContext: (context?: Record<string, unknown>) => void;
  addMessage: (message: ChatMessage) => void;
  sendMessage: (question: string) => Promise<void>;
  introduceTopic: () => Promise<void>;
  retry: () => Promise<void>;
  reset: () => void;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);

export function AssistantProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [studyContext, updateStudyContext] = useState<StudyContext>();
  const lessonId = studyContext?.kind === 'lesson' ? studyContext.lesson.lesson_id : studyContext?.experiment.lesson_id;
  const experimentId = studyContext?.kind === 'experiment' ? studyContext.experiment.experiment_id : undefined;
  const [resultContext, setResultContext] = useState<Record<string, unknown>>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  const pendingRef = useRef<PendingRequest | null>(null);
  const selectedTopicRef = useRef<string>();
  const introducedTopicRef = useRef<string>();

  useEffect(() => () => requestRef.current?.abort(), []);
  const addMessage = useCallback((message: ChatMessage) => {
    setMessages((current) => [...current, message]);
  }, []);

  const runRequest = useCallback(async (request: PendingRequest) => {
    if (requestRef.current) return;
    const controller = new AbortController();
    requestRef.current = controller;
    pendingRef.current = request;
    setLoading(true);
    setError(null);
    try {
      const response = await sendAssistantMessage(
        request.messages, request.lessonId, request.experimentId, request.resultContext, controller.signal,
      );
      if (requestRef.current !== controller) return;
      if (typeof response.reply !== 'string' || !response.reply.trim()) throw new Error('Empty assistant response');
      setMessages((current) => [...current, {
        role: 'assistant', content: response.reply, source: response.source, notice: response.notice,
      }]);
      pendingRef.current = null;
    } catch (cause) {
      if (requestRef.current !== controller || axios.isCancel(cause)) return;
      const limited = axios.isAxiosError(cause) && cause.response?.status === 429;
      setError(limited
        ? 'Too many requests. Wait a moment, then retry.'
        : 'The assistant could not be reached. Please try again.');
    } finally {
      if (requestRef.current === controller) {
        requestRef.current = null;
        setLoading(false);
      }
    }
  }, []);

  const sendMessage = useCallback(async (question: string) => {
    const content = question.trim();
    if (!content || requestRef.current) return;
    const userMessage: ChatMessage = { role: 'user', content: content.slice(0, 2000) };
    addMessage(userMessage);
    await runRequest({
      messages: [...messages, userMessage].slice(-8), lessonId, experimentId, resultContext,
    });
  }, [messages, lessonId, experimentId, resultContext, addMessage, runRequest]);

  const retry = useCallback(async () => {
    if (pendingRef.current) await runRequest(pendingRef.current);
  }, [runRequest]);

  const introduceTopic = useCallback(async () => {
    const key = topicKey(studyContext);
    if (!key || introducedTopicRef.current === key || messages.length || requestRef.current) return;
    introducedTopicRef.current = key;
    const question = studyContext?.kind === 'experiment'
      ? 'Give me an overview of my current experiment. Explain its purpose and circuit step by step, what to expect, and any recorded results. Suggest what to explore next.'
      : 'Give me an overview of my current lesson. Explain its main ideas at the appropriate difficulty, give a worked example, and suggest what to explore next.';
    await runRequest({ messages: [{ role: 'user', content: question }], lessonId, experimentId, resultContext });
  }, [studyContext, messages.length, lessonId, experimentId, resultContext, runRequest]);

  const reset = useCallback(() => {
    requestRef.current?.abort();
    requestRef.current = null;
    pendingRef.current = null;
    setMessages([]);
    setLoading(false);
    setError(null);
    // Keep the selected lesson/experiment when clearing the conversation.
  }, []);

  const setStudyContext = useCallback((context: StudyContext) => {
    const key = topicKey(context);
    if (selectedTopicRef.current !== key) {
      reset();
      setResultContext(undefined);
      introducedTopicRef.current = undefined;
      selectedTopicRef.current = key;
    }
    updateStudyContext(context);
  }, [reset]);

  const value = useMemo(() => ({
    messages, lessonId, experimentId, resultContext, studyContext, loading, error,
    setStudyContext, setResultContext, addMessage, sendMessage, introduceTopic, retry, reset,
  }), [messages, lessonId, experimentId, resultContext, studyContext, loading, error, setStudyContext, addMessage, sendMessage, introduceTopic, retry, reset]);

  return <AssistantContext.Provider value={value}>{children}</AssistantContext.Provider>;
}

export function useAssistant() {
  const context = useContext(AssistantContext);
  if (!context) throw new Error('useAssistant must be used inside AssistantProvider');
  return context;
}
