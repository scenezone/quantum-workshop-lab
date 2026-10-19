import FeedbackForm from '../components/FeedbackForm';
import { Link } from 'react-router-dom';

export default function About() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">Workshop Guide</h1>
      <ol className="mt-6 space-y-4 text-slate-300">
        <li><strong>1. Learn:</strong> Follow 14 lessons from qubits to oracle algorithms, Fourier transforms, teleportation, error correction, and variational methods.</li>
        <li><strong>2. Experiment:</strong> Choose one of 10 guided circuits, inspect its gates, and open the related theory lesson.</li>
        <li><strong>3. Simulate:</strong> Run on Qiskit Aer, compare probabilities, and inspect complex amplitudes and relative phases.</li>
        <li><strong>4. Hardware:</strong> If enabled, submit the same approved circuit to IBM Quantum and monitor its job.</li>
        <li><strong>5. Understand:</strong> Ask the AI assistant why ideal and observed results differ.</li>
        <li><strong>6. Reflect:</strong> Submit optional anonymous feedback.</li>
      </ol>

      <div className="mt-8"><FeedbackForm /></div>

      <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:flex-wrap">
        <Link to="/learn" className="btn-primary">Start Learning</Link>
        <Link to="/playground" className="btn-secondary">Open Playground</Link>
      </div>
    </div>
  );
}
