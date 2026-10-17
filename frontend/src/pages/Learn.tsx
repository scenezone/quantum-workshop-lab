import { useQuery } from '@tanstack/react-query';
import { BookOpen, Loader2 } from 'lucide-react';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Link } from 'react-router-dom';
import ErrorMessage from '../components/ErrorMessage';
import { fetchLessons } from '../services/api';

export default function Learn() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const lessonsQuery = useQuery({ queryKey: ['lessons'], queryFn: fetchLessons });

  if (lessonsQuery.isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
      </div>
    );
  }

  if (lessonsQuery.isError) {
    return <ErrorMessage message="Lessons could not be loaded. Please refresh the page." />;
  }

  const lessons = lessonsQuery.data ?? [];
  const selected = lessons.find((lesson) => lesson.lesson_id === selectedId) ?? lessons[0];

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">Learn Quantum</h1>
      <p className="mt-2 max-w-3xl text-slate-300">
        Start with qubits and superposition, then explore entanglement, gates, circuits, and real
        hardware noise.
      </p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[320px_1fr]">
        <aside className="space-y-3">
          {lessons.map((lesson) => (
            <button
              key={lesson.lesson_id}
              onClick={() => setSelectedId(lesson.lesson_id)}
              className={`w-full rounded-xl border p-4 text-left transition ${
                selected?.lesson_id === lesson.lesson_id
                  ? 'border-cyan-400/50 bg-cyan-400/10'
                  : 'border-white/10 bg-white/5 hover:bg-white/10'
              }`}
            >
              <p className="flex items-center gap-2 font-semibold">
                <BookOpen className="h-4 w-4 text-cyan-400" />
                {lesson.title}
              </p>
              <p className="mt-1 text-xs text-slate-400">{lesson.description}</p>
            </button>
          ))}
        </aside>

        {selected && (
          <article className="glass p-6">
            <h2 className="text-2xl font-bold">{selected.title}</h2>
            <div className="prose prose-invert mt-4 max-w-none">
              <ReactMarkdown>{selected.content}</ReactMarkdown>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              {selected.related_experiments.map((experimentId) => (
                <Link
                  key={experimentId}
                  to="/playground"
                  className="btn-secondary text-sm"
                >
                  Try related experiment
                </Link>
              ))}
            </div>
          </article>
        )}
      </div>
    </div>
  );
}