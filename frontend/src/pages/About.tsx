import FeedbackForm from '../components/FeedbackForm';
import { Link } from 'react-router-dom';

export default function About() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">Workshop Guide</h1>
      <ol className="mt-6 space-y-4 text-slate-300">
        <li><strong>1. Join:</strong> If your facilitator shares a session code, enter it on the <Link to="/progress" className="text-cyan-300 underline">Progress</Link> page with a nickname.</li>
        <li><strong>2. Learn:</strong> Follow 14 lessons from qubits to oracle algorithms, Fourier transforms, teleportation, error correction, and variational methods.</li>
        <li><strong>3. Experiment:</strong> Choose one of 11 guided circuits, inspect its gates, and open the related theory lesson.</li>
        <li><strong>4. Simulate:</strong> Run on Qiskit Aer with preset noise or a real-device noise model, measure in the X, Y, or Z basis, and check whether differences exceed sampling noise.</li>
        <li><strong>5. Build:</strong> Place gates on up to five qubits, watch the Bloch spheres update, solve build challenges, and export Qiskit or OpenQASM.</li>
        <li><strong>6. Explore labs:</strong> Violate a Bell inequality with the CHSH test, then watch a variational optimizer find a ground-state energy.</li>
        <li><strong>7. Hardware:</strong> If enabled, submit an approved guided circuit to IBM Quantum and follow it on the hardware jobs page.</li>
        <li><strong>8. Understand:</strong> Ask the workshop assistant for an explanation, hint, or quiz. Live AI is optional.</li>
        <li><strong>9. Reflect:</strong> Review your badges, export your progress, and submit optional anonymous feedback.</li>
      </ol>

      <section className="glass mt-8 p-5 sm:p-6" aria-labelledby="data-use-heading">
        <h2 id="data-use-heading" className="text-xl font-semibold">Data and privacy</h2>
        <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-relaxed text-slate-300">
          <li>You can use the workshop without an account. Lesson, challenge, and practice progress stays in this browser unless you export it or join a session.</li>
          <li>If you join a workshop session, your nickname, completed lessons and challenges, and practice score are shared with the facilitator. Session data expires automatically, after three days by default.</li>
          <li>Optional feedback ratings, completion status, comments, submission time, and any joined session code are stored by the workshop operator, who sets how long feedback is kept. Avoid personal or sensitive information in comments.</li>
          <li>When live AI is configured, your chat messages, written practice answers you submit, and selected lesson, circuit, or result context are sent to the configured AI provider. Otherwise, replies come from the built-in guide.</li>
          <li>If IBM Quantum access is enabled, approved circuit settings are sent to IBM when you submit a hardware job. Job status and results are stored by the workshop operator; terminal jobs are retained for seven days by default. Tracking details are kept in this browser to resume status checks.</li>
          <li>Opened lessons and the app itself are cached on this device so they work offline.</li>
        </ul>
      </section>

      <div className="mt-8"><FeedbackForm /></div>

      <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:flex-wrap">
        <Link to="/learn" className="btn-primary">Start Learning</Link>
        <Link to="/playground" className="btn-secondary">Open Playground</Link>
        <Link to="/facilitator" className="btn-secondary">Facilitator dashboard</Link>
      </div>
    </div>
  );
}
