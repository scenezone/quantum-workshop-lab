import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import axios from 'axios';
import { sendAssistantMessage } from '../services/api';
import type { AssistantMode, ChatMessage, Experiment, Lesson } from '../types/api';

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
  mode?: AssistantMode;
}

interface AssistantContextValue {
  messages: ChatMessage[];
  lessonId?: string;
  experimentId?: string;
  resultContext?: Record<string, unknown>;
  loading: boolean;
  error: string | null;
  studyContext?: StudyContext;
  pageContextAvailable: boolean;
  includePageContext: boolean;
  setStudyContext: (context: StudyContext) => void;
  setResultContext: (context?: Record<string, unknown>) => void;
  setIncludePageContext: (include: boolean) => void;
  addMessage: (message: ChatMessage) => void;
  sendMessage: (question: string, mode?: AssistantMode) => Promise<void>;
  introduceTopic: () => Promise<void>;
  retry: () => Promise<void>;
  reset: () => void;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);
const PAGE_CONTEXT_PREFERENCE_KEY = 'quantum-workshop-assistant-page-context-v1';
const CHAT_KEY = 'quantum-workshop-assistant-chat-v1';

interface StoredChat { topic?: string; messages: ChatMessage[] }

/** The conversation survives a page reload within this tab, but not a new tab. */
function readChat(): StoredChat {
  try {
    const value = JSON.parse(sessionStorage.getItem(CHAT_KEY) || 'null') as StoredChat | null;
    if (!value || !Array.isArray(value.messages)) return { messages: [] };
    return {
      topic: typeof value.topic === 'string' ? value.topic : undefined,
      messages: value.messages.filter((message) => (message.role === 'user' || message.role === 'assistant')
        && typeof message.content === 'string').slice(-30),
    };
  } catch {
    return { messages: [] };
  }
}

export function AssistantProvider({ children }: { children: ReactNode }) {
  const [stored] = useState(readChat);
  const [messages, setMessages] = useState<ChatMessage[]>(stored.messages);
  const [pageStudyContext, updateStudyContext] = useState<StudyContext>();
  const [includePageContext, updateIncludePageContext] = useState(() => {
    try {
      return window.localStorage.getItem(PAGE_CONTEXT_PREFERENCE_KEY) !== 'false';
    } catch {
      return true;
    }
  });
  const studyContext = includePageContext ? pageStudyContext : undefined;
  const lessonId = studyContext?.kind === 'lesson' ? studyContext.lesson.lesson_id : studyContext?.experiment.lesson_id;
  const experimentId = studyContext?.kind === 'experiment' ? studyContext.experiment.experiment_id : undefined;
  const [pageResultContext, updateResultContext] = useState<Record<string, unknown>>();
  const resultContext = includePageContext ? pageResultContext : undefined;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  const pendingRef = useRef<PendingRequest | null>(null);
  const selectedTopicRef = useRef<string | undefined>(stored.topic);
  const introducedTopicRef = useRef<string | undefined>(stored.messages.length ? stored.topic : undefined);

  useEffect(() => () => requestRef.current?.abort(), []);
  useEffect(() => {
    try {
      const finished = messages.filter((message) => !message.streaming);
      sessionStorage.setItem(CHAT_KEY, JSON.stringify({ topic: selectedTopicRef.current, messages: finished }));
    } catch {
      // The conversation still works when session storage is unavailable.
    }
  }, [messages]);
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
      let streaming = false;
      const response = await sendAssistantMessage(
        request.messages, request.lessonId, request.experimentId, request.resultContext, controller.signal, request.mode,
        {
          // Show the reply as it arrives; the final message replaces this partial one.
          onDelta: (text) => {
            if (requestRef.current !== controller) return;
            const partial: ChatMessage = { role: 'assistant', content: text, streaming: true };
            setMessages((current) => streaming ? [...current.slice(0, -1), partial] : [...current, partial]);
            streaming = true;
          },
        },
      );
      if (requestRef.current !== controller) return;
      if (typeof response.reply !== 'string' || !response.reply.trim()) throw new Error('Empty assistant response');
      const final: ChatMessage = {
        role: 'assistant', content: response.reply, source: response.source, notice: response.notice,
      };
      setMessages((current) => current[current.length - 1]?.streaming
        ? [...current.slice(0, -1), final] : [...current, final]);
      pendingRef.current = null;
    } catch (cause) {
      setMessages((current) => current.filter((message) => !message.streaming));
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

  const sendMessage = useCallback(async (question: string, mode: AssistantMode = 'explain') => {
    const content = question.trim();
    if (!content || requestRef.current) return;
    const userMessage: ChatMessage = { role: 'user', content: content.slice(0, 2000) };
    addMessage(userMessage);
    await runRequest({
      messages: [...messages, userMessage].slice(-8), lessonId, experimentId, resultContext, mode,
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
      updateResultContext(undefined);
      introducedTopicRef.current = undefined;
      selectedTopicRef.current = key;
    }
    updateStudyContext(context);
  }, [reset]);

  const setResultContext = useCallback((context?: Record<string, unknown>) => {
    updateResultContext(context);
  }, []);

  const setIncludePageContext = useCallback((include: boolean) => {
    if (includePageContext === include) return;
    updateIncludePageContext(include);
    try {
      window.localStorage.setItem(PAGE_CONTEXT_PREFERENCE_KEY, String(include));
    } catch {
      // Keep the preference for this session even when browser storage is unavailable.
    }
    introducedTopicRef.current = undefined;
    reset();
  }, [includePageContext, reset]);

  const value = useMemo(() => ({
    messages, lessonId, experimentId, resultContext, studyContext, pageContextAvailable: Boolean(pageStudyContext),
    includePageContext, loading, error, setStudyContext, setResultContext, setIncludePageContext,
    addMessage, sendMessage, introduceTopic, retry, reset,
  }), [messages, lessonId, experimentId, resultContext, studyContext, pageStudyContext, includePageContext, loading, error,
    setStudyContext, setResultContext, setIncludePageContext, addMessage, sendMessage, introduceTopic, retry, reset]);

  return <AssistantContext.Provider value={value}>{children}</AssistantContext.Provider>;
}

export function useAssistant() {
  const context = useContext(AssistantContext);
  if (!context) throw new Error('useAssistant must be used inside AssistantProvider');
  return context;
}
