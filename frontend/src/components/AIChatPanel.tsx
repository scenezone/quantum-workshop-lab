import { Bot, Loader2, Send } from 'lucide-react';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendAssistantMessage } from '../services/api';
import { useAssistant } from '../context/AssistantContext';
import type { ChatMessage } from '../types/api';

const suggestions = [
  'What is a qubit?',
  'What does the Hadamard gate do?',
  'Why are my results not exactly 50/50?',
  'What is quantum noise?',
];

export default function AIChatPanel({ compact = false }: { compact?: boolean }) {
  const { messages, addMessage, lessonId, experimentId, resultContext } = useAssistant();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(question: string) {
    if (!question.trim() || loading) return;

    const userMessage: ChatMessage = { role: 'user', content: question };
    const nextMessages = [...messages, userMessage];
    addMessage(userMessage);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await sendAssistantMessage(
        nextMessages.slice(-8),
        lessonId,
        experimentId,
        resultContext,
      );
      addMessage({ role: 'assistant', content: response.reply });
    } catch {
      setError('The AI assistant is unavailable right now. Please try again shortly.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className={`glass flex flex-col ${compact ? 'h-[520px]' : 'h-[680px]'} p-4`}>
      <header className="mb-3 flex items-center gap-2">
        <Bot className="h-5 w-5 text-cyan-400" />
        <h2 className="font-semibold">AI Quantum Assistant</h2>
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="rounded-xl bg-white/5 p-4 text-sm text-slate-300">
            Ask about qubits, gates, circuits, measurement results, or quantum noise.
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
              message.role === 'user'
                ? 'ml-auto bg-gradient-to-r from-cyan-500/20 to-purple-500/20'
                : 'bg-white/5'
            }`}
          >
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Loader2 className="h-4 w-4 animate-spin" /> Thinking…
          </div>
        )}

        {error && <p className="text-sm text-rose-300">{error}</p>}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => ask(suggestion)}
            className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300 hover:bg-white/10"
          >
            {suggestion}
          </button>
        ))}
      </div>

      <form
        className="mt-3 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          ask(input);
        }}
      >
        <input
          className="input"
          value={input}
          maxLength={2000}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask a quantum computing question"
          aria-label="Ask the AI quantum assistant"
        />
        <button className="btn-primary px-4" disabled={loading} aria-label="Send message">
          <Send className="h-4 w-4" />
        </button>
      </form>
    </section>
  );
}