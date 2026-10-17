import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { fetchJobStatus } from '../services/api';
import type { JobStatusResponse } from '../types/api';

const TERMINAL: JobStatusResponse['status'][] = ['completed', 'failed', 'cancelled'];

export function useExperimentJob(trackingId: string | null) {
  const query = useQuery({
    queryKey: ['hardware-job', trackingId],
    queryFn: () => fetchJobStatus(trackingId!),
    enabled: Boolean(trackingId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && TERMINAL.includes(status) ? false : 3000;
    },
  });

  useEffect(() => {
    return () => {
      query.remove();
    };
  }, [trackingId]);

  return query;
}