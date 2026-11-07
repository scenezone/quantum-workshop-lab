import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { fetchJobStatus } from '../services/api';
import type { JobStatusResponse } from '../types/api';

const TERMINAL = ['completed', 'failed', 'cancelled'];

/** Poll often while a job is new, then back off: IBM queues can take hours. */
export function pollInterval(job: JobStatusResponse | undefined, updates: number, now = Date.now()): number {
  const created = job?.created_at ? Date.parse(job.created_at) : NaN;
  const ageSeconds = Number.isFinite(created) ? (now - created) / 1000 : updates * 5;
  if (ageSeconds < 120) return 5000;
  if (ageSeconds < 600) return 15000;
  if (ageSeconds < 3600) return 60000;
  return 300000;
}

export function useExperimentJob(trackingId: string | null) {
  return useQuery({
    queryKey: ['hardware-job', trackingId],
    queryFn: ({ signal }) => fetchJobStatus(trackingId!, signal),
    enabled: Boolean(trackingId),
    retry: (attempt, error) => !axios.isAxiosError(error) || error.response?.status !== 404 ? attempt < 2 : false,
    refetchInterval: (query) => {
      if (axios.isAxiosError(query.state.error) && query.state.error.response?.status === 404) return false;
      const status = query.state.data?.status;
      if (status && TERMINAL.includes(status)) return false;
      return pollInterval(query.state.data, query.state.dataUpdateCount);
    },
    gcTime: 0,
  });
}
