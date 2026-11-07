import { Bar, BarChart, CartesianGrid, ErrorBar, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { standardError } from '../services/stats';

interface Props {
  observed: Record<string, number>;
  ideal: Record<string, number>;
  /** When provided, observed bars show ±2 standard errors. */
  shots?: number;
}

export default function ProbabilityComparison({ observed, ideal, shots }: Props) {
  const outcomes = Array.from(
    new Set([...Object.keys(ideal), ...Object.keys(observed)]),
  ).sort();

  const data = outcomes.map((outcome) => {
    const value = observed[outcome] ?? 0;
    return {
      outcome,
      ideal: Number(((ideal[outcome] ?? 0) * 100).toFixed(2)),
      observed: Number((value * 100).toFixed(2)),
      error: shots ? Number((2 * standardError(value, shots) * 100).toFixed(2)) : 0,
    };
  });

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
          <XAxis dataKey="outcome" stroke="#94a3b8" />
          <YAxis unit="%" stroke="#94a3b8" />
          <Tooltip
            formatter={(value, name, item) => name === 'Observed %' && shots
              ? `${value}% ± ${(item.payload as { error: number }).error}%`
              : `${value}%`}
            contentStyle={{ backgroundColor: '#0a1024', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12 }}
          />
          <Legend />
          <Bar dataKey="ideal" name="Ideal %" fill="#22d3ee" radius={[6, 6, 0, 0]} />
          <Bar dataKey="observed" name="Observed %" fill="#a855f7" radius={[6, 6, 0, 0]}>
            {shots ? <ErrorBar dataKey="error" width={6} strokeWidth={1.5} stroke="#f5d0fe" /> : null}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
