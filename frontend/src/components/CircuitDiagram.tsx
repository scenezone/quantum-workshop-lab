import type { Experiment, MeasurementBasis } from '../types/api';
import CircuitCanvas from './CircuitCanvas';

export default function CircuitDiagram({ experiment, measurementBases }: {
  experiment: Experiment;
  measurementBases?: MeasurementBasis[];
}) {
  const rotated = measurementBases?.some((basis) => basis !== 'Z');
  return (
    <section className="glass min-w-0 p-4" aria-label="Circuit and gate walkthrough">
      <h2 className="mb-3 font-semibold">Circuit: {experiment.title}</h2>
      <div className="max-w-full overflow-x-auto overscroll-x-contain" tabIndex={0} role="region" aria-label="Scrollable quantum circuit">
        <CircuitCanvas qubits={experiment.qubits} gates={experiment.gates} />
      </div>
      <p className="mt-2 text-xs text-slate-400">
        Gates run left to right. Measurement labels identify the classical result bits. Scroll horizontally for longer circuits.
        {rotated && ` Measurements use the ${measurementBases!.map((basis, qubit) => `${basis} basis on q${qubit}`).join(', ')}; a basis rotation is inserted just before each measurement.`}
      </p>
      <details className="mt-4">
        <summary className="cursor-pointer text-sm text-cyan-300">Gate-by-gate walkthrough ({experiment.gates.length} steps)</summary>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-slate-300">
          {experiment.gates.map((gate, index) => <li key={index}>
            <strong>{gate.name} on {gate.qubits.map((qubit) => `q${qubit}`).join(', ')}:</strong> {gate.explanation}
          </li>)}
        </ol>
      </details>
    </section>
  );
}
