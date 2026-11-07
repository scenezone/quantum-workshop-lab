import { useMutation, useQuery } from '@tanstack/react-query';
import { Loader2, Play } from 'lucide-react';
import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Scatter, ComposedChart, Tooltip, XAxis, YAxis,
} from 'recharts';
import ErrorMessage from '../components/ErrorMessage';
import { NoiseProfileSelect } from '../components/ExecutionControls';
import { fetchPublicConfig, runChsh, runVqe } from '../services/api';
import { formatAngle, parseAngle } from '../services/circuit';
import type { ChshResult, NoiseProfile, NoiseProfileInfo, VqeHamiltonian, VqeResult } from '../types/api';

const tooltipStyle = { backgroundColor: '#0a1024', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12 };
const OPTIMAL = ['0', 'π/2', 'π/4', '-π/4'];

function ShotSelect({ value, onChange, max }: { value: number; onChange: (value: number) => void; max: number }) {
  const options = [256, 512, 1024, 2048, 4096, 8192].filter((item) => item <= max);
  return (
    <label className="text-sm">Shots per circuit
      <select className="input mt-2" value={value} onChange={(event) => onChange(Number(event.target.value))}>
        {options.map((item) => <option key={item} value={item}>{item}</option>)}
      </select>
    </label>
  );
}

function ChshLab({ maxShots, profiles }: { maxShots: number; profiles?: NoiseProfileInfo[] }) {
  const [shots, setShots] = useState(1024);
  const [noise, setNoise] = useState<NoiseProfile>('ideal');
  const [angles, setAngles] = useState(OPTIMAL);
  const parsed = angles.map(parseAngle);
  const valid = parsed.every((value) => value !== null && Math.abs(value) <= 2 * Math.PI);
  const run = useMutation({ mutationFn: runChsh });
  const labels = ['Alice setting a₀', 'Alice setting a₁', 'Bob setting b₀', 'Bob setting b₁'];

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
      <section className="glass p-5">
        <h2 className="text-lg font-semibold">Bell test (CHSH)</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-300">
          Alice and Bob share the Bell state (|00⟩ + |11⟩)/√2. Each chooses one of two measurement directions in the
          X–Z plane and records ±1. From four settings we compute
          {' '}<strong>S = E(a₀,b₀) + E(a₀,b₁) + E(a₁,b₀) − E(a₁,b₁)</strong>, where E is the correlation.
          Any local hidden-variable theory obeys |S| ≤ 2; quantum mechanics allows up to 2√2 ≈ 2.83.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {labels.map((label, index) => (
            <label key={label} className="text-sm">{label}
              <input className="input mt-2 font-mono" value={angles[index]} aria-invalid={parsed[index] === null}
                onChange={(event) => setAngles(angles.map((item, i) => i === index ? event.target.value : item))} />
            </label>
          ))}
        </div>
        <button type="button" className="mt-2 text-sm text-cyan-300 underline" onClick={() => setAngles(OPTIMAL)}>Use the optimal angles</button>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <ShotSelect value={shots} onChange={setShots} max={maxShots} />
          <NoiseProfileSelect value={noise} onChange={setNoise} profiles={profiles} />
        </div>
        <button className="btn-primary mt-5" disabled={!valid || run.isPending}
          onClick={() => run.mutate({
            shots, noise_profile: noise,
            alice: [parsed[0]!, parsed[1]!], bob: [parsed[2]!, parsed[3]!],
          })}>
          {run.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />} Run the Bell test
        </button>
        {!valid && <p role="alert" className="mt-2 text-sm text-amber-200">Enter each angle in radians, such as 0.785 or pi/4.</p>}
        {run.isError && <div className="mt-4"><ErrorMessage message="The Bell test could not be run. Please try again." /></div>}
      </section>
      {run.data && <ChshResults result={run.data} />}
    </div>
  );
}

