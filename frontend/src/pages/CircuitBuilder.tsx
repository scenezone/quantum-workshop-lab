import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowLeft, ArrowRight, Redo2, Trash2, Undo2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import AmplitudeTable from '../components/AmplitudeTable';
import ChallengePanel from '../components/builder/ChallengePanel';
import CodeExport from '../components/builder/CodeExport';
import GatePalette, { ParameterFields } from '../components/builder/GatePalette';
import {
  operandLabels, parameterNames, parameterText, parseParameters, type ParameterText,
} from '../components/builder/gateParameters';
import CircuitCanvas from '../components/CircuitCanvas';
import ErrorMessage from '../components/ErrorMessage';
import { MeasurementBasisPicker, NoiseProfileSelect } from '../components/ExecutionControls';
import MeasurementHistogram from '../components/MeasurementHistogram';
import ProbabilityComparison from '../components/ProbabilityComparison';
import ResultStatistics from '../components/ResultStatistics';
import StateEvolutionViewer from '../components/StateEvolutionViewer';
import { useDebouncedValue } from '../hooks/useDebouncedValue';
import {
  fetchBuildChallenges, fetchCustomEvolution, fetchPublicConfig, simulateCustomCircuit,
} from '../services/api';
import { gateLabel, gateSpec, isValidCircuitDraft, type CircuitDraft } from '../services/circuit';
import { deleteSavedCircuit, getSavedCircuits, saveCircuit, type SavedCircuit } from '../services/circuitLibrary';
import { downloadResultCsv } from '../services/download';
import { MAX_CUSTOM_GATES, MAX_CUSTOM_QUBITS } from '../types/catalog.generated';
import type {
  CircuitGateName, CustomCircuitDefinition, CustomCircuitGate, ExperimentResult, MeasurementBasis, NoiseProfile,
} from '../types/api';

interface Circuit {
  qubits: number;
  gates: CustomCircuitGate[];
}

function initialDraft(): CircuitDraft {
  const raw = new URLSearchParams(window.location.search).get('circuit');
  if (raw) {
    try {
      const value: unknown = JSON.parse(raw);
      if (isValidCircuitDraft(value)) return value;
    } catch {
      // An invalid shared draft starts with a clean circuit.
    }
  }
  return { qubits: 2, gates: [], shots: 512, noise_profile: 'ideal' };
}

function defaultBases(qubits: number, bases?: MeasurementBasis[]): MeasurementBasis[] {
  return bases?.length === qubits ? bases : Array<MeasurementBasis>(qubits).fill('Z');
}

