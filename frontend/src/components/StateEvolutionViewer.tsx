import { useEffect, useState } from 'react';
import type { BlochVector, StateEvolutionStep } from '../types/api';

function BlochSphere({ vector }: { vector: BlochVector }) {
  const center = 100;
  const radius = 62;
  const x = center + (vector.x - vector.y) * radius * 0.52;
  const y = center - vector.z * radius * 0.78 + (vector.x + vector.y) * radius * 0.18;
  const description = `Qubit ${vector.qubit}: x ${vector.x.toFixed(2)}, y ${vector.y.toFixed(2)}, z ${vector.z.toFixed(2)}`;

  return (
    <figure className="rounded-xl border border-white/10 bg-navy-950/40 p-3">
      <svg viewBox="0 0 200 200" role="img" aria-label={description} className="mx-auto w-full max-w-56">
        <circle cx={center} cy={center} r={radius} fill="rgba(8,13,28,.7)" stroke="rgba(148,163,184,.55)" />
        <ellipse cx={center} cy={center} rx={radius} ry="20" fill="none" stroke="rgba(148,163,184,.3)" />
        <line x1={center} y1="25" x2={center} y2="175" stroke="rgba(148,163,184,.45)" strokeDasharray="3 4" />
        <line x1="30" y1={center} x2="170" y2={center} stroke="rgba(148,163,184,.45)" />
        <text x="95" y="24" fill="#67e8f9" fontSize="11">|0⟩</text>
        <text x="95" y="190" fill="#67e8f9" fontSize="11">|1⟩</text>
        <line x1={center} y1={center} x2={x} y2={y} stroke="#c084fc" strokeWidth="4" strokeLinecap="round" />
        <circle cx={x} cy={y} r="6" fill="#f8fafc" stroke="#c084fc" strokeWidth="3" />
        <text x="164" y="105" fill="#94a3b8" fontSize="10">x</text>
        <text x="103" y="45" fill="#94a3b8" fontSize="10">z</text>
      </svg>
      <figcaption className="text-center text-sm font-medium text-slate-200">Qubit {vector.qubit}</figcaption>
      <p className="mt-1 text-center font-mono text-xs text-slate-400">
        x {vector.x.toFixed(2)} · y {vector.y.toFixed(2)} · z {vector.z.toFixed(2)}
      </p>
    </figure>
  );
}

export default function StateEvolutionViewer({ steps }: { steps: StateEvolutionStep[] }) {
  const [stepIndex, setStepIndex] = useState(0);
  useEffect(() => setStepIndex(0), [steps]);
  const activeIndex = Math.min(stepIndex, Math.max(steps.length - 1, 0));
  const active = steps[activeIndex];
  if (!active) return null;

  return (
    <section className="glass p-5" aria-labelledby="state-evolution-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="state-evolution-title" className="font-semibold">State after each gate</h2>
          <p className="mt-1 text-xs text-slate-400">The Bloch vector shows each qubit’s reduced state. Entanglement can make an individual qubit look mixed.</p>
        </div>
        <span className="rounded-full border border-cyan-400/30 px-3 py-1 text-xs text-cyan-200">
          Step {activeIndex + 1} of {steps.length}
        </span>
      </div>
      <div className="mt-4 rounded-lg bg-white/5 p-4">
        <p className="font-semibold text-cyan-200">{active.gate}</p>
        <p className="mt-1 text-sm text-slate-300">{active.explanation}</p>
      </div>
      <input
        className="mt-5 w-full accent-cyan-400"
        type="range"
        min={0}
        max={steps.length - 1}
        value={activeIndex}
        aria-label="Circuit step"
        onChange={(event) => setStepIndex(Number(event.target.value))}
      />
      <div className="mt-3 flex justify-between gap-3">
        <button className="btn-secondary px-4 py-2 text-sm" disabled={activeIndex === 0}
          onClick={() => setStepIndex((value) => Math.max(0, value - 1))}>Previous gate</button>
        <button className="btn-secondary px-4 py-2 text-sm" disabled={activeIndex === steps.length - 1}
          onClick={() => setStepIndex((value) => Math.min(steps.length - 1, value + 1))}>Next gate</button>
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {active.qubits.map((vector) => <BlochSphere key={vector.qubit} vector={vector} />)}
      </div>
    </section>
  );
}
