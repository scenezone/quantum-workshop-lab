import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { fetchJobStatus } from '../services/api';

export function useExperimentJob(trackingId: string | null) {
  return useQuery({
    queryKey: ['hardware-job', trackingId],
    queryFn: ({ signal }) => fetchJobStatus(trackingId!, signal),
    enabled: Boolean(trackingId),
    retry: (attempt, error) => !axios.isAxiosError(error) || error.response?.status !== 404 ? attempt < 2 : false,
    refetchInterval: (query) => {
      if (axios.isAxiosError(query.state.error) && query.state.error.response?.status === 404) return false;
      const status = query.state.data?.status;
      return status && ['completed', 'failed', 'cancelled'].includes(status) ? false : 5000;
    },
    gcTime: 0,
  });
}
