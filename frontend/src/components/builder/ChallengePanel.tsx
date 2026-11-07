import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Trophy } from 'lucide-react';
import { Link } from 'react-router-dom';
import { checkBuildChallenge } from '../../services/api';
import { completeChallenge, useLearningProgress } from '../../services/learningProgress';
import type { BuildChallenge, CustomCircuitGate } from '../../types/api';

export default function ChallengePanel({ challenge, gates }: { challenge: BuildChallenge; gates: CustomCircuitGate[] }) {
  const progress = useLearningProgress();
  const check = useMutation({
    mutationFn: () => checkBuildChallenge(challenge.challenge_id, { qubits: challenge.qubits, gates }),
    onSuccess: (result) => { if (result.passed) completeChallenge(challenge.challenge_id); },
  });
  const done = progress.completedChallenges.includes(challenge.challenge_id);
  const error = check.error && axios.isAxiosError(check.error)
    ? String(check.error.response?.data?.detail ?? 'Your circuit could not be checked.')
    : check.error ? 'Your circuit could not be checked.' : '';

  return (
    <section className="glass mt-6 p-5" aria-label="Active build challenge">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-cyan-300">
            <Trophy className="h-4 w-4" aria-hidden="true" /> Build challenge · {challenge.difficulty}
          </p>
          <h2 className="mt-1 text-lg font-semibold">{challenge.title}</h2>
          <p className="mt-1 text-sm text-slate-300">{challenge.objective}</p>
          <p className="mt-2 text-xs text-slate-400">
            {challenge.qubits} qubit(s) · up to {challenge.max_gates} gates · allowed: {challenge.allowed_gates.join(', ')}
          </p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs ${done ? 'bg-emerald-400/10 text-emerald-200' : 'bg-white/10 text-slate-300'}`}>
          {done ? 'Complete' : 'In progress'}
        </span>
      </div>
      <details className="mt-3 text-sm">
        <summary className="cursor-pointer text-cyan-300">Show a hint</summary>
        <p className="mt-2 text-slate-300">{challenge.hint}</p>
      </details>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button type="button" className="btn-primary text-sm" disabled={check.isPending} onClick={() => check.mutate()}>
          {check.isPending ? 'Checking…' : 'Check my circuit'}
        </button>
        <Link to="/challenges" className="text-sm text-cyan-300 underline">All challenges</Link>
      </div>
      {check.data && <p role="status" className={`mt-3 text-sm ${check.data.passed ? 'text-emerald-200' : 'text-amber-200'}`}>
        {check.data.passed ? 'Challenge complete! ' : ''}{check.data.message}{' '}
        <span className="text-slate-400">
          ({check.data.metric === 'fidelity' ? 'state fidelity' : 'distribution match'} {(check.data.score * 100).toFixed(1)}%)
        </span>
      </p>}
      {error && <p role="alert" className="mt-3 text-sm text-rose-300">{error}</p>}
    </section>
  );
}
