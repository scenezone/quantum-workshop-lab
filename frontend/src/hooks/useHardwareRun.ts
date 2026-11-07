import { useMutation, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { fetchHardwareStatus, submitHardwareExperiment } from '../services/api';
import { createSubmissionKey } from '../services/experimentUtils';
import { saveSubmission, useHardwareSubmissions } from '../services/hardwareStorage';
import { addHardwareHistory } from '../services/jobHistory';
import type { ExperimentId, ExperimentResult } from '../types/api';
import { useExperimentJob } from './useExperimentJob';

const TERMINAL = ['completed', 'failed', 'cancelled'];

/** Hardware submission, retry with the original idempotency key, and job tracking for one experiment. */
export function useHardwareRun(experimentId: ExperimentId, options: {
  hardwareConfigured?: boolean;
  onSubmitted?: (experimentId: ExperimentId) => void;
  onFailed?: (experimentId: ExperimentId) => void;
}) {
  const submissions = useHardwareSubmissions();
  const saved = submissions[experimentId];
  const trackingId = saved?.trackingId ?? null;
  const pendingRetry = Boolean(saved && !saved.trackingId);

  const status = useQuery({
    queryKey: ['hardware-status'],
    queryFn: fetchHardwareStatus,
    // Polling quota only matters when this deployment can submit hardware jobs.
    refetchInterval: options.hardwareConfigured === false ? false : 15000,
  });
  const mutation = useMutation({
    mutationFn: (input: { experimentId: ExperimentId; shots: number; idempotencyKey: string }) =>
      submitHardwareExperiment(input.experimentId, input.shots, input.idempotencyKey),
    onSuccess: (data, input) => {
      saveSubmission(input.experimentId, {
        shots: input.shots, idempotencyKey: input.idempotencyKey, trackingId: data.tracking_id,
      });
      addHardwareHistory({
        trackingId: data.tracking_id, experimentId: input.experimentId, shots: input.shots,
        submittedAt: new Date().toISOString(),
      });
      options.onSubmitted?.(input.experimentId);
      void status.refetch();
    },
    onError: (_error, input) => options.onFailed?.(input.experimentId),
  });
  const job = useExperimentJob(trackingId);
  const expiredJob = axios.isAxiosError(job.error) && job.error.response?.status === 404;
  const activeJob = Boolean(trackingId && !expiredJob && (!job.data || !TERMINAL.includes(job.data.status)));

  const result: ExperimentResult | null = job.data?.counts && job.data.experiment_id === experimentId ? {
    experiment_id: job.data.experiment_id, backend: 'ibm_quantum',
    backend_name: job.data.backend_name, shots: job.data.shots,
    counts: job.data.counts, observed_probabilities: job.data.observed_probabilities ?? {},
    ideal_probabilities: job.data.ideal_probabilities, provider_job_id: job.data.provider_job_id,
    tracking_id: trackingId,
  } : null;

  function submit(shots: number) {
    const previous = pendingRetry ? saved : undefined;
    const idempotencyKey = previous?.idempotencyKey ?? createSubmissionKey();
    const submittedShots = previous?.shots ?? shots;
    saveSubmission(experimentId, { idempotencyKey, shots: submittedShots, trackingId: null });
    mutation.mutate({ experimentId, shots: submittedShots, idempotencyKey });
  }

  function canSubmit(shots: number, maxHardwareShots: number | undefined): boolean {
    if (pendingRetry) return true; // A retry recovers an earlier reservation, even without quota.
    const quota = status.data;
    return !activeJob && maxHardwareShots !== undefined && shots <= maxHardwareShots
      && Boolean(quota?.hardware_enabled) && quota!.remaining_today > 0 && quota!.active_jobs < quota!.active_limit;
  }

  return {
    saved, trackingId, pendingRetry, status, mutation, job, expiredJob, activeJob, result, submit, canSubmit,
    clearExpired: () => saveSubmission(experimentId),
  };
}
