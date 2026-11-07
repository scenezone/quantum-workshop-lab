import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { useState } from 'react';
import { importQasm } from '../../services/api';
import { qasmCode, qiskitCode } from '../../services/circuit';
import { downloadText } from '../../services/download';
import type { CustomCircuitDefinition, CustomCircuitGate, MeasurementBasis } from '../../types/api';

export default function CodeExport({ qubits, gates, bases, onImport }: {
  qubits: number;
  gates: CustomCircuitGate[];
  bases: MeasurementBasis[];
  onImport: (circuit: CustomCircuitDefinition) => void;
}) {
  const [format, setFormat] = useState<'qiskit' | 'qasm'>('qiskit');
  const [source, setSource] = useState('');
  const importer = useMutation({ mutationFn: importQasm, onSuccess: (circuit) => { onImport(circuit); setSource(''); } });
  const rotated = bases.some((basis) => basis !== 'Z') ? bases : undefined;
  const code = format === 'qiskit' ? qiskitCode(qubits, gates, rotated) : qasmCode(qubits, gates, rotated);
  const importError = importer.error && axios.isAxiosError(importer.error)
    ? String(importer.error.response?.data?.detail ?? 'The program could not be imported.')
    : importer.error ? 'The program could not be imported.' : '';

  return (
    <div className="mt-4">
      <div role="tablist" aria-label="Code format" className="flex gap-2">
        {(['qiskit', 'qasm'] as const).map((item) => (
          <button key={item} role="tab" type="button" aria-selected={format === item}
            className={`rounded-lg px-3 py-1 text-xs ${format === item ? 'bg-cyan-400/15 text-cyan-100' : 'text-slate-400 hover:text-slate-200'}`}
            onClick={() => setFormat(item)}>
            {item === 'qiskit' ? 'Qiskit (Python)' : 'OpenQASM 2'}
          </button>
        ))}
      </div>
      <pre className="mt-2 overflow-x-auto rounded-lg bg-navy-950 p-4 text-xs text-slate-200"><code>{code}</code></pre>
      <div className="mt-3 flex flex-wrap gap-3">
        <button type="button" className="btn-secondary text-sm"
          onClick={() => downloadText('quantum-workshop-circuit.py', qiskitCode(qubits, gates, rotated), 'text/x-python;charset=utf-8')}>
          Download Qiskit code
        </button>
        <button type="button" className="btn-secondary text-sm"
          onClick={() => downloadText('quantum-workshop-circuit.qasm', qasmCode(qubits, gates, rotated), 'text/plain;charset=utf-8')}>
          Download OpenQASM
        </button>
      </div>
      <details className="mt-4">
        <summary className="cursor-pointer text-sm text-cyan-300">Import an OpenQASM 2 program</summary>
        <form className="mt-3" onSubmit={(event) => { event.preventDefault(); if (source.trim()) importer.mutate(source); }}>
          <label className="text-sm" htmlFor="qasm-import">OpenQASM 2 source</label>
          <textarea id="qasm-import" className="input mt-2 min-h-32 font-mono text-xs" maxLength={20000} value={source}
            placeholder={'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\ncx q[0],q[1];'}
            onChange={(event) => setSource(event.target.value)} />
          <p className="mt-1 text-xs text-slate-400">
            Supports the builder’s gates plus p and u1. Measurements are added at the end automatically; this replaces the current circuit.
          </p>
          <button type="submit" className="btn-secondary mt-2 text-sm" disabled={!source.trim() || importer.isPending}>
            {importer.isPending ? 'Importing…' : 'Import program'}
          </button>
          {importError && <p role="alert" className="mt-2 text-sm text-rose-300">{importError}</p>}
        </form>
      </details>
    </div>
  );
}
