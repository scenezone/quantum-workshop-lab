import { useMutation, useQuery } from '@tanstack/react-query';
import { CircuitBoard, Cpu, Loader2, Play, Server } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import AIChatPanel from '../components/AIChatPanel';
import AmplitudeTable from '../components/AmplitudeTable';
import BackendComparison from '../components/BackendComparison';
import CircuitDiagram from '../components/CircuitDiagram';
import ErrorMessage from '../components/ErrorMessage';
import { MeasurementBasisPicker, NoiseProfileSelect } from '../components/ExecutionControls';
import MeasurementHistogram from '../components/MeasurementHistogram';
import ProbabilityComparison from '../components/ProbabilityComparison';
import ResultStatistics from '../components/ResultStatistics';
import StateEvolutionViewer from '../components/StateEvolutionViewer';
import { useAssistant } from '../context/AssistantContext';
import { useHardwareRun } from '../hooks/useHardwareRun';
import {
  fetchExperimentEvolution,
  fetchExperiments,
  fetchPublicConfig,
  fetchSavedHardwareResult,
  simulateExperiment,
} from '../services/api';
import { evaluateChallenge, getChallenge } from '../services/challenges';
import { isMeasurementBasis, isNoiseProfile } from '../services/circuit';
import { downloadResultCsv } from '../services/download';
import { isExperimentId } from '../services/experimentUtils';
import { useHardwareSubmissions } from '../services/hardwareStorage';
import { completeChallenge, useLearningProgress } from '../services/learningProgress';
import type { Experiment, ExperimentId, ExperimentResult, MeasurementBasis, NoiseProfile } from '../types/api';

function measuredQubits(experiment: Experiment | undefined): number[] {
  if (!experiment) return [];
  return [...new Set(experiment.gates.filter((gate) => gate.name === 'Measure').flatMap((gate) => gate.qubits))].sort();
}

function parseBases(value: string | null, qubits: number): MeasurementBasis[] | null {
  const bases = value?.toUpperCase().split('') ?? [];
  return bases.length === qubits && bases.every(isMeasurementBasis) ? bases : null;
}

