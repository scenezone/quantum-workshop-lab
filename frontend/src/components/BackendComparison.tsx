import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { ExperimentResult } from '../types/api';

interface Props {
  simulator: ExperimentResult;
  hardware: ExperimentResult;
}

function percentage(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

export default function BackendComparison({ simulator, hardware }: Props) {
  const outcomes = [...new Set([
    ...Object.keys(simulator.observed_probabilities),
    ...Object.keys(hardware.observed_probabilities),
  ])].sort();
  const data = outcomes.map((outcome) => ({
    outcome,
    simulator: (simulator.observed_probabilities[outcome] ?? 0) * 100,
    hardware: (hardware.observed_probabilities[outcome] ?? 0) * 100,
  }));
  const totalVariationDistance = outcomes.reduce((total, outcome) => total + Math.abs(
    (simulator.observed_probabilities[outcome] ?? 0) - (hardware.observed_probabilities[outcome] ?? 0),
  ), 0) / 2;

  return (
    <section className="glass p-5" aria-labelledby="backend-comparison-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="backend-comparison-title" className="font-semibold">Simulator vs IBM hardware</h2>
          <p className="mt-1 text-sm text-slate-300">Compare the measured outcome probabilities from both runs.</p>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-right">
          <p className="text-xs text-slate-400">Total variation distance</p>
          <p className="font-semibold text-cyan-200">{percentage(totalVariationDistance)}</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-cyan-400/20 bg-cyan-400/5 p-4">
          <p className="text-sm font-semibold text-cyan-200">Simulator · {simulator.backend_name ?? 'Qiskit Aer'}</p>
          <p className="mt-1 text-sm text-slate-300">{simulator.shots.toLocaleString()} shots
            {simulator.noise_profile ? ` · ${simulator.noise_profile} noise` : ''}</p>
        </div>
        <div className="rounded-xl border border-purple-400/20 bg-purple-400/5 p-4">
          <p className="text-sm font-semibold text-purple-200">IBM hardware · {hardware.backend_name ?? 'Backend name unavailable'}</p>
          <p className="mt-1 text-sm text-slate-300">{hardware.shots.toLocaleString()} shots</p>
        </div>
      </div>

      <div className="mt-4 h-72 w-full" role="img" aria-label="Grouped bar chart comparing simulator and IBM hardware outcome probabilities">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
            <XAxis dataKey="outcome" stroke="#94a3b8" />
            <YAxis unit="%" stroke="#94a3b8" />
            <Tooltip formatter={(value) => `${Number(value).toFixed(2)}%`} />
            <Legend />
            <Bar dataKey="simulator" name="Simulator" fill="#22d3ee" radius={[5, 5, 0, 0]} />
            <Bar dataKey="hardware" name="IBM hardware" fill="#a855f7" radius={[5, 5, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 overflow-x-auto">
        <table className="w-full min-w-[34rem] text-left text-sm">
          <caption className="sr-only">Measured probabilities and hardware-minus-simulator difference for each outcome</caption>
          <thead className="text-slate-400">
            <tr>
              <th scope="col" className="p-2">Outcome</th>
              <th scope="col" className="p-2">Simulator</th>
              <th scope="col" className="p-2">IBM hardware</th>
              <th scope="col" className="p-2">Difference</th>
            </tr>
          </thead>
          <tbody>{outcomes.map((outcome) => {
            const simulatorProbability = simulator.observed_probabilities[outcome] ?? 0;
            const hardwareProbability = hardware.observed_probabilities[outcome] ?? 0;
            const difference = (hardwareProbability - simulatorProbability) * 100;
            return <tr key={outcome} className="border-t border-white/10">
              <th scope="row" className="p-2 font-mono font-medium">{outcome}</th>
              <td className="p-2">{percentage(simulatorProbability)}</td>
              <td className="p-2">{percentage(hardwareProbability)}</td>
              <td className={`p-2 ${difference > 0 ? 'text-purple-200' : difference < 0 ? 'text-cyan-200' : 'text-slate-300'}`}>
                {difference > 0 ? '+' : ''}{difference.toFixed(2)} pp
              </td>
            </tr>;
          })}</tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-slate-400">Total variation distance is half the sum of the absolute probability differences. It ranges from 0% (identical distributions) to 100% (no overlap); shot counts and simulator noise can affect the comparison.</p>
    </section>
  );
}
