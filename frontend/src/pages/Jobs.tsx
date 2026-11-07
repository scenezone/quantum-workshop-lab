import { useQueries, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { fetchExperiments, fetchJobStatus } from '../services/api';
import { removeHardwareHistory, useHardwareHistory } from '../services/jobHistory';
import { pollInterval } from '../hooks/useExperimentJob';

const TERMINAL = ['completed', 'failed', 'cancelled'];
const STATUS_STYLE: Record<string, string> = {
  completed: 'text-emerald-200', failed: 'text-rose-300', cancelled: 'text-slate-400',
  queued: 'text-amber-200', running: 'text-cyan-200', unknown: 'text-amber-200',
};

export default function Jobs() {
  const history = useHardwareHistory();
  const experiments = useQuery({ queryKey: ['experiments'], queryFn: fetchExperiments });
  const jobs = useQueries({
    queries: history.map((entry) => ({
      queryKey: ['hardware-job', entry.trackingId],
      queryFn: ({ signal }: { signal: AbortSignal }) => fetchJobStatus(entry.trackingId, signal),
      retry: false,
      refetchInterval: (query: { state: { data?: Awaited<ReturnType<typeof fetchJobStatus>>; dataUpdateCount: number } }) =>
        query.state.data && TERMINAL.includes(query.state.data.status) ? false
          : Math.max(30000, pollInterval(query.state.data, query.state.dataUpdateCount)),
    })),
  });
  const title = (id: string) => experiments.data?.find((item) => item.experiment_id === id)?.title ?? id.replace(/_/g, ' ');

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <p className="text-sm font-semibold uppercase tracking-widest text-cyan-300">IBM Quantum</p>
      <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Your Hardware Jobs</h1>
      <p className="mt-2 max-w-3xl text-slate-300">
        Jobs you submitted from this browser. Device metrics describe the circuit after it was compiled for the chosen
        processor: more depth and more two-qubit gates usually mean more noise.
      </p>
      {history.length === 0 ? <div className="glass mt-8 p-6 text-slate-300">
        No hardware jobs yet. <Link to="/playground" className="text-cyan-300 underline">Open the Playground</Link> to submit one when hardware is enabled.
      </div> : <div className="glass mt-8 overflow-x-auto p-2">
        <table className="w-full min-w-[48rem] text-left text-sm">
          <thead className="text-slate-400"><tr>
            <th className="p-3">Experiment</th><th className="p-3">Submitted</th><th className="p-3">Status</th>
            <th className="p-3">Device</th><th className="p-3">Depth</th><th className="p-3">2-qubit gates</th>
            <th className="p-3">Top outcome</th><th className="p-3"><span className="sr-only">Actions</span></th>
          </tr></thead>
          <tbody>{history.map((entry, index) => {
            const job = jobs[index];
            const expired = axios.isAxiosError(job.error) && job.error.response?.status === 404;
            const data = job.data;
            const top = data?.counts ? Object.entries(data.counts).sort((a, b) => b[1] - a[1])[0] : undefined;
            return <tr key={entry.trackingId} className="border-t border-white/10">
              <td className="p-3 font-medium">{title(entry.experimentId)} <span className="block text-xs text-slate-400">{entry.shots} shots</span></td>
              <td className="p-3 text-slate-300">{new Date(entry.submittedAt).toLocaleString()}</td>
              <td className={`p-3 capitalize ${STATUS_STYLE[data?.status ?? ''] ?? 'text-slate-400'}`}>
                {expired ? 'Expired' : job.isLoading ? 'Loading…' : job.isError ? 'Unavailable' : data?.status}
              </td>
              <td className="p-3">{data?.backend_name ?? '—'}</td>
              <td className="p-3">{data?.transpiled_depth ?? '—'}</td>
              <td className="p-3">{data?.two_qubit_gate_count ?? '—'}</td>
              <td className="p-3 font-mono">{top ? `${top[0]} (${((top[1] / data!.shots) * 100).toFixed(0)}%)` : '—'}</td>
              <td className="p-3">
                <div className="flex gap-3">
                  <Link className="text-cyan-300 underline" to={`/playground?experiment=${entry.experimentId}`}>Open</Link>
                  <button type="button" className="text-rose-200 underline" onClick={() => removeHardwareHistory(entry.trackingId)}
                    aria-label={`Remove ${title(entry.experimentId)} job from history`}>Remove</button>
                </div>
              </td>
            </tr>;
          })}</tbody>
        </table>
      </div>}
      <p className="mt-4 text-xs text-slate-400">Tracking IDs act like private links to each job; this list is stored only in this browser.</p>
    </div>
  );
}