export default function Playground() {
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedId = searchParams.get('experiment');
  const challengeId = searchParams.get('challenge');
  const activeChallenge = getChallenge(challengeId);
  const requestedNoise = searchParams.get('noise');
  const experimentId: ExperimentId = isExperimentId(requestedId) ? requestedId : 'superposition';
  const currentExperiment = useRef(experimentId);
  currentExperiment.current = experimentId;
  const [shotsOverride, setShots] = useState<number | null>(() => {
    const requested = Number(searchParams.get('shots'));
    return Number.isInteger(requested) && requested > 0 ? requested : null;
  });
  const [noiseProfile, setNoiseProfile] = useState<NoiseProfile>(() =>
    isNoiseProfile(requestedNoise) ? requestedNoise : 'ideal',
  );
  const [basesByExperiment, setBasesByExperiment] = useState<Partial<Record<ExperimentId, MeasurementBasis[]>>>({});
  const [simulatorResult, setSimulatorResult] = useState<ExperimentResult | null>(null);
  const [shareUrl, setShareUrl] = useState('');
  const [shareNotice, setShareNotice] = useState('');
  const [challengeNotice, setChallengeNotice] = useState('');
  const progress = useLearningProgress();
  const [resultSource, setResultSource] = useState<'simulator' | 'hardware'>('hardware');
  const { setStudyContext, setResultContext } = useAssistant();
  const submissions = useHardwareSubmissions();

  const config = useQuery({ queryKey: ['public-config'], queryFn: fetchPublicConfig });
  const experimentsQuery = useQuery({ queryKey: ['experiments'], queryFn: fetchExperiments });
  const evolutionQuery = useQuery({
    queryKey: ['experiment-evolution', experimentId],
    queryFn: () => fetchExperimentEvolution(experimentId),
  });
  const savedHardwareQuery = useQuery({
    queryKey: ['saved-hardware-result', experimentId],
    queryFn: () => fetchSavedHardwareResult(experimentId),
  });
  const hardware = useHardwareRun(experimentId, {
    hardwareConfigured: config.data?.hardware_enabled,
    onSubmitted: (id) => { if (id === currentExperiment.current) setResultSource('hardware'); },
    onFailed: (id) => { if (id === currentExperiment.current) setResultSource('hardware'); },
  });
  const experiment = experimentsQuery.data?.find((item) => item.experiment_id === experimentId);
  const measured = useMemo(() => measuredQubits(experiment), [experiment]);
  const bases = basesByExperiment[experimentId]
    ?? (experiment && parseBases(searchParams.get('bases'), experiment.qubits))
    ?? Array<MeasurementBasis>(experiment?.qubits ?? 0).fill('Z');
  const rotated = bases.some((basis) => basis !== 'Z');
  const shots = hardware.pendingRetry ? hardware.saved!.shots : shotsOverride ?? config.data?.default_shots ?? 1024;

  const simulation = useMutation({
    mutationFn: (input: { experimentId: ExperimentId; shots: number; noiseProfile: NoiseProfile; bases: MeasurementBasis[] }) =>
      simulateExperiment(input.experimentId, input.shots, input.noiseProfile, input.bases),
    onSuccess: (result) => {
      setSimulatorResult(result);
      if (challengeId) {
        if (evaluateChallenge(challengeId, result)) {
          completeChallenge(challengeId);
          setChallengeNotice('Challenge complete! Your progress is saved in this browser.');
        } else {
          setChallengeNotice('Not quite yet. Check the challenge goal, shot count, noise, and measurement basis, then try again.');
        }
      }
      if (result.experiment_id === currentExperiment.current) setResultSource('simulator');
    },
  });
  const pending = simulation.isPending || hardware.mutation.isPending;
  const recordedHardwareResult = savedHardwareQuery.data?.experiment_id === experimentId ? savedHardwareQuery.data : null;
  const matchingSimulation = simulatorResult?.experiment_id === experimentId ? simulatorResult : null;
  const hardwareResult = hardware.result;
  const activeResult = resultSource === 'hardware'
    ? hardwareResult ?? recordedHardwareResult ?? matchingSimulation
    : matchingSimulation;
  const resultContext = useMemo(() => activeResult ? { ...activeResult } : undefined, [activeResult]);
  // Use primitive dependencies because the hardware result is reconstructed each render.
  const contextKey = JSON.stringify(resultContext);
  useEffect(() => {
    if (!experiment) return;
    setStudyContext({ kind: 'experiment', experiment });
    setResultContext(contextKey ? JSON.parse(contextKey) as Record<string, unknown> : undefined);
  }, [experiment, contextKey, setStudyContext, setResultContext]);

  async function shareSetup() {
    const url = new URL(window.location.href);
    url.searchParams.set('experiment', experimentId);
    url.searchParams.set('shots', String(shots));
    url.searchParams.set('noise', noiseProfile);
    if (rotated) url.searchParams.set('bases', bases.join(''));
    else url.searchParams.delete('bases');
    setShareUrl(url.toString());
    try {
      await navigator.clipboard.writeText(url.toString());
      setShareNotice('Experiment link copied.');
    } catch {
      setShareNotice('Copy the link from the field below.');
    }
  }

  const maxShots = config.data?.max_simulator_shots ?? 0;
  const maxHardwareShots = config.data?.max_hardware_shots;
  const shotOptions = [...new Set([128, 512, 1024, 2048, 4096, maxShots, maxHardwareShots ?? 0, config.data?.default_shots ?? 0, shots])]
    .filter((value) => value >= 1 && value <= Math.max(maxShots, maxHardwareShots ?? 0)).sort((a, b) => a - b);

  function chooseExperiment(id: ExperimentId) {
    setSearchParams({ experiment: id, ...(challengeId ? { challenge: challengeId } : {}) });
    setSimulatorResult(null);
    setResultSource(submissions[id]?.trackingId ? 'hardware' : 'simulator');
    simulation.reset();
    hardware.mutation.reset();
  }

  const hardwareEnabled = Boolean(hardware.status.data?.hardware_enabled);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">Quantum Playground</h1>
      <p className="mt-2 max-w-3xl text-slate-300">
        Move from foundational gates to phase kickback, GHZ states, quantum algorithms, and error correction.
        Inspect every gate, simulate the circuit, and connect amplitudes and phases to measured results.
      </p>
      <div className="mt-4 flex flex-wrap gap-3">
        <Link to="/builder" className="btn-secondary inline-flex text-sm">Create a custom circuit</Link>
        <Link to="/labs" className="btn-secondary inline-flex text-sm">Open the Bell test and VQE labs</Link>
      </div>
      {activeChallenge && <section className="glass mt-5 p-4" aria-label="Active challenge">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-cyan-300">Active challenge</p>
            <h2 className="mt-1 font-semibold">{activeChallenge.title}</h2>
            <p className="mt-1 text-sm text-slate-300">{activeChallenge.objective}</p>
          </div>
          <span className="text-sm text-emerald-200">{progress.completedChallenges.includes(activeChallenge.id) ? 'Completed' : `Minimum ${activeChallenge.minimumShots} shots`}</span>
        </div>
        {challengeNotice && <p role="status" className="mt-3 text-sm text-cyan-100">{challengeNotice}</p>}
      </section>}

      <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <div className="min-w-0 space-y-6">
          <section className="glass p-5">
            <h2 className="flex items-center gap-2 font-semibold">
              <CircuitBoard className="h-5 w-5 text-cyan-400" /> Experiment
            </h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {experimentsQuery.data?.map((item) => (
                <button key={item.experiment_id} disabled={pending} onClick={() => chooseExperiment(item.experiment_id)}
                  className={`rounded-xl border p-4 text-left transition ${experimentId === item.experiment_id
                    ? 'border-cyan-400/50 bg-cyan-400/10' : 'border-white/10 bg-white/5 hover:bg-white/10'}`}>
                  <p className="font-semibold">{item.title}</p>
                  <p className="mt-1 text-xs capitalize text-cyan-300">{item.difficulty}</p>
                  <p className="mt-1 text-xs text-slate-400">{item.qubits} qubit(s)</p>
                </button>
              ))}
            </div>
            {experiment && <p className="mt-4 text-sm text-slate-300">{experiment.description}</p>}
          </section>

          {(experimentsQuery.isLoading || config.isLoading) && <p role="status">Loading experiments...</p>}
          {(experimentsQuery.isError || config.isError) && <ErrorMessage message="Experiment settings could not be loaded. Please refresh to retry." />}
          {experiment && <>
            <CircuitDiagram experiment={experiment} measurementBases={bases} />
            {evolutionQuery.data && <StateEvolutionViewer steps={evolutionQuery.data.steps} />}
            <section className="glass p-5">
              <h2 className="font-semibold">Understand this experiment</h2>
              <p className="mt-3 text-sm leading-relaxed text-slate-300">{experiment.interpretation}</p>
              <div className="mt-4 flex flex-wrap gap-3">
                <Link to={`/learn?lesson=${encodeURIComponent(experiment.lesson_id)}`} className="btn-secondary text-sm">Study the theory</Link>
                {experiment.next_experiment && <button disabled={pending} className="btn-secondary text-sm"
                  onClick={() => chooseExperiment(experiment.next_experiment!)}>Next experiment</button>}
              </div>
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-cyan-300">View the Qiskit circuit code</summary>
                <pre className="mt-3 overflow-x-auto rounded-xl bg-navy-950 p-4 text-xs text-slate-200"><code>{experiment.qiskit_code}</code></pre>
              </details>
            </section>
          </>}

          <section className="glass p-5">
            <h2 className="flex items-center gap-2 font-semibold">
              <Server className="h-5 w-5 text-purple-400" /> Execution
            </h2>
            <div className="mt-4 grid gap-4">
              <label className="text-sm">
                Shots
                <select className="input mt-2" value={shots} disabled={pending || hardware.pendingRetry}
                  onChange={(event) => setShots(Number(event.target.value))}>
                  {shotOptions.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <NoiseProfileSelect value={noiseProfile} onChange={setNoiseProfile} profiles={config.data?.noise_profiles} />
              {experiment && <details open={rotated}>
                <summary className="cursor-pointer text-sm text-cyan-300">Measure in another basis (simulator)</summary>
                <div className="mt-3">
                  <MeasurementBasisPicker bases={bases} qubits={measured}
                    onChange={(next) => setBasesByExperiment((current) => ({ ...current, [experimentId]: next }))} />
                </div>
              </details>}

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <button className="btn-primary min-w-0 px-3 text-sm sm:text-base"
                  onClick={() => simulation.mutate({ experimentId, shots, noiseProfile, bases })}
                  disabled={pending || !config.data || shots > maxShots || experimentsQuery.isError}>
                  {simulation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  Run Simulator
                </button>
                <button className="btn-secondary min-w-0 px-3 text-sm sm:text-base" onClick={() => hardware.submit(shots)}
                  disabled={pending || !hardware.canSubmit(shots, maxHardwareShots)}>
                  <Cpu className="h-4 w-4" />
                  {hardware.pendingRetry ? 'Retry submission' : 'IBM Hardware'}
                </button>
              </div>
              {rotated && <p className="text-xs text-slate-400">IBM hardware runs always measure in the Z basis.</p>}
            </div>

            {!hardwareEnabled && <p className="mt-3 text-sm text-amber-300">
              Real quantum hardware is currently unavailable. You can continue with the simulator, including real-device noise models.
            </p>}
            {recordedHardwareResult && !hardwareResult && <p className="mt-3 text-sm text-amber-200" role="status">
              Showing the last saved IBM hardware run while a live result is unavailable. This is recorded data, not a new run.
            </p>}
            {simulation.isError && <ErrorMessage message="The simulator could not complete this experiment." />}
            {hardware.mutation.isError && <ErrorMessage message="Hardware submission failed or is unavailable." />}
            {hardware.expiredJob && <button className="btn-secondary mt-3" onClick={hardware.clearExpired}>Clear expired tracking ID</button>}
            {hardware.job.isError && <ErrorMessage message="The hardware job could not be loaded. Your submission is saved; refresh to retry." />}
            {hardware.status.isError && <ErrorMessage message="Hardware availability could not be checked." />}
            {hardware.pendingRetry && !hardware.mutation.isPending && <p className="mt-3 text-sm text-amber-300">Retry to recover this submission before starting another hardware job.</p>}
            {hardwareEnabled && hardware.status.data && <p className="mt-3 text-sm text-slate-300">
              {hardware.status.data.remaining_today} hardware submissions remaining today; {hardware.status.data.active_jobs}/{hardware.status.data.active_limit} active.{' '}
              <Link to="/jobs" className="text-cyan-300 underline">View your hardware jobs</Link>
            </p>}
            {hardware.trackingId && hardware.job.data && <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-4 text-sm">
              <p><strong>Status:</strong> {hardware.job.data.status}</p>
              {hardware.job.data.backend_name && <p><strong>Backend:</strong> {hardware.job.data.backend_name}</p>}
              {hardware.job.data.transpiled_depth != null && <p>
                <strong>Device circuit:</strong> depth {hardware.job.data.transpiled_depth} · {hardware.job.data.two_qubit_gate_count ?? 0} two-qubit gates
              </p>}
              {hardware.job.data.provider_job_id && <p className="break-all"><strong>IBM job ID:</strong> {hardware.job.data.provider_job_id}</p>}
              {hardware.job.data.error && <p className="text-rose-300">{hardware.job.data.error}</p>}
            </div>}
          </section>

          {activeResult && <section className="glass p-5">
            <h2 className="font-semibold">Measurement Results: {activeResult.backend === 'ibm_quantum' ? 'IBM hardware' : activeResult.backend === 'ibm_quantum_recorded' ? 'Recorded IBM hardware' : 'Simulator'}</h2>
            {activeResult.backend === 'ibm_quantum_recorded' && activeResult.recorded_at && (
              <p className="mt-2 text-xs text-amber-200">Saved from a completed hardware run on {new Date(activeResult.recorded_at).toLocaleString()}.</p>
            )}
            {activeResult.backend === 'aer_simulator' && activeResult.noise_profile && activeResult.noise_profile !== 'ideal' && (
              <p className="mt-2 text-sm text-amber-200">
                {activeResult.backend_name?.includes('snapshot') ? activeResult.backend_name.replace('Qiskit Aer · ', '') : `${activeResult.noise_profile} noise`} is applied to gates and readout. Compare the observed distribution with the ideal probabilities below.
              </p>
            )}
            {activeResult.measurement_bases?.some((basis) => basis !== 'Z') && <p className="mt-2 text-sm text-purple-200">
              Measured in the {activeResult.measurement_bases.join('')} basis (q0 first). Ideal probabilities are for this basis.
            </p>}
            {matchingSimulation && (hardwareResult || recordedHardwareResult) && <div className="my-3 flex flex-wrap gap-3">
              <button className="btn-secondary" onClick={() => setResultSource('simulator')} aria-pressed={resultSource === 'simulator'}>Simulator results</button>
              <button className="btn-secondary" onClick={() => setResultSource('hardware')} aria-pressed={resultSource === 'hardware'}>{hardwareResult ? 'Hardware results' : 'Recorded hardware results'}</button>
            </div>}
            <MeasurementHistogram counts={activeResult.counts} />
            <ProbabilityComparison observed={activeResult.observed_probabilities} ideal={activeResult.ideal_probabilities} shots={activeResult.shots} />
            <ResultStatistics counts={activeResult.counts} observed={activeResult.observed_probabilities}
              ideal={activeResult.ideal_probabilities} shots={activeResult.shots} />
            <div className="mt-4 flex flex-wrap gap-3">
              {activeResult.backend === 'aer_simulator' && <button className="btn-secondary text-sm" onClick={() => void shareSetup()}>
                Copy experiment link
              </button>}
              <button className="btn-secondary text-sm" onClick={() => downloadResultCsv(activeResult)}>Download results CSV</button>
            </div>
            {shareUrl && <div className="mt-3">
              <label className="block text-xs text-slate-400" htmlFor="share-experiment-url">Shareable setup link</label>
              <input id="share-experiment-url" className="input mt-1 text-xs" readOnly value={shareUrl} onFocus={(event) => event.currentTarget.select()} />
              <p role="status" className="mt-1 text-xs text-slate-400">{shareNotice}</p>
            </div>}
            {activeResult.amplitudes && <AmplitudeTable amplitudes={activeResult.amplitudes}
              open={experiment?.difficulty === 'advanced'} rotatedBasis={activeResult.measurement_bases?.some((basis) => basis !== 'Z')} />}
            <p className="mt-3 text-sm text-slate-300">
              Bitstrings are shown in Qiskit’s standard displayed convention: the leftmost bit is the
              highest classical-bit index.
            </p>
          </section>}
          {matchingSimulation && (hardwareResult || recordedHardwareResult) && (
            <BackendComparison simulator={matchingSimulation} hardware={hardwareResult ?? recordedHardwareResult!} />
          )}
        </div>

        <AIChatPanel compact />
      </div>
    </div>
  );
}
