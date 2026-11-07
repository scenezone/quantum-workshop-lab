import { CheckCircle2, TriangleAlert } from 'lucide-react';
import {
  expectedSamplingDistance,
  hellingerFidelity,
  samplingVerdict,
  totalVariationDistance,
} from '../services/stats';

/** Explains whether a measured histogram differs from the ideal more than chance allows. */
export default function ResultStatistics({ counts, observed, ideal, shots }: {
  counts: Record<string, number>;
  observed: Record<string, number>;
  ideal: Record<string, number>;
  shots: number;
}) {
  if (!Object.keys(ideal).length || !shots) return null;
  const distance = totalVariationDistance(observed, ideal);
  const typical = expectedSamplingDistance(ideal, shots);
  const fidelity = hellingerFidelity(observed, ideal);
  const verdict = samplingVerdict(counts, ideal);
  const Icon = verdict.consistent ? CheckCircle2 : TriangleAlert;
  return (
    <section aria-label="Result statistics" className="mt-4 rounded-xl border border-white/10 bg-white/5 p-4 text-sm">
      <p className={`flex items-start gap-2 ${verdict.consistent ? 'text-emerald-200' : 'text-amber-200'}`}>
        <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <span>{verdict.summary}</span>
      </p>
      <dl className="mt-3 grid gap-3 sm:grid-cols-3">
        <div>
          <dt className="text-xs text-slate-400">Distance from ideal (TVD)</dt>
          <dd className="font-semibold text-cyan-100">{(distance * 100).toFixed(1)} pp</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-400">Typical from sampling alone</dt>
          <dd className="font-semibold text-cyan-100">≈ {(typical * 100).toFixed(1)} pp</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-400">Fidelity with ideal</dt>
          <dd className="font-semibold text-cyan-100">{fidelity.toFixed(3)}</dd>
        </div>
      </dl>
      <p className="mt-3 text-xs text-slate-400">
        Error bars on the probability chart show ±2 standard errors, √(p(1−p)/N). More shots shrink them by √N.
        TVD is half the summed absolute differences (0 = identical); fidelity is (Σ√(p·q))² (1 = identical).
      </p>
    </section>
  );
}
