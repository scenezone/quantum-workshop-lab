import { useMutation, useQuery } from '@tanstack/react-query';
import { CircuitBoard, Cpu, Loader2, Play, Server } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { saveSubmission, useHardwareSubmissions } from '../services/hardwareStorage';
import { createSubmissionKey, isExperimentId } from '../services/experimentUtils';
import AIChatPanel from '../components/AIChatPanel';
import CircuitDiagram from '../components/CircuitDiagram';
import ErrorMessage from '../components/ErrorMessage';
import MeasurementHistogram from '../components/MeasurementHistogram';
import ProbabilityComparison from '../components/ProbabilityComparison';
import { useAssistant } from '../context/AssistantContext';
import { useExperimentJob } from '../hooks/useExperimentJob';
import {
  fetchExperiments,
  fetchPublicConfig,
  fetchHardwareStatus,
  simulateExperiment,
  submitHardwareExperiment,
} from '../services/api';
import type { ExperimentId, ExperimentResult } from '../types/api';

export default function Playground() {
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedId = searchParams.get('experiment');
  const experimentId: ExperimentId = isExperimentId(requestedId) ? requestedId : 'superposition';
  const currentExperiment = useRef(experimentId);
  currentExperiment.current = experimentId;
  const [shotsOverride, setShots] = useState<number | null>(null);
  const [simulatorResult, setSimulatorResult] = useState<ExperimentResult | null>(null);
  const [resultSource, setResultSource] = useState<'simulator' | 'hardware'>('hardware');
  const submissions = useHardwareSubmissions();
  const saved = submissions[experimentId];
  const trackingId = saved?.trackingId ?? null;
  const { setStudyContext, setResultContext } = useAssistant();

  const config = useQuery({ queryKey: ['public-config'], queryFn: fetchPublicConfig });
  const shots = saved && !saved.trackingId ? saved.shots : shotsOverride ?? config.data?.default_shots ?? 1024;
  const experimentsQuery = useQuery({ queryKey: ['experiments'], queryFn: fetchExperiments });
  const hardwareStatusQuery = useQuery({
    queryKey: ['hardware-status'], queryFn: fetchHardwareStatus, refetchInterval: 15000,
  });
  const simulation = useMutation({
    mutationFn: (input: { experimentId: ExperimentId; shots: number }) =>
      simulateExperiment(input.experimentId, input.shots),
    onSuccess: (result) => {
      setSimulatorResult(result);
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
  const matchingSimulation = simulatorResult?.experiment_id === experimentId ? simulatorResult : null;
  const activeResult = resultSource === 'hardware' ? hardwareResult ?? matchingSimulation : matchingSimulation;
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
  const maxShots = config.data?.max_simulator_shots ?? 0;
  const shotOptions = [...new Set([128, 512, 1024, 2048, 4096, maxShots, config.data?.max_hardware_shots ?? 0, config.data?.default_shots ?? 0, shots])]
    .filter((value) => value >= 1 && value <= Math.max(maxShots, config.data?.max_hardware_shots ?? 0)).sort((a, b) => a - b);

  function chooseExperiment(id: ExperimentId) {
    setSearchParams({ experiment: id });
    setSimulatorResult(null);
    setResultSource(submissions[id]?.trackingId ? 'hardware' : 'simulator');
    simulation.reset();
    hardware.reset();
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">Quantum Playground</h1>
      <p className="mt-2 max-w-3xl text-slate-300">
        Move from foundational gates to phase kickback, GHZ states, quantum algorithms, and error correction.
        Inspect every gate, simulate the circuit, and connect amplitudes and phases to measured results.
      </p>

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

          {(experimentsQuery.isLoading || config.isLoading) && <p role="status">Loading experiments...</p>}
          {(experimentsQuery.isError || config.isError) && <ErrorMessage message="Experiment settings could not be loaded. Please refresh to retry." />}
          {experiment && <>
            <CircuitDiagram experiment={experiment} />
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
                <select
                  className="input mt-2"
                  value={shots}
                  disabled={pending || Boolean(saved && !saved.trackingId)}
                  onChange={(event) => setShots(Number(event.target.value))}
                >
                  {shotOptions.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <button
                  className="btn-primary min-w-0 px-3 text-sm sm:text-base"
                  onClick={() => simulation.mutate({ experimentId, shots })}
                  disabled={pending || !config.data || shots > maxShots || experimentsQuery.isError}
                >
                  {simulation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  Run Simulator
                </button>

                <button
                  className="btn-secondary min-w-0 px-3 text-sm sm:text-base"
                  onClick={runHardware}
                  disabled={
                    pending || (!(saved && !saved.trackingId) && (Boolean(activeJob) || !config.data ||
                    shots > config.data.max_hardware_shots ||
                    !hardwareStatusQuery.data?.hardware_enabled ||
                    hardwareStatusQuery.data.remaining_today === 0 ||
                    hardwareStatusQuery.data.active_jobs >= hardwareStatusQuery.data.active_limit))
                  }
                >
                  <Cpu className="h-4 w-4" />
                  {saved && !saved.trackingId ? 'Retry submission' : 'IBM Hardware'}
                </button>
              </div>
            </div>

            {!hardwareStatusQuery.data?.hardware_enabled && (
              <p className="mt-3 text-sm text-amber-300">
                Real quantum hardware is currently unavailable. You can continue with the simulator.
              </p>
            )}

            {simulation.isError && (
              <ErrorMessage message="The simulator could not complete this experiment." />
            )}
            {hardware.isError && (
              <ErrorMessage message="Hardware submission failed or is unavailable." />
            )}

            {expiredJob && <button className="btn-secondary mt-3" onClick={() => saveSubmission(experimentId)}>Clear expired tracking ID</button>}
            {job.isError && <ErrorMessage message="The hardware job could not be loaded. Your submission is saved; refresh to retry." />}
            {hardwareStatusQuery.isError && <ErrorMessage message="Hardware availability could not be checked." />}
            {saved && !saved.trackingId && !hardware.isPending && <p className="mt-3 text-sm text-amber-300">Retry to recover this submission before starting another hardware job.</p>}
            {hardwareStatusQuery.data?.hardware_enabled && <p className="mt-3 text-sm text-slate-300">{hardwareStatusQuery.data.remaining_today} hardware submissions remaining today; {hardwareStatusQuery.data.active_jobs}/{hardwareStatusQuery.data.active_limit} active.</p>}
            {trackingId && job.data && (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-4 text-sm">
                <p>
                  <strong>Status:</strong> {job.data.status}
                </p>
                {job.data.backend_name && (
                  <p>
                    <strong>Backend:</strong> {job.data.backend_name}
                  </p>
                )}
                {job.data.provider_job_id && (
                  <p className="break-all">
                    <strong>IBM job ID:</strong> {job.data.provider_job_id}
                  </p>
                )}
                {job.data.error && <p className="text-rose-300">{job.data.error}</p>}
              </div>
            )}
          </section>

          {activeResult && (
            <section className="glass p-5">
              <h2 className="font-semibold">Measurement Results: {activeResult.backend === 'ibm_quantum' ? 'IBM hardware' : 'Simulator'}</h2>
              {matchingSimulation && hardwareResult && <div className="my-3 flex flex-wrap gap-3">
                <button className="btn-secondary" onClick={() => setResultSource('simulator')} aria-pressed={resultSource === 'simulator'}>Simulator results</button>
                <button className="btn-secondary" onClick={() => setResultSource('hardware')} aria-pressed={resultSource === 'hardware'}>Hardware results</button>
              </div>}
              <MeasurementHistogram counts={activeResult.counts} />
              <ProbabilityComparison
                observed={activeResult.observed_probabilities}
                ideal={activeResult.ideal_probabilities}
              />
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
        </div>

        <AIChatPanel compact />
      </div>
    </div>
  );
}
