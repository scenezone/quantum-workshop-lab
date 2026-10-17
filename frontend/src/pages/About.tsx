import { Link } from 'react-router-dom';

export default function About() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">Workshop Guide</h1>
      <ol className="mt-6 space-y-4 text-slate-300">
        <li><strong>1. Learn:</strong> Read the qubit, superposition, entanglement, gates, and hardware lessons.</li>
        <li><strong>2. Experiment:</strong> Open the Playground and select Superposition, Bell Entanglement, or Interference.</li>
        <li><strong>3. Simulate:</strong> Run the circuit on Qiskit Aer and inspect the histogram.</li>
        <li><strong>4. Hardware:</strong> If enabled, submit the same approved circuit to IBM Quantum and monitor its job.</li>
        <li><strong>5. Understand:</strong> Ask the AI assistant why ideal and observed results differ.</li>
        <li><strong>6. Reflect:</strong> Submit optional anonymous feedback.</li>
      </ol>

      <div className="mt-8 flex gap-4">
        <Link to="/learn" className="btn-primary">Start Learning</Link>
        <Link to="/playground" className="btn-secondary">Open Playground</Link>
      </div>
    </div>
  );
}