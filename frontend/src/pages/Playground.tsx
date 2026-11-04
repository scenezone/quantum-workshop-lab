import { useMutation, useQuery } from '@tanstack/react-query';
import { CircuitBoard, Cpu, Loader2, Play } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { saveSubmission, useHardwareSubmissions } from '../services/hardwareStorage';
import { createSubmissionKey, isExperimentId } from '../services/experimentUtils';
import AIChatPanel from '../components/AIChatPanel';
import BackendComparison from '../components/BackendComparison';
import CircuitDiagram from '../components/CircuitDiagram';
import ErrorMessage from '../components/ErrorMessage';
import MeasurementHistogram from '../components/MeasurementHistogram';
import ProbabilityComparison from '../components/ProbabilityComparison';
import StateEvolutionViewer from '../components/StateEvolutionViewer';
import { useAssistant } from '../context/AssistantContext';
import { useExperimentJob } from '../hooks/useExperimentJob';
import {
  fetchExperiments,
  fetchExperimentEvolution,
  fetchPublicConfig,
  fetchHardwareStatus,
  fetchSavedHardwareResult,
  simulateExperiment,
  submitHardwareExperiment,
} from '../services/api';
import type { ExperimentId, ExperimentResult } from '../types/api';
import { completeChallenge, getLearningProgress } from '../services/learningProgress';
import { evaluateChallenge, getChallenge } from '../services/challenges';

const NOISE_PROFILES = ['ideal', 'low', 'medium', 'high'] as const;
type NoiseProfile = typeof NOISE_PROFILES[number];

