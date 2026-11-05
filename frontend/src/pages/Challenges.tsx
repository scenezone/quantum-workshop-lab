import { Link } from 'react-router-dom';
import { challenges } from '../services/challenges';
import { getLearningProgress } from '../services/learningProgress';

export default function Challenges() {
  const completed = new Set(getLearningProgress().completedChallenges);
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <p className="text-sm font-semibold uppercase tracking-widest text-cyan-300">Practice by experimenting</p>
      <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Quantum Challenges</h1>
      <p className="mt-3 max-w-3xl text-slate-300">Each challenge checks an ideal simulator result. Use at least the requested shots and keep noise set to Ideal.</p>
      <div className="mt-8 grid gap-5 md:grid-cols-2">
        {challenges.map((challenge) => (
          <article key={challenge.id} className="glass p-5">
            <div className="flex items-start justify-between gap-4">
              <h2 className="text-lg font-semibold">{challenge.title}</h2>
              <span className={`rounded-full px-3 py-1 text-xs ${completed.has(challenge.id)
                ? 'bg-emerald-400/10 text-emerald-200' : 'bg-white/10 text-slate-300'}`}>
                {completed.has(challenge.id) ? 'Complete' : 'Not started'}
              </span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">{challenge.objective}</p>
            <p className="mt-3 text-xs text-slate-400">Minimum {challenge.minimumShots} shots · simulator only</p>
            <Link className="btn-primary mt-5 text-sm"
              to={`/playground?experiment=${encodeURIComponent(challenge.experimentId)}&challenge=${encodeURIComponent(challenge.id)}&shots=${challenge.minimumShots}&noise=ideal`}>
              Start challenge
            </Link>
          </article>
        ))}
      </div>
      <Link to="/learn" className="mt-7 inline-block text-sm text-cyan-200 underline">Back to lessons</Link>
    </div>
  );
}
