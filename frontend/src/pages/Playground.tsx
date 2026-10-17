import { useMutation, useQuery } from '@tanstack/react-query';
import { CircuitBoard, Cpu, Loader2, Play, Server } from 'lucide-react';
import { useState } from 'react';
import AIChatPanel from '../components/AIChatPanel';
import CircuitDiagram from '../components/CircuitDiagram';
import ErrorMessage from '../components/ErrorMessage';
import MeasurementHistogram from '../components/MeasurementHistogram';
import ProbabilityComparison from '../components/ProbabilityComparison';
import { useAssistant } from '../context/AssistantContext';
import { useExperimentJob } from '../hooks/useExperimentJob';
import {
  fetchExperiments,
  fetchHardwareStatus,
  simulateExperiment,
  submitHardwareExperiment,
} from '../services/api';
import type { ExperimentResult } from '../types/api';

export default function Playground() {
  const [experimentId, setExperimentId] = useState('superposition');
  const [shots, setShots] = useState(1024);
  const [simulatorResult, setSimulatorResult] = useState<ExperimentResult | null>(null);
  const [trackingId, setTrackingId] = useState<string | null>(null);
  const { setExperimentId: setAssistantExperiment, setResultContext } = useAssistant();

  const experimentsQuery = useQuery({
    queryKey: ['experiments'],
    queryFn: fetchExperiments,
  });
  const hardwareStatusQuery = useQuery({
    queryKey: ['hardware-status'],
    queryFn: fetchHardwareStatus,
  });

  const simulation = useMutation({
    mutationFn: () => simulateExperiment(experimentId, shots),
    onSuccess: (result) => {
      setSimulatorResult(result);
      setAssistantExperiment(experimentId);
      setResultContext({
        backend: result.backend,
        backend_name: result.backend_name,
        shots: result.shots,
        counts: result.counts,
        observed_probabilities: result.observed_probabilities,
        ideal_probabilities: result.ideal_probabilities,
      });
    },
  });

  const hardware = useMutation({
    mutationFn: () => submitHardwareExperiment(experimentId, shots),
    onSuccess: (data) => setTrackingId(data.tracking_id),
  });

  const job = useExperimentJob(trackingId);
  const experiment = experimentsQuery.data?.find((item) => item.experiment_id === experimentId);
  const activeResult = job.data?.counts
    ? {
        experiment_id: experimentId,
        backend: 'ibm_quantum' as const,
        backend_name: job.data.backend_name,
        shots: job.data.shots,
        counts: job.data.counts ?? {},
        observed_probabilities: job.data.observed_probabilities ?? {},
        ideal_probabilities: job.data.ideal_probabilities,
        provider_job_id: job.data.provider_job_id,
        tracking_id: job.data.tracking_id,
      }
    : simulatorResult;

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">Quantum Playground</h1>
      <p className="mt-2 max-w-3xl text-slate-300">
        Choose a guided experiment, inspect its circuit, run it on the Qiskit Aer simulator, or submit
        it to real IBM Quantum hardware when enabled.
      </p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <div className="space-y-6">
          <section className="glass p-5">
            <h2 className="flex items-center gap-2 font-semibold">
              <CircuitBoard className="h-5 w-5 text-cyan-400" /> Experiment
            </h2>

            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {experimentsQuery.data?.map((item) => (
                <button
                  key={item.experiment_id}
                  onClick={() => {
                    setExperimentId(item.experiment_id);
                    setSimulatorResult(null);
                    setTrackingId(null);
                    setAssistantExperiment(item.experiment_id);
                  }}
                  className={`rounded-xl border p-4 text-left transition ${
                    experimentId === item.experiment_id
                      ? 'border-cyan-400/50 bg-cyan-400/10'
                      : 'border-white/10 bg-white/5 hover:bg-white/10'
                  }`}
                >
                  <p className="font-semibold">{item.title}</p>
                  <p className="mt-1 text-xs text-slate-400">{item.qubits} qubit(s)</p>
                </button>
              ))}
            </div>

            {experiment && (
              <p className="mt-4 text-sm text-slate-300">{experiment.description}</p>
            )}
          </section>

          <CircuitDiagram experimentId={experimentId as any} />

          <section className="glass p-5">
            <h2 className="flex items-center gap-2 font-semibold">
              <Server className="h-5 w-5 text-purple-400" /> Execution
            </h2>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="text-sm">
                Shots
                <select
                  className="input mt-2"
                  value={shots}
                  onChange={(event) => setShots(Number(event.target.value))}
                >
                  {[128, 512, 1024, 2048, 4096].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>

              <div className="flex items-end gap-3">
                <button
                  className="btn-primary flex-1"
                  onClick={() => simulation.mutate()}
                  disabled={simulation.isPending}
                >
                  {simulation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  Run Simulator
                </button>

                <button
                  className="btn-secondary flex-1"
                  onClick={() => hardware.mutate()}
                  disabled={
                    hardware.isPending ||
                    !hardwareStatusQuery.data?.hardware_enabled
                  }
                >
                  <Cpu className="h-4 w-4" />
                  IBM Hardware
                </button>
              </div>
            </div>

            {!hardwareStatusQuery.data?.hardware_enabled && (
              <p className="mt-3 text-sm text-amber-300">
                IBM hardware is disabled by default. Configure backend credentials and quota limits to
                enable it.
              </p>
            )}

            {simulation.isError && (
              <ErrorMessage message="The simulator could not complete this experiment." />
            )}
            {hardware.isError && (
              <ErrorMessage message="Hardware submission failed or is unavailable." />
            )}

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
              <h2 className="font-semibold">Measurement Results</h2>
              <MeasurementHistogram counts={activeResult.counts} />
              <ProbabilityComparison
                observed={activeResult.observed_probabilities}
                ideal={activeResult.ideal_probabilities}
              />
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