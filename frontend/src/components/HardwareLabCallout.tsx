import { useQuery } from '@tanstack/react-query';
import { Cpu } from 'lucide-react';
import { Link } from 'react-router-dom';
import { fetchPublicConfig } from '../services/api';

interface Props {
  experimentId?: string;
  title?: string;
  description?: string;
  compact?: boolean;
}

export default function HardwareLabCallout({
  experimentId,
  title = 'Run an experiment on real IBM quantum hardware',
  description = 'Open the guided lab to submit a supported circuit, follow its job, and compare measured hardware results with the simulator.',
  compact = false,
}: Props) {
  const config = useQuery({ queryKey: ['public-config'], queryFn: fetchPublicConfig });
  const hardwareAvailable = config.data?.hardware_enabled === true;
  const hardwareVerified = hardwareAvailable && config.data?.hardware_demo_verified === true;
  const target = experimentId
    ? `/playground?experiment=${encodeURIComponent(experimentId)}`
    : '/playground';
  const status = config.isLoading
    ? 'Checking IBM access'
    : config.isError
      ? 'Simulator mode · IBM access status unavailable'
      : hardwareVerified
        ? 'Live IBM flow verified'
        : hardwareAvailable
          ? 'Simulator active · IBM pilot available'
          : 'Simulator active · IBM access unavailable';
  const action = config.isLoading
    ? 'Open hardware lab'
    : hardwareVerified
      ? 'Run on IBM hardware'
      : hardwareAvailable
        ? 'Try IBM hardware'
        : 'Open Simulator lab';

  return (
    <section className={`glass quantum-gradient ${compact ? 'p-4' : 'p-5 sm:p-6'}`} aria-label="Real IBM hardware lab">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-cyan-200">
            <Cpu className="h-4 w-4" /> Real IBM hardware
          </p>
          <h2 className="mt-2 text-lg font-semibold">{title}</h2>
          <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-300">{description}</p>
          <p className={`mt-2 text-xs font-semibold ${hardwareVerified ? 'text-emerald-200' : 'text-amber-100'}`} role="status">
            {status}
          </p>
        </div>
        <Link to={target} className={`${hardwareVerified ? 'btn-primary' : 'btn-secondary'} shrink-0 text-sm`}>
          <Cpu className="h-4 w-4" />{action}
        </Link>
      </div>
    </section>
  );
}
