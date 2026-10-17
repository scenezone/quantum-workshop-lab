import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface Props {
  observed: Record<string, number>;
  ideal: Record<string, number>;
}

export default function ProbabilityComparison({ observed, ideal }: Props) {
  const outcomes = Array.from(
    new Set([...Object.keys(ideal), ...Object.keys(observed)]),
  ).sort();

  const data = outcomes.map((outcome) => ({
    outcome,
    ideal: Number(((ideal[outcome] ?? 0) * 100).toFixed(2)),
    observed: Number(((observed[outcome] ?? 0) * 100).toFixed(2)),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
          <XAxis dataKey="outcome" stroke="#94a3b8" />
          <YAxis unit="%" stroke="#94a3b8" />
          <Tooltip />
          <Legend />
          <Bar dataKey="ideal" name="Ideal %" fill="#22d3ee" radius={[6, 6, 0, 0]} />
          <Bar dataKey="observed" name="Observed %" fill="#a855f7" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}