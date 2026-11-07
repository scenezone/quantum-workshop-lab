import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import ErrorMessage from '../components/ErrorMessage';
import { fetchBuildChallenges } from '../services/api';
import { challenges } from '../services/challenges';
import { useLearningProgress } from '../services/learningProgress';

function Status({ done }: { done: boolean }) {
  return (
    <span className={`shrink-0 rounded-full px-3 py-1 text-xs ${done ? 'bg-emerald-400/10 text-emerald-200' : 'bg-white/10 text-slate-300'}`}>
      {done ? 'Complete' : 'Not started'}
    </span>
  );
}

export default function Challenges() {
  const completed = new Set(useLearningProgress().completedChallenges);
  const build = useQuery({ queryKey: ['build-challenges'], queryFn: fetchBuildChallenges });
  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <p className="text-sm font-semibold uppercase tracking-widest text-cyan-300">Practice by experimenting</p>
      <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Quantum Challenges</h1>
      <p className="mt-3 max-w-3xl text-slate-300">
        Run guided experiments to observe key behavior, then build circuits that prepare a target state.
        Build challenges are graded on the server by comparing your circuit’s ideal state with the goal.
      </p>

      <h2 className="mt-10 text-xl font-semibold">Build a state</h2>
      <p className="mt-1 text-sm text-slate-400">Design the circuit yourself in the builder, using only the allowed gates.</p>
      {build.isLoading && <p role="status" className="mt-4 text-sm text-slate-400">Loading build challenges…</p>}
      {build.isError && <div className="mt-4"><ErrorMessage message="Build challenges could not be loaded. Please refresh the page." /></div>}
      <div className="mt-5 grid gap-5 md:grid-cols-2">
        {build.data?.map((challenge) => (
          <article key={challenge.challenge_id} className="glass p-5">
            <div className="flex items-start justify-between gap-4">
              <h3 className="text-lg font-semibold">{challenge.title}</h3>
              <Status done={completed.has(challenge.challenge_id)} />
            </div>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">{challenge.objective}</p>
            <p className="mt-3 text-xs capitalize text-slate-400">
              {challenge.difficulty} · {challenge.qubits} qubit(s) · gates: {challenge.allowed_gates.join(', ')}
            </p>
            <Link className="btn-primary mt-5 text-sm" to={`/builder?challenge=${encodeURIComponent(challenge.challenge_id)}`}>
              Open in builder
            </Link>
          </article>
        ))}
      </div>

      <h2 className="mt-12 text-xl font-semibold">Observe in the Playground</h2>
      <p className="mt-1 text-sm text-slate-400">Each challenge checks an ideal simulator result. Use at least the requested shots and keep noise set to Ideal.</p>
      <div className="mt-5 grid gap-5 md:grid-cols-2">
        {challenges.map((challenge) => (
          <article key={challenge.id} className="glass p-5">
            <div className="flex items-start justify-between gap-4">
              <h3 className="text-lg font-semibold">{challenge.title}</h3>
              <Status done={completed.has(challenge.id)} />
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
      <div className="mt-8 flex flex-wrap gap-4 text-sm">
        <Link to="/progress" className="text-cyan-200 underline">See your progress and badges</Link>
        <Link to="/learn" className="text-cyan-200 underline">Back to lessons</Link>
      </div>
    </div>
  );
}