function isNoiseProfile(value: string | null): value is NoiseProfile {
  return NOISE_PROFILES.includes(value as NoiseProfile);
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
  const [simulatorResult, setSimulatorResult] = useState<ExperimentResult | null>(null);
  const [shareUrl, setShareUrl] = useState('');
  const [shareNotice, setShareNotice] = useState('');
  const [challengeNotice, setChallengeNotice] = useState('');
  const [challengeProgress, setChallengeProgress] = useState(getLearningProgress);
  const [resultSource, setResultSource] = useState<'simulator' | 'hardware'>('hardware');
  const submissions = useHardwareSubmissions();
  const saved = submissions[experimentId];
  const trackingId = saved?.trackingId ?? null;
  const { setStudyContext, setResultContext } = useAssistant();

  const config = useQuery({ queryKey: ['public-config'], queryFn: fetchPublicConfig });
  const shots = saved && !saved.trackingId ? saved.shots : shotsOverride ?? config.data?.default_shots ?? 1024;
  const experimentsQuery = useQuery({ queryKey: ['experiments'], queryFn: fetchExperiments });
  const evolutionQuery = useQuery({
    queryKey: ['experiment-evolution', experimentId],
    queryFn: () => fetchExperimentEvolution(experimentId),
  });
  const hardwareStatusQuery = useQuery({
    queryKey: ['hardware-status'], queryFn: fetchHardwareStatus, refetchInterval: 15000,
  });
  const savedHardwareQuery = useQuery({
    queryKey: ['saved-hardware-result', experimentId],
    queryFn: () => fetchSavedHardwareResult(experimentId),
  });
  const simulation = useMutation({
    mutationFn: (input: { experimentId: ExperimentId; shots: number; noiseProfile: NoiseProfile }) =>
      simulateExperiment(input.experimentId, input.shots, input.noiseProfile),
    onSuccess: (result) => {
      setSimulatorResult(result);
      if (challengeId) {
        if (evaluateChallenge(challengeId, result)) {
          setChallengeProgress(completeChallenge(challengeId));
          setChallengeNotice('Challenge complete! Your progress is saved in this browser.');
        } else {
          setChallengeNotice('Not quite yet. Check the challenge goal, shot count, and noise setting, then try again.');
        }
      }
      if (result.experiment_id === currentExperiment.current) setResultSource('simulator');
    },
  });
  const hardware = useMutation({
    mutationFn: (input: { experimentId: ExperimentId; shots: number; idempotencyKey: string }) =>
      submitHardwareExperiment(input.experimentId, input.shots, input.idempotencyKey),
    onSuccess: (data, input) => {
      saveSubmission(input.experimentId, {
        shots: input.shots, idempotencyKey: input.idempotencyKey, trackingId: data.tracking_id,
      });
      if (input.experimentId === currentExperiment.current) setResultSource('hardware');
      void hardwareStatusQuery.refetch();
    },
    onError: (_error, input) => {
      if (input.experimentId === currentExperiment.current) setResultSource('hardware');
    },
  });
  const job = useExperimentJob(trackingId);
  const expiredJob = axios.isAxiosError(job.error) && job.error.response?.status === 404;
  const activeJob = trackingId && !expiredJob && (!job.data || !['completed', 'failed', 'cancelled'].includes(job.data.status));
  const pending = simulation.isPending || hardware.isPending;
  const experiment = experimentsQuery.data?.find((item) => item.experiment_id === experimentId);
  const hardwareResult: ExperimentResult | null = job.data?.counts && job.data.experiment_id === experimentId ? {
    experiment_id: job.data.experiment_id, backend: 'ibm_quantum',
    backend_name: job.data.backend_name, shots: job.data.shots,
    counts: job.data.counts, observed_probabilities: job.data.observed_probabilities ?? {},
    ideal_probabilities: job.data.ideal_probabilities, provider_job_id: job.data.provider_job_id,
    tracking_id: trackingId,
  } : null;
  const recordedHardwareResult = savedHardwareQuery.data?.experiment_id === experimentId
    ? savedHardwareQuery.data
    : null;
  const hardwareDemoVerified = config.data?.hardware_demo_verified === true;
  const hardwareReady = hardwareDemoVerified && hardwareStatusQuery.data?.hardware_enabled === true;
  const canRetryHardware = Boolean(saved && !saved.trackingId);
  const hardwareButtonDisabled = pending || (!canRetryHardware && (
    Boolean(activeJob) ||
    !config.data ||
    shots > config.data.max_hardware_shots ||
    !hardwareStatusQuery.data?.hardware_enabled ||
    hardwareStatusQuery.data.remaining_today === 0 ||
    hardwareStatusQuery.data.active_jobs >= hardwareStatusQuery.data.active_limit
  ));
  const matchingSimulation = simulatorResult?.experiment_id === experimentId ? simulatorResult : null;
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

  function runHardware() {
    const previous = saved && !saved.trackingId ? saved : undefined;
    const idempotencyKey = previous?.idempotencyKey ?? createSubmissionKey();
    const submittedShots = previous?.shots ?? shots;
    saveSubmission(experimentId, { idempotencyKey, shots: submittedShots, trackingId: null });
    hardware.mutate({ experimentId, shots: submittedShots, idempotencyKey });
  }

  async function shareSetup() {
    const url = new URL(window.location.href);
    url.searchParams.set('experiment', experimentId);
    url.searchParams.set('shots', String(shots));
    url.searchParams.set('noise', noiseProfile);
    setShareUrl(url.toString());
    try {
      await navigator.clipboard.writeText(url.toString());
      setShareNotice('Experiment link copied.');
    } catch {
      setShareNotice('Copy the link from the field below.');
    }
  }

  function downloadResultCsv(result: ExperimentResult) {
    const outcomes = [...new Set([
      ...Object.keys(result.counts),
      ...Object.keys(result.ideal_probabilities),
    ])].sort();
    const rows = [
      ['outcome', 'count', 'observed_probability', 'ideal_probability'],
      ...outcomes.map((outcome) => [
        outcome,
        String(result.counts[outcome] ?? 0),
        String(result.observed_probabilities[outcome] ?? 0),
        String(result.ideal_probabilities[outcome] ?? 0),
      ]),
    ];
    const csv = rows.map((row) => row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${result.experiment_id}-results.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }
  const maxShots = config.data?.max_simulator_shots ?? 0;
  const shotOptions = [...new Set([128, 512, 1024, 2048, 4096, maxShots, config.data?.max_hardware_shots ?? 0, config.data?.default_shots ?? 0, shots])]
    .filter((value) => value >= 1 && value <= Math.max(maxShots, config.data?.max_hardware_shots ?? 0)).sort((a, b) => a - b);

  function chooseExperiment(id: ExperimentId) {
    setSearchParams({ experiment: id, ...(challengeId ? { challenge: challengeId } : {}) });
    setSimulatorResult(null);
    setResultSource(submissions[id]?.trackingId ? 'hardware' : 'simulator');
    simulation.reset();
    hardware.reset();
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">Quantum Hardware Lab</h1>
      <p className="mt-2 max-w-3xl text-slate-300">
        Run workshop experiments on real IBM quantum hardware and compare their measurements with a simulator.
        Hardware is the goal; the active run mode stays clearly labeled until the live flow is verified.
      </p>
      <section className="glass quantum-gradient mt-6 overflow-hidden border-cyan-300/20 p-6 sm:p-8" aria-label="Real hardware lab status">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(16rem,0.8fr)] lg:items-center">
          <div>
            <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-cyan-200">
              <Cpu className="h-4 w-4" /> Real IBM quantum hardware
            </p>
            <h2 className="mt-3 max-w-2xl text-2xl font-bold sm:text-3xl">Your experiment, measured on a real quantum processor</h2>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-200">
              Submit the selected circuit to IBM, follow its queue status, then compare the returned measurements with the simulator.
            </p>
          </div>
          <div className="rounded-2xl border border-white/15 bg-navy-950/60 p-5">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Run status</p>
            {hardwareReady ? (
              <>
                <p className="mt-2 inline-flex items-center gap-2 font-semibold text-emerald-200"><span className="h-2 w-2 rounded-full bg-emerald-400" /> IBM hardware flow verified</p>
                <p className="mt-2 text-sm text-slate-300">Live hardware is the primary run mode. Simulator results remain available for comparison.</p>
              </>
            ) : hardwareDemoVerified ? (
              <>
                <p className="mt-2 inline-flex items-center gap-2 font-semibold text-amber-200"><span className="h-2 w-2 rounded-full bg-amber-400" /> IBM flow verified · access unavailable</p>
                <p className="mt-2 text-sm text-slate-300">This lab has completed an end-to-end hardware run before. Simulator mode is active until IBM access returns.</p>
              </>
            ) : (
              <>
                <p className="mt-2 inline-flex items-center gap-2 font-semibold text-amber-200"><span className="h-2 w-2 rounded-full bg-amber-400" /> Simulator mode active</p>
                <p className="mt-2 text-sm text-slate-300">
                  The IBM workflow has not been marked end-to-end verified yet. Simulator results are labeled as simulator runs.
                </p>
              </>
            )}
            {hardwareStatusQuery.data?.hardware_enabled && (
              <p className="mt-3 border-t border-white/10 pt-3 text-xs text-slate-400">
                Lab jobs: {hardwareStatusQuery.data.active_jobs}/{hardwareStatusQuery.data.active_limit} active · {hardwareStatusQuery.data.remaining_today} app submissions left today
              </p>
            )}
          </div>
        </div>
      </section>
      <Link to="/builder" className="btn-secondary mt-4 inline-flex text-sm">Create a custom circuit</Link>
      {activeChallenge && <section className="glass mt-5 p-4" aria-label="Active challenge">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-cyan-300">Active challenge</p>
            <h2 className="mt-1 font-semibold">{activeChallenge.title}</h2>
            <p className="mt-1 text-sm text-slate-300">{activeChallenge.objective}</p>
          </div>
          <span className="text-sm text-emerald-200">{challengeProgress.completedChallenges.includes(activeChallenge.id) ? 'Completed' : `Minimum ${activeChallenge.minimumShots} shots`}</span>
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
                <button
                  key={item.experiment_id}
                  disabled={pending}
                  onClick={() => chooseExperiment(item.experiment_id)}
                  className={`rounded-xl border p-4 text-left transition ${
                    experimentId === item.experiment_id
                      ? 'border-cyan-400/50 bg-cyan-400/10'
                      : 'border-white/10 bg-white/5 hover:bg-white/10'
                  }`}
                >
                  <p className="font-semibold">{item.title}</p>
                  <p className="mt-1 text-xs capitalize text-cyan-300">{item.difficulty}</p>
                  <p className="mt-1 text-xs text-slate-400">{item.qubits} qubit(s)</p>
                </button>
              ))}
            </div>

            {experiment && (
              <p className="mt-4 text-sm text-slate-300">{experiment.description}</p>
            )}
          </section>

          <section id="experiment-execution" className={`glass p-5 ${hardwareReady ? 'border-purple-300/30 shadow-lg shadow-purple-950/30' : 'border-cyan-300/20'}`}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-purple-200">
                  <Cpu className="h-4 w-4" /> Run the selected experiment
                </p>
                <h2 className="mt-2 text-xl font-semibold">{experiment?.title ?? 'Choose an experiment'}</h2>
                <p className="mt-1 text-sm text-slate-300">
                  {hardwareReady
                    ? 'Send this circuit to IBM hardware, then compare the measured results.'
                    : hardwareDemoVerified
                      ? 'IBM hardware was verified previously, but access is unavailable right now. Simulator is active.'
                      : 'Simulator is the current verified mode. IBM hardware stays clearly identified as a pilot run until end-to-end verification.'}
                </p>
              </div>
              <span className={`rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wide ${hardwareReady ? 'border-emerald-300/30 bg-emerald-300/10 text-emerald-200' : 'border-amber-300/30 bg-amber-300/10 text-amber-100'}`}>
                {hardwareReady ? 'Live hardware ready' : hardwareDemoVerified ? 'IBM access unavailable' : 'Simulator mode'}
              </span>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <label className="text-sm">
                Shots
                <select
                  className="input mt-2"
                  value={shots}
                  disabled={pending || Boolean(saved && !saved.trackingId)}
                  onChange={(event) => setShots(Number(event.target.value))}
                >
                  {shotOptions.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <label className="text-sm">
                Simulator noise
                <select className="input mt-2" value={noiseProfile}
                  onChange={(event) => {
                    if (isNoiseProfile(event.target.value)) setNoiseProfile(event.target.value);
                  }}>
                  <option value="ideal">Ideal (no added noise)</option>
                  <option value="low">Low noise</option>
                  <option value="medium">Medium noise</option>
                  <option value="high">High noise</option>
                </select>
              </label>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <button
                className={`${hardwareReady ? 'btn-primary' : 'btn-secondary'} min-h-12 px-3 text-sm sm:text-base`}
                onClick={runHardware}
                disabled={hardwareButtonDisabled}
              >
                {hardware.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Cpu className="h-4 w-4" />}
                {canRetryHardware
                  ? 'Retry IBM submission'
                  : hardwareStatusQuery.data?.hardware_enabled
                    ? hardwareReady ? 'Run on IBM hardware' : 'Try IBM hardware'
                    : hardwareStatusQuery.isLoading ? 'Checking IBM access' : 'IBM hardware unavailable'}
              </button>
              <button
                className={`${hardwareReady ? 'btn-secondary' : 'btn-primary'} min-h-12 px-3 text-sm sm:text-base`}
                onClick={() => simulation.mutate({ experimentId, shots, noiseProfile })}
                disabled={pending || !config.data || shots > maxShots || experimentsQuery.isError}
              >
                {simulation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                {hardwareReady ? 'Run Simulator' : 'Run Simulator (active mode)'}
              </button>
            </div>

            {!hardwareStatusQuery.data?.hardware_enabled && (
              <p className="mt-3 text-sm text-amber-200">
                IBM access is unavailable. The current run mode is Simulator; its results will be labeled clearly.
              </p>
            )}
            {hardwareStatusQuery.data?.hardware_enabled && !hardwareDemoVerified && (
              <p className="mt-3 text-sm text-amber-100">
                IBM access is configured, but the page stays in Simulator mode until an end-to-end hardware run is verified.
              </p>
            )}
            {recordedHardwareResult && !hardwareResult && (
              <p className="mt-3 text-sm text-amber-200" role="status">
                Showing the last saved IBM hardware run while a live result is unavailable. This is recorded data, not a new run.
              </p>
            )}
            {simulation.isError && <div className="mt-3"><ErrorMessage message="The simulator could not complete this experiment." /></div>}
            {hardware.isError && <div className="mt-3"><ErrorMessage message="Hardware submission failed or is unavailable." /></div>}
            {expiredJob && <button className="btn-secondary mt-3" onClick={() => saveSubmission(experimentId)}>Clear expired tracking ID</button>}
            {job.isError && <div className="mt-3"><ErrorMessage message="The hardware job could not be loaded. Your submission is saved; refresh to retry." /></div>}
            {hardwareStatusQuery.isError && <div className="mt-3"><ErrorMessage message="Hardware availability could not be checked." /></div>}
            {canRetryHardware && !hardware.isPending && <p className="mt-3 text-sm text-amber-300">Retry to recover this submission before starting another hardware job.</p>}
            {trackingId && job.data && (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-4 text-sm">
                <p><strong>Status:</strong> {job.data.status}</p>
                {job.data.backend_name && <p><strong>Backend:</strong> {job.data.backend_name}</p>}
                {job.data.provider_job_id && <p className="break-all"><strong>IBM job ID:</strong> {job.data.provider_job_id}</p>}
                {job.data.error && <p className="text-rose-300">{job.data.error}</p>}
              </div>
            )}
            {hardwareStatusQuery.data?.hardware_enabled && (
              <p className="mt-3 text-xs text-slate-400">
                {hardwareStatusQuery.data.remaining_today} app submissions remaining today · {hardwareStatusQuery.data.active_jobs}/{hardwareStatusQuery.data.active_limit} active
              </p>
            )}
          </section>

          {(experimentsQuery.isLoading || config.isLoading) && <p role="status">Loading experiments...</p>}
          {(experimentsQuery.isError || config.isError) && <ErrorMessage message="Experiment settings could not be loaded. Please refresh to retry." />}
          {experiment && <>
            <CircuitDiagram experiment={experiment} />
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

          {activeResult && (
            <section className="glass p-5">
              <h2 className="font-semibold">Measurement Results: {activeResult.backend === 'ibm_quantum' ? 'IBM hardware' : activeResult.backend === 'ibm_quantum_recorded' ? 'Recorded IBM hardware' : 'Simulator'}</h2>
              {activeResult.backend === 'ibm_quantum_recorded' && activeResult.recorded_at && (
                <p className="mt-2 text-xs text-amber-200">Saved from a completed hardware run on {new Date(activeResult.recorded_at).toLocaleString()}.</p>
              )}
              {activeResult.backend === 'aer_simulator' && activeResult.noise_profile && activeResult.noise_profile !== 'ideal' && (
                <p className="mt-2 text-sm text-amber-200">
                  {activeResult.noise_profile} noise is applied to gates and readout. Compare the observed distribution with the ideal probabilities below.
                </p>
              )}
              {matchingSimulation && (hardwareResult || recordedHardwareResult) && <div className="my-3 flex flex-wrap gap-3">
                <button className="btn-secondary" onClick={() => setResultSource('simulator')} aria-pressed={resultSource === 'simulator'}>Simulator results</button>
                <button className="btn-secondary" onClick={() => setResultSource('hardware')} aria-pressed={resultSource === 'hardware'}>{hardwareResult ? 'Hardware results' : 'Recorded hardware results'}</button>
              </div>}
              <MeasurementHistogram counts={activeResult.counts} />
              <ProbabilityComparison
                observed={activeResult.observed_probabilities}
                ideal={activeResult.ideal_probabilities}
              />
              <div className="mt-4 flex flex-wrap gap-3">
                {activeResult.backend === 'aer_simulator' && <button className="btn-secondary text-sm" onClick={() => void shareSetup()}>
                  Copy experiment link
                </button>}
                <button className="btn-secondary text-sm" onClick={() => downloadResultCsv(activeResult)}>
                  Download results CSV
                </button>
              </div>
              {shareUrl && <div className="mt-3">
                <label className="block text-xs text-slate-400" htmlFor="share-experiment-url">Shareable setup link</label>
                <input id="share-experiment-url" className="input mt-1 text-xs" readOnly value={shareUrl} onFocus={(event) => event.currentTarget.select()} />
                <p role="status" className="mt-1 text-xs text-slate-400">{shareNotice}</p>
              </div>}
              {activeResult.amplitudes && <details className="mt-5" open={experiment?.difficulty === 'advanced'}>
                <summary className="cursor-pointer font-semibold text-cyan-300">Ideal state before measurement: amplitudes and phases</summary>
                <p className="my-3 text-sm text-slate-300">
                  This table comes from the ideal statevector, not hardware measurements. Basis strings include every qubit
                  in q[n-1]...q[0] order; the histogram includes only measured classical bits. Relative phases matter;
                  a common global phase does not affect observations. Zero amplitudes are omitted.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[28rem] text-left text-sm">
                    <thead className="text-slate-400"><tr><th className="p-2">Basis state</th><th className="p-2">Real</th><th className="p-2">Imaginary</th><th className="p-2">Probability</th><th className="p-2">Phase</th></tr></thead>
                    <tbody>{activeResult.amplitudes.map((amplitude) => <tr key={amplitude.outcome} className="border-t border-white/10">
                      <td className="p-2 font-mono">|{amplitude.outcome}&gt;</td>
                      <td className="p-2">{amplitude.real.toFixed(4)}</td><td className="p-2">{amplitude.imag.toFixed(4)}</td>
                      <td className="p-2">{(amplitude.probability * 100).toFixed(2)}%</td><td className="p-2">{amplitude.phase_degrees.toFixed(1)} deg</td>
                    </tr>)}</tbody>
                  </table>
                </div>
              </details>}
              <p className="mt-3 text-sm text-slate-300">
                Bitstrings are shown in Qiskit’s standard displayed convention: the leftmost bit is the
                highest classical-bit index.
              </p>
            </section>
          )}
          {matchingSimulation && (hardwareResult || recordedHardwareResult) && (
            <BackendComparison simulator={matchingSimulation} hardware={hardwareResult ?? recordedHardwareResult!} />
          )}
        </div>

        <AIChatPanel compact />
      </div>
    </div>
  );
}
