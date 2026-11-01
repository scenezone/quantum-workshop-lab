import { useMutation, useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import ErrorMessage from '../components/ErrorMessage';
import MeasurementHistogram from '../components/MeasurementHistogram';
import ProbabilityComparison from '../components/ProbabilityComparison';
import { fetchPublicConfig, simulateCustomCircuit } from '../services/api';
import { deleteSavedCircuit, getSavedCircuits, saveCircuit } from '../services/circuitLibrary';
import type { CircuitGateName, CustomCircuitGate, ExperimentResult } from '../types/api';

const gateNames: CircuitGateName[] = ['H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ', 'CX', 'CZ', 'SWAP'];
const twoQubitGates = new Set<CircuitGateName>(['CX', 'CZ', 'SWAP']);
const rotations = new Set<CircuitGateName>(['RX', 'RY', 'RZ']);

interface CircuitDraft {
  qubits: number;
  gates: CustomCircuitGate[];
  shots: number;
  noise_profile: 'ideal' | 'low' | 'medium' | 'high';
}

const noiseProfiles = ['ideal', 'low', 'medium', 'high'] as const;

function initialDraft(): CircuitDraft {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get('circuit');
  if (raw) {
    try {
      const value = JSON.parse(raw) as CircuitDraft;
      if (Number.isInteger(value.qubits) && value.qubits >= 1 && value.qubits <= 3
        && Array.isArray(value.gates) && value.gates.length <= 30
        && Number.isInteger(value.shots) && value.shots >= 1 && value.shots <= 10000
        && noiseProfiles.includes(value.noise_profile)
        && value.gates.every((gate) => gateNames.includes(gate.name)
          && gate.qubits.every((qubit) => Number.isInteger(qubit) && qubit >= 0 && qubit < value.qubits))) {
        return value;
      }
    } catch {
      // An invalid shared draft starts with a clean circuit.
    }
  }
  return { qubits: 2, gates: [], shots: 512, noise_profile: 'ideal' };
}

function qiskitCode(qubits: number, gates: CustomCircuitGate[]): string {
  const lines = [`from qiskit import QuantumCircuit`, `qc = QuantumCircuit(${qubits})`];
  for (const gate of gates) {
    const args = gate.qubits.join(', ');
    if (rotations.has(gate.name)) lines.push(`qc.${gate.name.toLowerCase()}(${gate.angle}, ${args})`);
    else lines.push(`qc.${gate.name.toLowerCase()}(${args})`);
  }
  lines.push('qc.measure_all()', 'print(qc.draw())');
  return lines.join('\n');
}

function downloadCsv(result: ExperimentResult) {
  const outcomes = [...new Set([...Object.keys(result.counts), ...Object.keys(result.ideal_probabilities)])].sort();
  const rows = [
    ['outcome', 'count', 'observed_probability', 'ideal_probability'],
    ...outcomes.map((outcome) => [outcome, String(result.counts[outcome] ?? 0),
      String(result.observed_probabilities[outcome] ?? 0), String(result.ideal_probabilities[outcome] ?? 0)]),
  ];
  const csv = rows.map((row) => row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(',')).join('\n');
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  link.download = 'custom-circuit-results.csv';
  link.click();
  URL.revokeObjectURL(link.href);
}

export default function CircuitBuilder() {
  const initial = useMemo(initialDraft, []);
  const config = useQuery({ queryKey: ['public-config'], queryFn: fetchPublicConfig });
  const [qubits, setQubits] = useState(initial.qubits);
  const [gates, setGates] = useState(initial.gates);
  const [gateName, setGateName] = useState<CircuitGateName>('H');
  const [control, setControl] = useState(0);
  const [target, setTarget] = useState(1);
  const [angle, setAngle] = useState(Math.PI / 2);
  const [shots, setShots] = useState(initial.shots);
  const [noiseProfile, setNoiseProfile] = useState<NonNullable<ExperimentResult['noise_profile']>>(initial.noise_profile);
  const [shareUrl, setShareUrl] = useState('');
  const [notice, setNotice] = useState('');
  const [draftName, setDraftName] = useState('My quantum circuit');
  const [savedCircuits, setSavedCircuits] = useState(getSavedCircuits);
  const simulation = useMutation({ mutationFn: simulateCustomCircuit });
  const maxShots = config.data?.max_simulator_shots ?? 0;
  const shotOptions = [...new Set([128, 512, 1024, 2048, 4096, maxShots, config.data?.default_shots ?? 0])]
    .filter((value) => value >= 1 && value <= maxShots).sort((a, b) => a - b);
  const isTwoQubit = twoQubitGates.has(gateName);
  const validTarget = !isTwoQubit || control !== target;

  useEffect(() => {
    if (maxShots && shots > maxShots) setShots(config.data?.default_shots ?? maxShots);
  }, [config.data, maxShots, shots]);

  function changeQubitCount(value: number) {
    setQubits(value);
    setGates((current) => current.filter((gate) => gate.qubits.every((qubit) => qubit < value)));
    setControl((current) => Math.min(current, value - 1));
    setTarget(value > 1 ? 1 : 0);
  }

  function addGate() {
    if (gates.length >= 30 || !validTarget) return;
    const nextGate: CustomCircuitGate = {
      name: gateName,
      qubits: isTwoQubit ? [control, target] : [control],
      ...(rotations.has(gateName) ? { angle } : {}),
    };
    setGates((current) => [...current, nextGate]);
  }

  function createShareLink() {
    const url = new URL(window.location.href);
    url.searchParams.set('circuit', JSON.stringify({ qubits, gates, shots, noise_profile: noiseProfile }));
    setShareUrl(url.toString());
    setNotice('Share link is ready. It contains the circuit setup, not previous results.');
  }

  function saveCurrentCircuit() {
    const name = draftName.trim();
    if (!name) return;
    setSavedCircuits(saveCircuit({
      id: `${Date.now()}`,
      name,
      qubits,
      gates,
      shots,
      noise_profile: noiseProfile,
    }));
    setNotice('Circuit saved in this browser.');
  }

  function loadCircuit(circuit: ReturnType<typeof getSavedCircuits>[number]) {
    setQubits(circuit.qubits);
    setGates(circuit.gates);
    setShots(circuit.shots);
    setNoiseProfile(circuit.noise_profile);
    simulation.reset();
    setNotice(`Loaded “${circuit.name}”.`);
  }

  async function copyShareLink() {
    if (!shareUrl) createShareLink();
    const url = shareUrl || (() => {
      const next = new URL(window.location.href);
      next.searchParams.set('circuit', JSON.stringify({ qubits, gates, shots, noise_profile: noiseProfile }));
      return next.toString();
    })();
    try {
      await navigator.clipboard.writeText(url);
      setNotice('Experiment link copied.');
    } catch {
      setShareUrl(url);
      setNotice('Copy the link from the field below.');
    }
  }

  function downloadCode() {
    const code = qiskitCode(qubits, gates);
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([code], { type: 'text/x-python;charset=utf-8' }));
    link.download = 'quantum-workshop-circuit.py';
    link.click();
    URL.revokeObjectURL(link.href);
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-cyan-300">Simulator only</p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Circuit Builder</h1>
          <p className="mt-2 max-w-3xl text-slate-300">Arrange approved gates, simulate safely, and export the resulting Qiskit example.</p>
        </div>
        <Link to="/playground" className="btn-secondary">Open guided experiments</Link>
      </div>

      <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <div className="space-y-6">
          <section className="glass p-5">
            <h2 className="font-semibold">Circuit setup</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="text-sm">Qubits
                <select className="input mt-2" value={qubits} onChange={(event) => changeQubitCount(Number(event.target.value))}>
                  {[1, 2, 3].map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <label className="text-sm">Gate
                <select className="input mt-2" value={gateName} onChange={(event) => setGateName(event.target.value as CircuitGateName)}>
                  {gateNames.filter((name) => !twoQubitGates.has(name) || qubits > 1).map((name) => <option key={name}>{name}</option>)}
                </select>
              </label>
              <label className="text-sm">Qubit
                <select className="input mt-2" value={control} onChange={(event) => setControl(Number(event.target.value))}>
                  {Array.from({ length: qubits }, (_, index) => <option key={index} value={index}>q{index}</option>)}
                </select>
              </label>
              {isTwoQubit && <label className="text-sm">Target qubit
                <select className="input mt-2" value={target} onChange={(event) => setTarget(Number(event.target.value))}>
                  {Array.from({ length: qubits }, (_, index) => <option key={index} value={index}>q{index}</option>)}
                </select>
              </label>}
              {rotations.has(gateName) && <label className="text-sm">Rotation angle (radians)
                <input className="input mt-2" type="number" min={-6.283185} max={6.283185} step="0.1" value={angle}
                  onChange={(event) => setAngle(Number(event.target.value))} />
              </label>}
            </div>
            {!validTarget && <p role="alert" className="mt-3 text-sm text-amber-200">A two-qubit gate needs two different qubits.</p>}
            <button className="btn-primary mt-4" onClick={addGate} disabled={gates.length >= 30 || !validTarget}>Add gate ({gates.length}/30)</button>
          </section>

          <section className="glass p-5" aria-labelledby="gate-sequence-title">
            <div className="flex items-center justify-between gap-3">
              <h2 id="gate-sequence-title" className="font-semibold">Gate sequence</h2>
              <button className="text-sm text-rose-200 underline" onClick={() => setGates([])} disabled={!gates.length}>Clear circuit</button>
            </div>
            {gates.length ? <ol className="mt-4 space-y-2">
              {gates.map((gate, index) => <li key={`${index}-${gate.name}`} className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm">
                <span><span className="mr-2 font-mono text-cyan-200">{String(index + 1).padStart(2, '0')}</span>
                  <strong>{gate.name}</strong>{rotations.has(gate.name) && `(${gate.angle})`}
                  <span className="ml-2 text-slate-400">on {gate.qubits.map((qubit) => `q${qubit}`).join(', ')}</span></span>
                <button className="text-rose-200 underline" aria-label={`Remove gate ${index + 1}`} onClick={() => setGates((current) => current.filter((_, item) => item !== index))}>Remove</button>
              </li>)}
            </ol> : <p className="mt-3 text-sm text-slate-400">Add a gate to begin. Measurements are appended automatically when you run the circuit.</p>}
            <pre className="mt-4 overflow-x-auto rounded-lg bg-navy-950 p-4 text-xs text-slate-200"><code>{qiskitCode(qubits, gates)}</code></pre>
            <div className="mt-3 flex flex-wrap gap-3">
              <button className="btn-secondary text-sm" onClick={downloadCode}>Download Qiskit code</button>
              <button className="btn-secondary text-sm" onClick={createShareLink}>Create share link</button>
              <button className="btn-secondary text-sm" onClick={() => void copyShareLink()}>Copy link</button>
            </div>
            <div className="mt-5 border-t border-white/10 pt-4">
              <h3 className="text-sm font-semibold">Saved in this browser</h3>
              <form className="mt-3 flex flex-wrap gap-2" onSubmit={(event) => { event.preventDefault(); saveCurrentCircuit(); }}>
                <input className="input min-w-48 flex-1" aria-label="Saved circuit name" maxLength={40} value={draftName}
                  onChange={(event) => setDraftName(event.target.value)} />
                <button type="submit" className="btn-secondary text-sm" disabled={!draftName.trim()}>Save circuit</button>
              </form>
              {savedCircuits.length > 0 && <ul className="mt-3 space-y-2">
                {savedCircuits.map((circuit) => <li key={circuit.id} className="flex items-center justify-between gap-3 rounded-lg bg-white/5 px-3 py-2 text-sm">
                  <span className="min-w-0 truncate">{circuit.name} <span className="text-xs text-slate-400">· {circuit.qubits} qubits · {circuit.gates.length} gates</span></span>
                  <div className="flex shrink-0 gap-3">
                    <button type="button" className="text-cyan-200 underline" onClick={() => loadCircuit(circuit)}>Load</button>
                    <button type="button" className="text-rose-200 underline" aria-label={`Delete ${circuit.name}`}
                      onClick={() => setSavedCircuits(deleteSavedCircuit(circuit.id))}>Delete</button>
                  </div>
                </li>)}
              </ul>}
            </div>
            {shareUrl && <input className="input mt-3 text-xs" aria-label="Shareable circuit link" readOnly value={shareUrl} onFocus={(event) => event.currentTarget.select()} />}
            {notice && <p role="status" className="mt-2 text-xs text-slate-400">{notice}</p>}
          </section>
        </div>

        <div className="space-y-6">
          <section className="glass p-5">
            <h2 className="font-semibold">Run simulation</h2>
            {config.isLoading && <p role="status" className="mt-2 text-sm text-slate-400">Loading simulator limits…</p>}
            {config.isError && <div className="mt-3"><ErrorMessage message="Simulator settings could not be loaded. Please refresh and try again." /></div>}
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="text-sm">Shots
                <select className="input mt-2" value={shots} onChange={(event) => setShots(Number(event.target.value))}>
                  {shotOptions.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <label className="text-sm">Noise profile
                <select className="input mt-2" value={noiseProfile} onChange={(event) => setNoiseProfile(event.target.value as typeof noiseProfile)}>
                  <option value="ideal">Ideal</option><option value="low">Low</option>
                  <option value="medium">Medium</option><option value="high">High</option>
                </select>
              </label>
            </div>
            <button className="btn-primary mt-4" disabled={simulation.isPending || !config.data || shots > maxShots}
              onClick={() => simulation.mutate({ qubits, gates, shots, noise_profile: noiseProfile })}>
              {simulation.isPending ? 'Simulating…' : 'Run circuit'}
            </button>
            {simulation.isError && <div className="mt-4"><ErrorMessage message="The circuit could not be simulated. Check the gate sequence and try again." /></div>}
          </section>

          {simulation.data && <CircuitResults result={simulation.data} />}
        </div>
      </div>
    </div>
  );
}

function CircuitResults({ result }: { result: ExperimentResult }) {
  return (
    <section className="glass p-5" aria-label="Custom circuit results">
      <h2 className="font-semibold">Results · {result.shots} shots · {result.noise_profile} noise</h2>
      <p className="mt-2 text-sm text-slate-300">Observed counts are compared with the ideal state probabilities for this circuit.</p>
      <MeasurementHistogram counts={result.counts} />
      <ProbabilityComparison observed={result.observed_probabilities} ideal={result.ideal_probabilities} />
      <button className="btn-secondary mt-4 text-sm" onClick={() => downloadCsv(result)}>Download results CSV</button>
    </section>
  );
}
