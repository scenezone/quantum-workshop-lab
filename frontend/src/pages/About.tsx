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
        <li><strong>4. Explore:</strong> Step through gates on Bloch spheres, add preset noise, or build a small custom circuit for simulation.</li>
        <li><strong>5. Hardware:</strong> If enabled, submit an approved guided circuit to IBM Quantum and monitor its job.</li>
        <li><strong>6. Understand:</strong> Ask the workshop assistant for an explanation, hint, or quiz. Live AI is optional.</li>
        <li><strong>7. Reflect:</strong> Track lesson and challenge progress in this browser, then submit optional anonymous feedback.</li>
      </ol>

      <section className="glass mt-8 p-5 sm:p-6" aria-labelledby="data-use-heading">
        <h2 id="data-use-heading" className="text-xl font-semibold">Data and privacy</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-relaxed text-slate-300">
          <li>You can use the workshop without creating an account. Lesson and simulation context stays in this browser session.</li>
          <li>Optional feedback ratings, completion status, comments, and submission time are stored until the workshop operator removes them. Avoid including personal or sensitive information in comments.</li>
          <li>When live AI is configured, your chat messages and selected lesson, circuit, or result context are sent to the configured AI provider. Otherwise, replies come from the built-in guide.</li>
          <li>If IBM Quantum access is enabled, approved circuit settings are sent to IBM when you submit a hardware job. Job status and results are stored by the workshop operator; terminal jobs are retained for seven days by default. Tracking details are kept in this browser to resume status checks.</li>
        </ul>
      </section>

      <div className="mt-8"><FeedbackForm /></div>

      <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:flex-wrap">
        <Link to="/learn" className="btn-primary">Start Learning</Link>
        <Link to="/playground" className="btn-secondary">Open Playground</Link>
      </div>
    </div>
  );
}