export default function CircuitBuilder() {
  const [params] = useSearchParams();
  const challengeId = params.get('challenge');
  const initial = useMemo(initialDraft, []);
  const config = useQuery({ queryKey: ['public-config'], queryFn: fetchPublicConfig });
  const challenges = useQuery({ queryKey: ['build-challenges'], queryFn: fetchBuildChallenges, enabled: Boolean(challengeId) });
  const challenge = challenges.data?.find((item) => item.challenge_id === challengeId);

  const [circuit, setCircuitState] = useState<Circuit>({ qubits: initial.qubits, gates: initial.gates });
  const [history, setHistory] = useState<{ past: Circuit[]; future: Circuit[] }>({ past: [], future: [] });
  const [gateName, setGateName] = useState<CircuitGateName>('H');
  const [operands, setOperands] = useState([0, 1, 2]);
  const [paramText, setParamText] = useState<ParameterText>(parameterText());
  const [pending, setPending] = useState<number[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [editText, setEditText] = useState<ParameterText>(parameterText());
  const [shots, setShots] = useState(initial.shots);
  const [noiseProfile, setNoiseProfile] = useState<NoiseProfile>(initial.noise_profile);
  const [bases, setBases] = useState<MeasurementBasis[]>(defaultBases(initial.qubits, initial.measurement_bases));
  const [shareUrl, setShareUrl] = useState('');
  const [notice, setNotice] = useState('');
  const [draftName, setDraftName] = useState('My quantum circuit');
  const [savedCircuits, setSavedCircuits] = useState(getSavedCircuits);
  const simulation = useMutation({ mutationFn: simulateCustomCircuit });

  const { qubits, gates } = circuit;
  const spec = gateSpec(gateName);
  const maxGates = challenge?.max_gates ?? MAX_CUSTOM_GATES;
  const parsedParams = parseParameters(gateName, paramText);
  const paramError = typeof parsedParams === 'string' ? parsedParams : '';
  const chosen = operands.slice(0, spec.qubits).map((qubit) => Math.min(qubit, qubits - 1));
  const operandError = new Set(chosen).size !== chosen.length ? 'Choose a different qubit for each operand.' : '';
  const maxShots = config.data?.max_simulator_shots ?? 0;
  const shotOptions = [...new Set([128, 512, 1024, 2048, 4096, maxShots, config.data?.default_shots ?? 0])]
    .filter((value) => value >= 1 && value <= maxShots).sort((a, b) => a - b);

  const evolutionInput = useDebouncedValue<CustomCircuitDefinition>(circuit, 450);
  const evolution = useQuery({
    queryKey: ['custom-evolution', evolutionInput],
    queryFn: ({ signal }) => fetchCustomEvolution(evolutionInput, signal),
    enabled: evolutionInput.gates.length > 0,
    staleTime: Infinity,
  });

  useEffect(() => {
    if (maxShots && shots > maxShots) setShots(config.data?.default_shots ?? maxShots);
  }, [config.data, maxShots, shots]);

  // A challenge fixes the qubit count and the available gates.
  useEffect(() => {
    if (!challenge) return;
    if (circuit.qubits !== challenge.qubits) {
      setCircuitState({ qubits: challenge.qubits, gates: [] });
      setBases(defaultBases(challenge.qubits));
    }
    if (!challenge.allowed_gates.includes(gateName)) setGateName(challenge.allowed_gates[0]);
  }, [challenge, circuit.qubits, gateName]);

  function commit(next: Circuit, message = '') {
    setHistory((current) => ({ past: [...current.past.slice(-49), circuit], future: [] }));
    setCircuitState(next);
    setPending([]);
    simulation.reset();
    setNotice(message);
  }

  function undo() {
    const previous = history.past[history.past.length - 1];
    if (!previous) return;
    setHistory({ past: history.past.slice(0, -1), future: [circuit, ...history.future] });
    setCircuitState(previous);
    setSelected(null);
    setBases((current) => defaultBases(previous.qubits, current));
  }

  function redo() {
    const next = history.future[0];
    if (!next) return;
    setHistory({ past: [...history.past, circuit], future: history.future.slice(1) });
    setCircuitState(next);
    setSelected(null);
    setBases((current) => defaultBases(next.qubits, current));
  }

  function chooseGate(name: CircuitGateName) {
    setGateName(name);
    setPending([]);
  }

  function append(operandQubits: number[]) {
    if (typeof parsedParams === 'string') {
      setNotice(parsedParams);
      return;
    }
    if (gates.length >= maxGates) {
      setNotice(`This circuit already has the maximum of ${maxGates} gates.`);
      return;
    }
    const gate: CustomCircuitGate = { name: gateName, qubits: operandQubits, ...parsedParams };
    commit({ qubits, gates: [...gates, gate] }, `Added ${gateLabel(gate)} on ${operandQubits.map((q) => `q${q}`).join(', ')}.`);
  }

  function placeOnWire(qubit: number) {
    if (spec.qubits === 1) return append([qubit]);
    if (pending.includes(qubit)) return setPending(pending.filter((item) => item !== qubit));
    const next = [...pending, qubit];
    if (next.length === spec.qubits) append(next);
    else {
      setPending(next);
      setNotice(`${operandLabels(gateName)[next.length - 1]}: q${qubit}. Now choose the ${operandLabels(gateName)[next.length].toLowerCase()}.`);
    }
  }

  function changeQubitCount(value: number) {
    commit({ qubits: value, gates: gates.filter((gate) => gate.qubits.every((qubit) => qubit < value)) });
    setBases((current) => defaultBases(value, current.slice(0, value).concat(Array(Math.max(0, value - current.length)).fill('Z'))));
    setSelected(null);
  }

  function selectGate(index: number) {
    setSelected(index === selected ? null : index);
    setEditText(parameterText(gates[index]));
  }

  function moveSelected(offset: number) {
    if (selected === null) return;
    const target = selected + offset;
    if (target < 0 || target >= gates.length) return;
    const next = [...gates];
    [next[selected], next[target]] = [next[target], next[selected]];
    commit({ qubits, gates: next });
    setSelected(target);
  }

  function deleteGate(index: number) {
    commit({ qubits, gates: gates.filter((_, item) => item !== index) }, `Removed gate ${index + 1}.`);
    setSelected(null);
  }

  function applyEdit() {
    if (selected === null) return;
    const values = parseParameters(gates[selected].name, editText);
    if (typeof values === 'string') return setNotice(values);
    commit({ qubits, gates: gates.map((gate, index) => index === selected ? { ...gate, ...values } : gate) },
      `Updated gate ${selected + 1}.`);
  }

  function draftUrl(): string {
    const url = new URL(window.location.href);
    url.searchParams.delete('challenge');
    const draft: CircuitDraft = { qubits, gates, shots, noise_profile: noiseProfile, measurement_bases: bases };
    url.searchParams.set('circuit', JSON.stringify(draft));
    return url.toString();
  }

  async function copyShareLink() {
    const url = draftUrl();
    setShareUrl(url);
    try {
      await navigator.clipboard.writeText(url);
      setNotice('Circuit link copied. It contains the circuit setup, not previous results.');
    } catch {
      setNotice('Copy the link from the field below.');
    }
  }

  function saveCurrentCircuit() {
    const name = draftName.trim();
    if (!name) return;
    setSavedCircuits(saveCircuit({
      id: `${Date.now()}`, name, qubits, gates, shots, noise_profile: noiseProfile, measurement_bases: bases,
    }));
    setNotice('Circuit saved in this browser.');
  }

  function loadCircuit(saved: SavedCircuit) {
    if (challenge && saved.qubits !== challenge.qubits) {
      setNotice(`This challenge needs a ${challenge.qubits}-qubit circuit.`);
      return;
    }
    commit({ qubits: saved.qubits, gates: saved.gates }, `Loaded “${saved.name}”.`);
    setShots(saved.shots);
    setNoiseProfile(saved.noise_profile);
    setBases(defaultBases(saved.qubits, saved.measurement_bases));
  }

  function importCircuit(imported: CustomCircuitDefinition) {
    if (challenge && imported.qubits !== challenge.qubits) {
      setNotice(`This challenge needs a ${challenge.qubits}-qubit circuit.`);
      return;
    }
    commit(imported, `Imported ${imported.gates.length} gates on ${imported.qubits} qubits.`);
    setBases(defaultBases(imported.qubits));
  }

  const selectedGate = selected !== null ? gates[selected] : undefined;

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-cyan-300">Simulator only</p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Circuit Builder</h1>
          <p className="mt-2 max-w-3xl text-slate-300">
            Pick a gate, then click a <span className="font-mono text-cyan-200">+</span> on a wire to place it. Click a placed gate to edit,
            move, or remove it. Watch each qubit’s state update, then simulate and export your circuit.
          </p>
        </div>
        <Link to="/playground" className="btn-secondary">Open guided experiments</Link>
      </div>

      {challengeId && challenges.isLoading && <p role="status" className="mt-6 text-sm text-slate-400">Loading challenge…</p>}
      {challengeId && challenges.isSuccess && !challenge && <div className="mt-6"><ErrorMessage message="This challenge was not found." /></div>}
      {challenge && <ChallengePanel challenge={challenge} gates={gates} />}

      <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <div className="min-w-0 space-y-6">
          <section className="glass p-5" aria-labelledby="editor-title">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 id="editor-title" className="font-semibold">Circuit editor</h2>
              <div className="flex items-center gap-2">
                <button type="button" className="btn-secondary px-3 py-2 text-sm" onClick={undo} disabled={!history.past.length} aria-label="Undo">
                  <Undo2 className="h-4 w-4" />
                </button>
                <button type="button" className="btn-secondary px-3 py-2 text-sm" onClick={redo} disabled={!history.future.length} aria-label="Redo">
                  <Redo2 className="h-4 w-4" />
                </button>
                <label className="flex items-center gap-2 text-sm">Qubits
                  <select className="input w-20" value={qubits} disabled={Boolean(challenge)}
                    onChange={(event) => changeQubitCount(Number(event.target.value))}>
                    {Array.from({ length: MAX_CUSTOM_QUBITS }, (_, index) => index + 1).map((value) => <option key={value} value={value}>{value}</option>)}
                  </select>
                </label>
              </div>
            </div>
            <div className="mt-4">
              <GatePalette active={gateName} onSelect={chooseGate} qubits={qubits} allowed={challenge?.allowed_gates} />
              <p className="mt-2 text-xs text-slate-400">{spec.label}{spec.qubits > 1 ? ` · choose ${spec.qubits} qubits in order: ${operandLabels(gateName).join(', ').toLowerCase()}` : ''}</p>
            </div>
            {parameterNames(gateName).length > 0 && <div className="mt-4">
              <ParameterFields name={gateName} text={paramText} onChange={setParamText} idPrefix="new-gate" />
            </div>}
            <div className="mt-4 max-w-full overflow-x-auto rounded-xl border border-white/10 bg-navy-950/40 p-2" role="region"
              aria-label="Scrollable circuit editor" tabIndex={0}>
              <CircuitCanvas qubits={qubits} gates={gates.map((gate) => ({ ...gate, label: gateLabel(gate) }))}
                ariaLabel="Interactive circuit editor" selectedIndex={selected} onSelectGate={selectGate}
                onAddSlot={gates.length < maxGates ? placeOnWire : undefined} pendingQubits={pending} measurementBases={bases} />
            </div>
            {pending.length > 0 && <button type="button" className="mt-2 text-sm text-slate-300 underline" onClick={() => setPending([])}>
              Cancel placing {gateName}
            </button>}

            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-cyan-300">Add a gate with menus instead</summary>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                {operandLabels(gateName).map((label, index) => (
                  <label key={label} className="text-sm">{label}
                    <select className="input mt-2" value={chosen[index]}
                      onChange={(event) => setOperands((current) => current.map((item, i) => i === index ? Number(event.target.value) : item))}>
                      {Array.from({ length: qubits }, (_, qubit) => <option key={qubit} value={qubit}>q{qubit}</option>)}
                    </select>
                  </label>
                ))}
              </div>
              {operandError && <p role="alert" className="mt-2 text-sm text-amber-200">{operandError}</p>}
              <button type="button" className="btn-primary mt-3 text-sm" onClick={() => append(chosen)}
                disabled={gates.length >= maxGates || Boolean(operandError) || Boolean(paramError)}>
                Add gate ({gates.length}/{maxGates})
              </button>
            </details>

            {selectedGate && <div className="mt-4 rounded-xl border border-cyan-400/30 bg-cyan-400/5 p-4" aria-label="Selected gate">
              <p className="text-sm font-semibold">Gate {selected! + 1}: {gateLabel(selectedGate)} on {selectedGate.qubits.map((q) => `q${q}`).join(', ')}</p>
              {parameterNames(selectedGate.name).length > 0 && <div className="mt-3">
                <ParameterFields name={selectedGate.name} text={editText} onChange={setEditText} idPrefix="edit-gate" />
                <button type="button" className="btn-secondary mt-2 text-sm" onClick={applyEdit}>Apply angles</button>
              </div>}
              <div className="mt-3 flex flex-wrap gap-2">
                <button type="button" className="btn-secondary px-3 py-2 text-sm" onClick={() => moveSelected(-1)} disabled={selected === 0}>
                  <ArrowLeft className="h-4 w-4" /> Earlier
                </button>
                <button type="button" className="btn-secondary px-3 py-2 text-sm" onClick={() => moveSelected(1)} disabled={selected === gates.length - 1}>
                  Later <ArrowRight className="h-4 w-4" />
                </button>
                <button type="button" className="btn-secondary px-3 py-2 text-sm text-rose-200" onClick={() => deleteGate(selected!)}>
                  <Trash2 className="h-4 w-4" /> Remove
                </button>
              </div>
            </div>}
            {notice && <p role="status" className="mt-3 text-sm text-slate-300">{notice}</p>}
          </section>

          {evolution.data && gates.length > 0 && <StateEvolutionViewer steps={evolution.data.steps} />}

          <section className="glass p-5" aria-labelledby="gate-sequence-title">
            <div className="flex items-center justify-between gap-3">
              <h2 id="gate-sequence-title" className="font-semibold">Gate sequence and code</h2>
              <button className="text-sm text-rose-200 underline" onClick={() => { commit({ qubits, gates: [] }, 'Circuit cleared.'); setSelected(null); }}
                disabled={!gates.length}>Clear circuit</button>
            </div>
            {gates.length ? <ol className="mt-4 space-y-2">
              {gates.map((gate, index) => <li key={`${index}-${gate.name}`} className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm">
                <span><span className="mr-2 font-mono text-cyan-200">{String(index + 1).padStart(2, '0')}</span>
                  <strong>{gateLabel(gate)}</strong>
                  <span className="ml-2 text-slate-400">on {gate.qubits.map((qubit) => `q${qubit}`).join(', ')}</span></span>
                <button className="text-rose-200 underline" aria-label={`Remove gate ${index + 1}`} onClick={() => deleteGate(index)}>Remove</button>
              </li>)}
            </ol> : <p className="mt-3 text-sm text-slate-400">Add a gate to begin. Measurements are appended automatically when you run the circuit.</p>}
            <CodeExport qubits={qubits} gates={gates} bases={bases} onImport={importCircuit} />
            <div className="mt-5 border-t border-white/10 pt-4">
              <h3 className="text-sm font-semibold">Save and share</h3>
              <form className="mt-3 flex flex-wrap gap-2" onSubmit={(event) => { event.preventDefault(); saveCurrentCircuit(); }}>
                <input className="input min-w-48 flex-1" aria-label="Saved circuit name" maxLength={40} value={draftName}
                  onChange={(event) => setDraftName(event.target.value)} />
                <button type="submit" className="btn-secondary text-sm" disabled={!draftName.trim()}>Save circuit</button>
                <button type="button" className="btn-secondary text-sm" onClick={() => void copyShareLink()}>Copy share link</button>
              </form>
              {shareUrl && <input className="input mt-3 text-xs" aria-label="Shareable circuit link" readOnly value={shareUrl} onFocus={(event) => event.currentTarget.select()} />}
              {savedCircuits.length > 0 && <ul className="mt-3 space-y-2">
                {savedCircuits.map((saved) => <li key={saved.id} className="flex items-center justify-between gap-3 rounded-lg bg-white/5 px-3 py-2 text-sm">
                  <span className="min-w-0 truncate">{saved.name} <span className="text-xs text-slate-400">· {saved.qubits} qubits · {saved.gates.length} gates</span></span>
                  <div className="flex shrink-0 gap-3">
                    <button type="button" className="text-cyan-200 underline" onClick={() => loadCircuit(saved)}>Load</button>
                    <button type="button" className="text-rose-200 underline" aria-label={`Delete ${saved.name}`}
                      onClick={() => setSavedCircuits(deleteSavedCircuit(saved.id))}>Delete</button>
                  </div>
                </li>)}
              </ul>}
            </div>
          </section>
        </div>

        <div className="min-w-0 space-y-6">
          <section className="glass p-5">
            <h2 className="font-semibold">Run simulation</h2>
            {config.isLoading && <p role="status" className="mt-2 text-sm text-slate-400">Loading simulator limits…</p>}
            {config.isError && <div className="mt-3"><ErrorMessage message="Simulator settings could not be loaded. Please refresh and try again." /></div>}
            <div className="mt-4 grid gap-4">
              <label className="text-sm">Shots
                <select className="input mt-2" value={shots} onChange={(event) => setShots(Number(event.target.value))}>
                  {shotOptions.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <NoiseProfileSelect value={noiseProfile} onChange={setNoiseProfile} profiles={config.data?.noise_profiles} label="Noise profile" />
              <MeasurementBasisPicker bases={bases} onChange={setBases} />
            </div>
            <button className="btn-primary mt-4" disabled={simulation.isPending || !config.data || shots > maxShots}
              onClick={() => simulation.mutate({ qubits, gates, shots, noise_profile: noiseProfile, measurement_bases: bases })}>
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
  const rotated = result.measurement_bases?.some((basis) => basis !== 'Z');
  return (
    <section className="glass p-5" aria-label="Custom circuit results">
      <h2 className="font-semibold">Results · {result.shots} shots · {result.backend_name ?? result.noise_profile}</h2>
      <p className="mt-2 text-sm text-slate-300">
        Observed counts are compared with the ideal probabilities for this circuit
        {rotated ? ` measured in the ${result.measurement_bases!.join('')} basis (q0 first)` : ''}.
      </p>
      <MeasurementHistogram counts={result.counts} />
      <ProbabilityComparison observed={result.observed_probabilities} ideal={result.ideal_probabilities} shots={result.shots} />
      <ResultStatistics counts={result.counts} observed={result.observed_probabilities} ideal={result.ideal_probabilities} shots={result.shots} />
      {result.amplitudes && <AmplitudeTable amplitudes={result.amplitudes} rotatedBasis={rotated} />}
      <button className="btn-secondary mt-4 text-sm" onClick={() => downloadResultCsv(result, 'custom-circuit-results.csv')}>Download results CSV</button>
    </section>
  );
}