function ChshResults({ result }: { result: ChshResult }) {
  const sigma = result.s_standard_error;
  const margin = sigma > 0 ? (Math.abs(result.s_value) - result.classical_bound) / sigma : 0;
  const position = (value: number) => `${Math.min(100, Math.max(0, (Math.abs(value) / 3) * 100))}%`;
  return (
    <section className="glass p-5" aria-label="Bell test results">
      <p className="text-sm text-slate-400">{result.backend_name} · {result.shots} shots per setting</p>
      <p className="mt-2 text-4xl font-black text-cyan-100">S = {result.s_value.toFixed(3)}
        <span className="ml-2 text-lg font-normal text-slate-400">± {sigma.toFixed(3)}</span></p>
      <p className={`mt-2 text-sm ${margin > 3 ? 'text-emerald-200' : 'text-amber-200'}`}>
        {margin > 3
          ? `This violates the classical bound of 2 by ${margin.toFixed(1)} standard errors: no local hidden-variable model can reproduce it.`
          : Math.abs(result.s_value) > result.classical_bound
            ? 'S is above 2, but not by enough standard errors to be convincing. Try more shots or less noise.'
            : 'S is within the classical bound. Noise or these measurement angles hide the quantum correlation.'}
      </p>
      <div className="relative mt-6 h-4 rounded-full bg-white/10" role="img"
        aria-label={`S value ${result.s_value.toFixed(2)} on a scale with the classical bound 2 and quantum bound 2.83`}>
        <div className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-cyan-500 to-purple-500" style={{ width: position(result.s_value) }} />
        <div className="absolute -top-1 h-6 w-0.5 bg-amber-300" style={{ left: position(result.classical_bound) }} />
        <div className="absolute -top-1 h-6 w-0.5 bg-emerald-300" style={{ left: position(result.quantum_bound) }} />
      </div>
      <div className="mt-2 flex justify-between text-xs text-slate-400">
        <span>0</span><span className="text-amber-200">classical limit 2</span><span className="text-emerald-200">quantum limit 2.83</span>
      </div>
      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[30rem] text-left text-sm">
          <caption className="sr-only">Correlation for each pair of measurement settings</caption>
          <thead className="text-slate-400"><tr>
            <th className="p-2">Alice</th><th className="p-2">Bob</th><th className="p-2">Counts</th>
            <th className="p-2">E measured</th><th className="p-2">E ideal</th>
          </tr></thead>
          <tbody>{result.settings.map((setting, index) => <tr key={index} className="border-t border-white/10">
            <td className="p-2 font-mono">{formatAngle(setting.alice_angle)}</td>
            <td className="p-2 font-mono">{formatAngle(setting.bob_angle)}</td>
            <td className="p-2 font-mono text-xs">{Object.entries(setting.counts).sort().map(([key, value]) => `${key}:${value}`).join(' ')}</td>
            <td className="p-2">{setting.correlation.toFixed(3)}</td>
            <td className="p-2">{setting.ideal_correlation.toFixed(3)}</td>
          </tr>)}</tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-slate-400">E = P(same) − P(different). Ideal S for these angles: {result.ideal_s_value.toFixed(3)}.</p>
    </section>
  );
}

function VqeLab({ maxShots, profiles }: { maxShots: number; profiles?: NoiseProfileInfo[] }) {
  const [hamiltonian, setHamiltonian] = useState<VqeHamiltonian>('zx');
  const [iterations, setIterations] = useState(20);
  const [rate, setRate] = useState(0.4);
  const [shots, setShots] = useState(1024);
  const [noise, setNoise] = useState<NoiseProfile>('ideal');
  const [initial, setInitial] = useState('');
  const run = useMutation({ mutationFn: runVqe });
  const parameters = hamiltonian === 'zx' ? 1 : 2;
  const initialValues = initial.trim() ? initial.split(',').map(parseAngle) : null;
  const initialValid = !initialValues || (initialValues.length === parameters && initialValues.every((value) => value !== null));

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
      <section className="glass p-5">
        <h2 className="text-lg font-semibold">Variational quantum eigensolver</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-300">
          A quantum circuit with adjustable RY angles prepares a trial state. Measuring in the Z and X bases estimates its
          energy ⟨H⟩. A classical optimizer then follows the parameter-shift gradient,
          {' '}∂E/∂θ = [E(θ + π/2) − E(θ − π/2)]/2, toward the lowest energy.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="text-sm">Problem
            <select className="input mt-2" value={hamiltonian} onChange={(event) => { setHamiltonian(event.target.value as VqeHamiltonian); setInitial(''); }}>
              <option value="zx">One qubit: H = Z + X</option>
              <option value="h2">Hydrogen molecule (2 qubits)</option>
            </select>
          </label>
          <label className="text-sm">Starting angles (optional)
            <input className="input mt-2 font-mono" value={initial} placeholder={parameters === 1 ? 'e.g. 2.6' : 'e.g. -0.5, 2.6'}
              aria-invalid={!initialValid} onChange={(event) => setInitial(event.target.value)} />
          </label>
          <label className="text-sm">Iterations: {iterations}
            <input type="range" className="mt-3 w-full accent-cyan-400" min={1} max={40} value={iterations}
              onChange={(event) => setIterations(Number(event.target.value))} />
          </label>
          <label className="text-sm">Learning rate: {rate.toFixed(2)}
            <input type="range" className="mt-3 w-full accent-cyan-400" min={0.05} max={1.5} step={0.05} value={rate}
              onChange={(event) => setRate(Number(event.target.value))} />
          </label>
          <ShotSelect value={shots} onChange={setShots} max={maxShots} />
          <NoiseProfileSelect value={noise} onChange={setNoise} profiles={profiles} />
        </div>
        <button className="btn-primary mt-5" disabled={run.isPending || !initialValid}
          onClick={() => run.mutate({
            hamiltonian, iterations, learning_rate: rate, shots, noise_profile: noise,
            ...(initialValues ? { initial_parameters: initialValues as number[] } : {}),
          })}>
          {run.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />} Run the optimizer
        </button>
        {!initialValid && <p role="alert" className="mt-2 text-sm text-amber-200">Enter {parameters} comma-separated angle(s), or leave the field empty.</p>}
        <p className="mt-3 text-xs text-slate-400">
          Try a starting angle of 0 for the hydrogen molecule: the optimizer crawls across a flat plateau, a common difficulty in real VQE.
        </p>
        {run.isError && <div className="mt-4"><ErrorMessage message="The optimizer could not be run. Please try again." /></div>}
      </section>
      {run.data && <VqeResults result={run.data} />}
    </div>
  );
}

