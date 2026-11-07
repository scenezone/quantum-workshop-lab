import type { Amplitude } from '../types/api';

export default function AmplitudeTable({ amplitudes, open, rotatedBasis }: {
  amplitudes: Amplitude[];
  open?: boolean;
  rotatedBasis?: boolean;
}) {
  return (
    <details className="mt-5" open={open}>
      <summary className="cursor-pointer font-semibold text-cyan-300">Ideal state before measurement: amplitudes and phases</summary>
      <p className="my-3 text-sm text-slate-300">
        This table comes from the ideal statevector, not hardware measurements. Basis strings include every qubit
        in q[n-1]...q[0] order; the histogram includes only measured classical bits. Relative phases matter;
        a common global phase does not affect observations. Zero amplitudes are omitted.
        {rotatedBasis && ' Amplitudes are shown in the computational (Z) basis, before the measurement-basis rotation.'}
      </p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[28rem] text-left text-sm">
          <thead className="text-slate-400"><tr><th className="p-2">Basis state</th><th className="p-2">Real</th><th className="p-2">Imaginary</th><th className="p-2">Probability</th><th className="p-2">Phase</th></tr></thead>
          <tbody>{amplitudes.map((amplitude) => <tr key={amplitude.outcome} className="border-t border-white/10">
            <td className="p-2 font-mono">|{amplitude.outcome}&gt;</td>
            <td className="p-2">{amplitude.real.toFixed(4)}</td><td className="p-2">{amplitude.imag.toFixed(4)}</td>
            <td className="p-2">{(amplitude.probability * 100).toFixed(2)}%</td><td className="p-2">{amplitude.phase_degrees.toFixed(1)} deg</td>
          </tr>)}</tbody>
        </table>
      </div>
    </details>
  );
}
