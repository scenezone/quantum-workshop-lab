import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import type { ChatMessage } from '../types/api';

interface AssistantContextValue {
  messages: ChatMessage[];
  lessonId?: string;
  experimentId?: string;
  resultContext?: Record<string, unknown>;
  setLessonId: (id?: string) => void;
  setExperimentId: (id?: string) => void;
  setResultContext: (context?: Record<string, unknown>) => void;
  addMessage: (message: ChatMessage) => void;
  reset: () => void;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);

export function AssistantProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lessonId, setLessonId] = useState<string | undefined>();
  const [experimentId, setExperimentId] = useState<string | undefined>();
  const [resultContext, setResultContext] = useState<Record<string, unknown> | undefined>();

  const value = useMemo(
    () => ({
      messages,
      lessonId,
      experimentId,
      resultContext,
      setLessonId,
      setExperimentId,
      setResultContext,
      addMessage: (message: ChatMessage) =>
        setMessages((current) => [...current, message]),
      reset: () => {
        setMessages([]);
        setLessonId(undefined);
        setExperimentId(undefined);
        setResultContext(undefined);
      },
    }),
    [messages, lessonId, experimentId, resultContext],
  );

  return <AssistantContext.Provider value={value}>{children}</AssistantContext.Provider>;
}

export function useAssistant() {
  const context = useContext(AssistantContext);
  if (!context) throw new Error('useAssistant must be used inside AssistantProvider');
  return context;
}