function VqeResults({ result }: { result: VqeResult }) {
  const finalExact = result.trace[result.trace.length - 1].exact_energy;
  const error = finalExact - result.ground_energy;
  return (
    <section className="glass p-5" aria-label="Optimizer results">
      <p className="text-sm text-slate-400">{result.description}</p>
      <dl className="mt-4 grid gap-3 sm:grid-cols-3">
        <div><dt className="text-xs text-slate-400">Final estimate</dt><dd className="text-2xl font-bold text-cyan-100">{result.final_energy.toFixed(4)}</dd></div>
        <div><dt className="text-xs text-slate-400">Exact ground energy</dt><dd className="text-2xl font-bold text-emerald-200">{result.ground_energy.toFixed(4)}</dd></div>
        <div><dt className="text-xs text-slate-400">Gap at final angles</dt><dd className="text-2xl font-bold text-purple-200">{error.toFixed(4)}</dd></div>
      </dl>
      <p className="mt-2 text-xs text-slate-400">Final angles: {result.final_parameters.map((value) => value.toFixed(3)).join(', ')} rad · {result.backend_name}</p>
      <h3 className="mt-5 text-sm font-semibold">Energy at each iteration</h3>
      <div className="mt-2 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={result.trace}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
            <XAxis dataKey="iteration" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" domain={['auto', 'auto']} tickFormatter={(value: number) => value.toFixed(2)} />
            <Tooltip contentStyle={tooltipStyle} formatter={(value) => Number(value).toFixed(4)} />
            <Legend />
            <ReferenceLine y={result.ground_energy} stroke="#6ee7b7" strokeDasharray="5 4" label={{ value: 'ground', fill: '#6ee7b7', fontSize: 11 }} />
            <Line type="monotone" dataKey="energy" name="Measured estimate" stroke="#a855f7" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="exact_energy" name="Exact at these angles" stroke="#22d3ee" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {result.landscape.length > 0 && <>
        <h3 className="mt-5 text-sm font-semibold">Energy landscape E(θ) and the optimizer’s path</h3>
        <div className="mt-2 h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis type="number" dataKey="theta" domain={[-Math.PI, Math.PI]} stroke="#94a3b8"
                tickFormatter={(value: number) => value.toFixed(1)} allowDuplicatedCategory={false} />
              <YAxis stroke="#94a3b8" tickFormatter={(value: number) => value.toFixed(1)} />
              <Tooltip contentStyle={tooltipStyle} formatter={(value) => Number(value).toFixed(3)} />
              <Line data={result.landscape} type="monotone" dataKey="energy" name="E(θ)" stroke="#22d3ee" dot={false} strokeWidth={2} />
              <Scatter data={result.trace.map((step) => ({ theta: step.parameters[0], energy: step.exact_energy }))}
                dataKey="energy" name="Optimizer steps" fill="#f0abfc" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </>}
    </section>
  );
}

export default function Labs() {
  const [params, setParams] = useSearchParams();
  const lab = params.get('lab') === 'vqe' ? 'vqe' : 'chsh';
  const config = useQuery({ queryKey: ['public-config'], queryFn: fetchPublicConfig });
  const maxShots = Math.min(config.data?.max_simulator_shots ?? 4096, 8192);
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <p className="text-sm font-semibold uppercase tracking-widest text-cyan-300">Multi-circuit experiments</p>
      <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Quantum Labs</h1>
      <p className="mt-2 max-w-3xl text-slate-300">
        These labs run several circuits together: a Bell-inequality test of entanglement, and a variational algorithm that
        combines a quantum circuit with a classical optimizer.
      </p>
      <div role="tablist" aria-label="Labs" className="mt-6 flex flex-wrap gap-2">
        {([['chsh', 'Bell test (CHSH)'], ['vqe', 'Variational eigensolver']] as const).map(([id, label]) => (
          <button key={id} role="tab" aria-selected={lab === id} onClick={() => setParams({ lab: id })}
            className={`rounded-full border px-4 py-2 text-sm ${lab === id ? 'border-cyan-400 bg-cyan-400/10 text-cyan-200' : 'border-white/10 text-slate-300'}`}>
            {label}
          </button>
        ))}
      </div>
      <div className="mt-6" role="tabpanel">
        {lab === 'chsh'
          ? <ChshLab maxShots={maxShots} profiles={config.data?.noise_profiles} />
          : <VqeLab maxShots={maxShots} profiles={config.data?.noise_profiles} />}
      </div>
    </div>
  );
}
