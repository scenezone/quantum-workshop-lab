import { Atom, Bot, Cpu, FlaskConical, LineChart, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import HardwareLabCallout from '../components/HardwareLabCallout';

const features = [
  {
    icon: Atom,
    title: 'Beginner to advanced',
    description: 'Learn amplitudes, quantum algorithms, teleportation, and error correction.',
  },
  {
    icon: FlaskConical,
    title: 'Safe experiments',
    description: 'Explore 11 guided circuits with no Python setup or arbitrary code execution.',
  },
  {
    icon: Cpu,
    title: 'Real IBM hardware',
    description: 'Run approved guided circuits on IBM hardware. Simulator mode stays labeled until the live flow is verified.',
  },
  {
    icon: LineChart,
    title: 'Visual quantum states',
    description: 'Step through each gate with Bloch sphere views, noise controls, and measured results.',
  },
  {
    icon: Bot,
    title: 'Workshop assistant',
    description: 'Ask context-aware questions. Live AI is optional; the built-in guide works without credentials.',
  },
  {
    icon: ShieldCheck,
    title: 'Build and share',
    description: 'Compose a small safe circuit, export Qiskit code, and share its setup.',
  },
];

export default function Home() {
  return (
    <div>
      <section className="quantum-gradient border-b border-white/10">
        <div className="mx-auto max-w-7xl px-4 py-20 text-center sm:px-6">
          <p className="mx-auto mb-4 w-fit rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-widest text-cyan-300">
            Quantum Workshop Lab
          </p>
          <h1 className="mx-auto max-w-4xl text-4xl font-black leading-tight sm:text-6xl">
            Run Quantum Experiments on Real Hardware
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-300">
            Start with an approved experiment, send it to an IBM quantum processor, and compare the measurements
            with the simulator. When live hardware is not verified or available, the page says so clearly.
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link to="/learn" className="btn-primary">Start Learning</Link>
            <Link to="/builder" className="btn-secondary">Build a Circuit</Link>
          </div>
          <div className="mx-auto mt-10 max-w-4xl text-left">
            <HardwareLabCallout
              title="Make a real hardware run the first experiment"
              description="Choose a guided circuit and run it on IBM hardware when access is available. Until the live flow is verified, Simulator stays the active mode."
            />
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, description }) => (
            <div key={title} className="glass p-6">
              <Icon className="h-6 w-6 text-cyan-400" />
              <h3 className="mt-4 text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-slate-300">{description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
