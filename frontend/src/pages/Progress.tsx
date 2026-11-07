import { useQuery } from '@tanstack/react-query';
import { Award, Download, Upload } from 'lucide-react';
import { useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import SessionJoinCard from '../components/SessionJoinCard';
import { fetchBuildChallenges, fetchLessons } from '../services/api';
import { computeBadges } from '../services/badges';
import { downloadText } from '../services/download';
import {
  exportProgress, importProgress, practiceSummary, resetProgress, useLearningProgress,
} from '../services/learningProgress';
import { EXPERIMENT_CHALLENGE_IDS } from '../types/catalog.generated';

export default function Progress() {
  const [params] = useSearchParams();
  const progress = useLearningProgress();
  const lessons = useQuery({ queryKey: ['lessons'], queryFn: fetchLessons });
  const challenges = useQuery({ queryKey: ['build-challenges'], queryFn: fetchBuildChallenges });
  const [notice, setNotice] = useState('');
  const [mode, setMode] = useState<'merge' | 'replace'>('merge');
  const fileInput = useRef<HTMLInputElement>(null);
  const practice = practiceSummary(progress);
  const lessonList = lessons.data ?? [];
  const buildIds = challenges.data?.map((item) => item.challenge_id) ?? [];
  const totalChallenges = EXPERIMENT_CHALLENGE_IDS.length + buildIds.length;
  const badges = computeBadges(progress, lessonList, buildIds);
  const earned = badges.filter((badge) => badge.earned).length;

  async function importFile(file: File) {
    try {
      importProgress(await file.text(), mode);
      setNotice(mode === 'merge' ? 'Progress merged into this browser.' : 'Progress replaced from the file.');
    } catch (cause) {
      setNotice(cause instanceof Error ? cause.message : 'The file could not be imported.');
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <p className="text-sm font-semibold uppercase tracking-widest text-cyan-300">Saved in this browser</p>
      <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Your Progress</h1>

      <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ['Lessons completed', `${progress.completedLessons.length} / ${lessonList.length || 14}`],
          ['Challenges completed', `${progress.completedChallenges.length} / ${totalChallenges || '…'}`],
          ['Practice correct', `${practice.correct} / ${practice.attempted}`],
          ['Badges earned', `${earned} / ${badges.length}`],
        ].map(([label, value]) => (
          <div key={label} className="glass p-4">
            <dt className="text-xs text-slate-400">{label}</dt>
            <dd className="mt-1 text-2xl font-bold text-cyan-100">{value}</dd>
          </div>
        ))}
      </dl>

      <section className="mt-8" aria-labelledby="badges-title">
        <h2 id="badges-title" className="text-xl font-semibold">Badges</h2>
        <ul className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {badges.map((badge) => (
            <li key={badge.id} className={`glass flex gap-3 p-4 ${badge.earned ? '' : 'opacity-70'}`}>
              <Award className={`h-8 w-8 shrink-0 ${badge.earned ? 'text-amber-300' : 'text-slate-600'}`} aria-hidden="true" />
              <div>
                <p className="font-semibold">{badge.title} <span className="sr-only">{badge.earned ? '(earned)' : '(not yet earned)'}</span></p>
                <p className="text-sm text-slate-300">{badge.description}</p>
                <p className="mt-1 text-xs text-slate-400">{badge.earned ? 'Earned' : badge.progress}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <SessionJoinCard initialCode={params.get('session') ?? ''} />
        <section className="glass p-5" aria-labelledby="backup-title">
          <h2 id="backup-title" className="font-semibold">Back up or move your progress</h2>
          <p className="mt-2 text-sm text-slate-300">
            Progress is stored only in this browser. Export a file to keep a copy or continue on another device.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button type="button" className="btn-secondary text-sm"
              onClick={() => downloadText('quantum-workshop-progress.json', exportProgress(progress), 'application/json')}>
              <Download className="h-4 w-4" /> Export progress
            </button>
            <button type="button" className="btn-secondary text-sm" onClick={() => fileInput.current?.click()}>
              <Upload className="h-4 w-4" /> Import progress
            </button>
            <input ref={fileInput} type="file" accept="application/json,.json" className="sr-only" aria-label="Progress file"
              onChange={(event) => { const file = event.target.files?.[0]; if (file) void importFile(file); event.target.value = ''; }} />
          </div>
          <fieldset className="mt-3 text-sm">
            <legend className="text-slate-400">When importing</legend>
            <label className="mr-4 inline-flex items-center gap-2"><input type="radio" name="import-mode" checked={mode === 'merge'}
              onChange={() => setMode('merge')} className="accent-cyan-400" /> Merge with this browser</label>
            <label className="inline-flex items-center gap-2"><input type="radio" name="import-mode" checked={mode === 'replace'}
              onChange={() => setMode('replace')} className="accent-cyan-400" /> Replace this browser’s progress</label>
          </fieldset>
          <button type="button" className="mt-4 text-sm text-rose-200 underline" onClick={() => {
            if (window.confirm('Reset all lesson, challenge, and practice progress in this browser?')) {
              resetProgress();
              setNotice('Progress reset.');
            }
          }}>Reset progress</button>
          {notice && <p role="status" className="mt-3 text-sm text-slate-300">{notice}</p>}
        </section>
      </div>

      <div className="mt-8 flex flex-wrap gap-4 text-sm">
        <Link to="/learn" className="text-cyan-200 underline">Continue learning</Link>
        <Link to="/challenges" className="text-cyan-200 underline">Try a challenge</Link>
        <Link to="/jobs" className="text-cyan-200 underline">Your hardware jobs</Link>
        <Link to="/facilitator" className="text-slate-400 underline">Facilitator dashboard</Link>
      </div>
    </div>
  );
}
