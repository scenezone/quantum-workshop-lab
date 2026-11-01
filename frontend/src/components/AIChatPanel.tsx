import { Bot, Loader2, Send, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import Markdown from './Markdown';
import { useAssistant } from '../context/AssistantContext';
import type { AssistantMode } from '../types/api';

const suggestions = [
  'What is a qubit?',
  'What does the Hadamard gate do?',
  'Why are my results not exactly 50/50?',
  'What is quantum noise?',
];

export default function AIChatPanel({ compact = false, autoIntroduce = false }: { compact?: boolean; autoIntroduce?: boolean }) {
  const { messages, studyContext, resultContext, pageContextAvailable, includePageContext, setIncludePageContext,
    loading, error, sendMessage, introduceTopic, retry, reset } = useAssistant();
  const topic = studyContext?.kind === 'lesson' ? studyContext.lesson : studyContext?.experiment;
  const topicSuggestions = studyContext?.kind === 'experiment' ? [
    'Walk me through this circuit step by step.',
    'Why do we use these gates in this experiment?',
    resultContext ? 'Explain my recorded results and compare them with the ideal probabilities.' : 'What results should I expect from this experiment?',
  ] : studyContext ? [
    'Explain the main idea of this lesson with an example.',
    'Help me work through the equations in this lesson.',
    'Check my understanding of this topic with a question.',
  ] : suggestions;
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<AssistantMode>('explain');
  const conversation = useRef<HTMLDivElement>(null);
  const lastMessage = useRef<HTMLDivElement>(null);
  const previousMessageCount = useRef(0);
  const followLatest = useRef(true);
  useEffect(() => {
    if (autoIntroduce) void introduceTopic();
  }, [autoIntroduce, introduceTopic]);
  useEffect(() => {
    const log = conversation.current;
    if (!log) return;
    const incoming = messages.length > previousMessageCount.current;
    const latest = messages[messages.length - 1];
    if (messages.length === 0 && !loading && !error) {
      log.scrollTop = 0;
      followLatest.current = true;
    } else if (incoming && latest?.role === 'user') {
      log.scrollTop = log.scrollHeight;
      followLatest.current = true;
    } else if (incoming && latest?.role === 'assistant' && followLatest.current && lastMessage.current) {
      // Start long answers at their first line instead of skipping to their end.
      log.scrollTop += lastMessage.current.getBoundingClientRect().top - log.getBoundingClientRect().top - 12;
    } else if (!incoming && (loading || error) && followLatest.current) {
      log.scrollTop = log.scrollHeight;
    }
    previousMessageCount.current = messages.length;
  }, [messages, loading, error]);

  function ask(question: string) {
    if (!question.trim() || loading) return;
    setInput('');
    void sendMessage(question, mode);
  }

  return (
    <section className={`glass flex min-w-0 flex-col ${compact ? 'h-[600px]' : 'h-[min(800px,100dvh)] min-h-[520px]'} p-3 sm:p-5`}>
      <header className="mb-3 flex flex-wrap items-center gap-2">
        <Bot className="h-5 w-5 shrink-0 text-cyan-400" />
        <h2 className="font-semibold">Workshop Assistant</h2>
        {(messages.length > 0 || loading || error) && <button type="button" onClick={reset} className="ml-auto text-xs text-slate-300 hover:text-white">
          {loading ? 'Cancel and clear chat' : 'Clear chat'}
        </button>}
      </header>

      <fieldset className="mb-3">
        <legend className="mb-2 text-xs text-slate-400">Response style</legend>
        <div className="flex flex-wrap gap-2">
          {([
            ['explain', 'Explain'], ['hint', 'Give a hint'], ['quiz', 'Quiz me'],
          ] as const).map(([value, label]) => <button key={value} type="button" disabled={loading}
            aria-pressed={mode === value} onClick={() => setMode(value)}
            className={`rounded-full border px-3 py-1.5 text-xs transition ${mode === value
              ? 'border-cyan-400/50 bg-cyan-400/10 text-cyan-100' : 'border-white/10 text-slate-300 hover:bg-white/5'}`}>
            {label}
          </button>)}
        </div>
      </fieldset>

      <div ref={conversation} role="log" aria-label="Assistant conversation" aria-live="polite"
        onScroll={(event) => {
          const log = event.currentTarget;
          followLatest.current = log.scrollHeight - log.scrollTop - log.clientHeight < 80;
        }}
        className="min-h-0 min-w-0 flex-1 space-y-5 overflow-y-auto pr-1 sm:pr-2">
        {studyContext && topic && <div className="rounded-xl border border-cyan-400/20 bg-cyan-400/5 p-3 text-sm" role="region" aria-label="Current study topic">
          <div className="flex items-start justify-between gap-3">
            <p className="text-xs capitalize text-cyan-300">Current {studyContext.kind} · {topic.difficulty}</p>
            <button type="button" onClick={() => setIncludePageContext(false)}
              className="-mr-1 -mt-1 rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
              aria-label="Remove page context and start a fresh chat" title="Remove page context and start fresh">
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
          <h3 className="mt-1 font-semibold">{topic.title}</h3>
          <p className="mt-2 text-slate-300">{topic.description}</p>
          {studyContext.kind === 'lesson' && studyContext.lesson.learning_objectives.length > 0 && <ul className="mt-2 list-disc space-y-1 pl-4 text-slate-300">
            {studyContext.lesson.learning_objectives.slice(0, 3).map(objective => <li key={objective}>{objective}</li>)}
          </ul>}
          {studyContext.kind === 'experiment' && <p className="mt-2 text-slate-300">{studyContext.experiment.interpretation}</p>}
          {typeof resultContext?.shots === 'number' && <p className="mt-2 text-cyan-300">Recorded results: {resultContext.shots} shots · {resultContext.backend === 'ibm_quantum' ? 'IBM hardware' : 'Simulator'}</p>}
          <Link className="mt-2 inline-block text-cyan-300 underline" to={studyContext.kind === 'lesson'
            ? `/learn?lesson=${encodeURIComponent(studyContext.lesson.lesson_id)}`
            : `/playground?experiment=${encodeURIComponent(studyContext.experiment.experiment_id)}`}>
            Return to {studyContext.kind}
          </Link>
        </div>}
        {!includePageContext && <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm" role="status">
          <p className="text-slate-300">Page context is off. The assistant won’t receive lesson, experiment, or result details.</p>
          {pageContextAvailable && <button type="button" onClick={() => setIncludePageContext(true)}
            className="shrink-0 rounded-lg border border-cyan-400/30 px-3 py-1.5 text-xs text-cyan-200 hover:bg-cyan-400/10">
            Use page context
          </button>}
        </div>}
        {messages.length === 0 && !studyContext && <div className="rounded-xl bg-white/5 p-4 text-sm text-slate-300">
          Ask about qubits, gates, circuits, measurement results, or quantum noise.
        </div>}
        {messages.map((message, index) => (
          <div key={index} ref={index === messages.length - 1 ? lastMessage : undefined}
            className={`min-w-0 rounded-2xl p-4 sm:p-5 ${message.role === 'user'
              ? 'ml-auto max-w-[90%] bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-sm sm:max-w-[80%]'
              : 'w-full bg-white/5 text-[0.9375rem] sm:text-base'}`}>
            {message.role === 'assistant' && message.source && <p className={`mb-2 text-xs ${message.source === 'llm' ? 'text-cyan-300' : 'text-amber-300'}`}>
              {message.source === 'llm' ? 'AI answer' : 'Workshop guide (offline)'}
            </p>}
            {message.notice && <p className="mb-2 text-xs text-amber-200">{message.notice}</p>}
            <Markdown>{message.content}</Markdown>
          </div>
        ))}
        {loading && <div role="status" className="flex items-center gap-2 text-sm text-slate-400">
          <Loader2 className="h-4 w-4 animate-spin" /> Thinking...
        </div>}
        {error && <div role="alert" className="text-sm text-rose-300">
          <p>{error}</p>
          <button type="button" className="mt-2 underline" disabled={loading} onClick={() => void retry()}>Retry message</button>
        </div>}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {topicSuggestions.map((suggestion) => <button key={suggestion} type="button" disabled={loading} onClick={() => ask(suggestion)}
          className="max-w-full rounded-full border border-white/10 bg-white/5 px-3 py-2 text-left text-xs text-slate-300 hover:bg-white/10">
          {suggestion}
        </button>)}
      </div>

      <form className="mt-3 flex gap-2" onSubmit={(event) => { event.preventDefault(); ask(input); }}>
        <input className="input flex-1" value={input} maxLength={2000} onChange={(event) => setInput(event.target.value)}
          placeholder={mode === 'quiz' ? 'Answer or ask for a question' : mode === 'hint' ? 'Ask for a hint' : 'Ask a quantum computing question'}
          aria-label="Ask the workshop assistant" />
        <button className="btn-primary shrink-0 px-4" disabled={loading || !input.trim()} aria-label="Send message">
          <Send className="h-4 w-4" />
        </button>
      </form>
    </section>
  );
}
