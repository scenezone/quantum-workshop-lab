import { Atom, Bot, Cpu, LineChart, ShieldCheck, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';

const features = [
  {
    icon: Book,
    title: 'Beginner lessons',
    description: 'Learn qubits, superposition, entanglement, gates, and circuits.',
  },
  {
    icon: Zap,
    title: 'Safe experiments',
    description: 'Run predefined circuits—no Python coding or arbitrary code execution.',
  },
  {
    icon: Cpu,
    title: 'Real IBM hardware',
    description: 'Submit approved circuits to IBM Quantum when enabled and available.',
  },
  {
    icon: LineChart,
    title: 'Interactive results',
    description: 'Compare ideal probabilities with actual measurement counts.',
  },
  {
    icon: Bot,
    title: 'AI assistant',
    description: 'Ask context-aware questions about your lessons and results.',
  },
  {
    icon: ShieldCheck,
    title: 'Workshop-ready',
    description: 'No accounts, conservative public quotas, and secure backend secrets.',
  },
];

function Book(props: { className?: string }) {
  return <Atom {...props} />;
}

export default function Home() {
  return (
    <div>
      <section className="quantum-gradient border-b border-white/10">
        <div className="mx-auto max-w-7xl px-4 py-20 text-center sm:px-6">
          <p className="mx-auto mb-4 w-fit rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-widest text-cyan-300">
            Quantum Workshop Lab
          </p>
          <h1 className="mx-auto max-w-4xl text-4xl font-black leading-tight sm:text-6xl">
            Explore Quantum Computing
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-300">
            Understand quantum computing through interactive lessons, run real quantum circuits, and
            explore results with your personal AI quantum assistant.
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link to="/learn" className="btn-primary">Start Learning</Link>
            <Link to="/playground" className="btn-secondary">Launch Playground</Link>
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