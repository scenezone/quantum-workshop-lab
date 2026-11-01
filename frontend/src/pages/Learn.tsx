import { useQuery } from '@tanstack/react-query';
import { BookOpen, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Markdown from '../components/Markdown';
import LessonPractice from '../components/LessonPractice';
import { useAssistant } from '../context/AssistantContext';
import ErrorMessage from '../components/ErrorMessage';
import { fetchLessons } from '../services/api';
import type { Difficulty } from '../types/api';
import { completeLesson, getLearningProgress } from '../services/learningProgress';

export default function Learn() {
  const [params, setParams] = useSearchParams();
  const [level, setLevel] = useState<Difficulty | 'all'>('all');
  const [search, setSearch] = useState('');
  const [progress, setProgress] = useState(getLearningProgress);
  const lessonsQuery = useQuery({ queryKey: ['lessons'], queryFn: fetchLessons });
  const { setStudyContext } = useAssistant();
  const lessons = lessonsQuery.data ?? [];
  const filtered = lessons.filter((lesson) => (level === 'all' || lesson.difficulty === level) &&
    `${lesson.title} ${lesson.description} ${lesson.learning_objectives.join(' ')}`.toLowerCase().includes(search.toLowerCase()));
  const selected = filtered.find((lesson) => lesson.lesson_id === params.get('lesson')) ?? filtered[0];

  useEffect(() => {
    if (selected) setStudyContext({ kind: 'lesson', lesson: selected });
  }, [selected, setStudyContext]);

  function openLesson(id: string) {
    setLevel('all');
    setSearch('');
    setParams({ lesson: id });
  }

  if (lessonsQuery.isLoading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-cyan-400" /></div>;
  if (lessonsQuery.isError) return <ErrorMessage message="Lessons could not be loaded. Please refresh the page." />;

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">Learn Quantum</h1>
      <p className="mt-2 max-w-3xl text-slate-300">
        Build foundations in qubits and measurement, then work through complex amplitudes, oracle algorithms,
        Fourier transforms, teleportation, error correction, and variational methods.
      </p>
      <section className="glass mt-5 flex flex-wrap items-center justify-between gap-4 p-4" aria-label="Learning progress">
        <div className="min-w-48 flex-1">
          <div className="flex justify-between gap-3 text-sm">
            <span>Lessons completed</span>
            <span>{progress.completedLessons.length} / {lessons.length}</span>
          </div>
          <progress className="mt-2 h-2 w-full accent-cyan-400" max={Math.max(lessons.length, 1)}
            value={progress.completedLessons.length} aria-label="Lessons completed" />
        </div>
        <Link to="/challenges" className="btn-secondary text-sm">Try a quantum challenge</Link>
      </section>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        {(['all', 'beginner', 'intermediate', 'advanced'] as const).map((difficulty) => (
          <button key={difficulty} onClick={() => setLevel(difficulty)} aria-pressed={level === difficulty}
            className={`rounded-full border px-4 py-2 text-sm capitalize ${level === difficulty ? 'border-cyan-400 bg-cyan-400/10 text-cyan-200' : 'border-white/10 text-slate-300'}`}>
            {difficulty} ({lessons.filter((lesson) => difficulty === 'all' || lesson.difficulty === difficulty).length})
          </button>
        ))}
        <input className="input max-w-sm" aria-label="Search lessons" placeholder="Search concepts or learning objectives"
          value={search} onChange={(event) => setSearch(event.target.value)} />
      </div>
      <div className="mt-8 grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)] xl:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="min-w-0 space-y-3" aria-label="Learning path">
          {filtered.map((lesson) => (
            <button key={lesson.lesson_id} onClick={() => setParams({ lesson: lesson.lesson_id })}
              aria-current={selected?.lesson_id === lesson.lesson_id ? 'page' : undefined}
              className={`w-full rounded-xl border p-4 text-left ${selected?.lesson_id === lesson.lesson_id
                ? 'border-cyan-400/50 bg-cyan-400/10' : 'border-white/10 bg-white/5 hover:bg-white/10'}`}>
              <span className="mb-2 block text-xs capitalize text-cyan-300">{lesson.difficulty}</span>
              <p className="flex items-center gap-2 font-semibold"><BookOpen className="h-4 w-4 shrink-0 text-cyan-400" />{lesson.title}</p>
              <p className="mt-1 text-xs text-slate-400">{lesson.description}</p>
            </button>
          ))}
          {filtered.length === 0 && <p className="text-slate-300">No lessons match this search. Try another concept or level.</p>}
        </aside>
        {selected && <article className="glass min-w-0 p-4 sm:p-6">
          <p className="mb-2 text-sm capitalize text-cyan-300">{selected.difficulty} lesson</p>
          <h2 className="text-2xl font-bold">{selected.title}</h2>
          <div className="mt-4 rounded-xl bg-white/5 p-4 text-sm">
            <h3 className="font-semibold">What you will learn</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-300">
              {selected.learning_objectives.map((objective) => <li key={objective}>{objective}</li>)}
            </ul>
            {(selected.prerequisites?.length ?? 0) > 0 && <div className="mt-3">
              <p className="text-slate-400">Recommended background</p>
              <div className="mt-1 flex flex-wrap gap-3">{selected.prerequisites?.map((id) => (
                <button key={id} onClick={() => openLesson(id)} className="text-cyan-300 underline">
                  {lessons.find((lesson) => lesson.lesson_id === id)?.title ?? id}
                </button>
              ))}</div>
            </div>}
          </div>
          <div className="prose prose-invert mt-6 max-w-none overflow-x-auto"><Markdown>{selected.content}</Markdown></div>
          {(selected.practice_questions?.length ?? 0) > 0 && <LessonPractice key={selected.lesson_id}
            lessonId={selected.lesson_id} questions={selected.practice_questions!} />}
          <div className="mt-6 flex flex-wrap gap-3">
            {selected.related_experiments.map((id) => <Link key={id} to={`/playground?experiment=${encodeURIComponent(id)}`}
              className="btn-secondary text-sm">Try {id.replace(/_/g, ' ')}</Link>)}
            <Link to="/assistant" className="btn-primary text-sm">Discuss this lesson</Link>
            <button className="btn-secondary text-sm" aria-pressed={progress.completedLessons.includes(selected.lesson_id)}
              onClick={() => setProgress(completeLesson(selected.lesson_id))}>
              {progress.completedLessons.includes(selected.lesson_id) ? 'Lesson completed' : 'Mark lesson complete'}
            </button>
          </div>
          {(selected.references?.length ?? 0) > 0 && <div className="mt-6 border-t border-white/10 pt-4 text-sm">
            <h3 className="mb-2 font-semibold">Further reading</h3>
            {selected.references?.map((reference) => <a key={reference.url} href={reference.url} target="_blank"
              rel="noreferrer" className="block text-cyan-300 underline">{reference.title}</a>)}
          </div>}
        </article>}
      </div>
    </div>
  );
}
