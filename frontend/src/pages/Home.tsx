import { Atom, Bot, Cpu, FlaskConical, LineChart, Microscope, ShieldCheck, Trophy, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useI18n } from '../i18n/context';

const features = [
  {
    icon: Atom,
    title: 'Beginner to advanced',
    description: '14 lessons from qubits to amplitudes, quantum algorithms, teleportation, error correction, and variational methods.',
  },
  {
    icon: FlaskConical,
    title: 'Safe experiments',
    description: 'Explore 11 guided circuits, measure them in the X, Y, or Z basis, and compare ideal and noisy runs.',
  },
  {
    icon: ShieldCheck,
    title: 'Visual circuit builder',
    description: 'Place gates on up to 5 qubits, watch every qubit on a Bloch sphere, and export Qiskit or OpenQASM.',
  },
  {
    icon: Trophy,
    title: 'Challenges and badges',
    description: 'Build target states such as Bell and GHZ states, graded on the server, and track your progress.',
  },
  {
    icon: Microscope,
    title: 'Bell test and VQE labs',
    description: 'Violate the CHSH inequality and watch a variational optimizer find a molecule’s ground energy.',
  },
  {
    icon: LineChart,
    title: 'Real-device noise',
    description: 'Simulate with calibration snapshots of IBM processors and see whether differences exceed sampling noise.',
  },
  {
    icon: Cpu,
    title: 'Real IBM hardware',
    description: 'Submit approved circuits to IBM Quantum when enabled, and compare device metrics across your jobs.',
  },
  {
    icon: Bot,
    title: 'Workshop assistant',
    description: 'Ask context-aware questions with streaming answers. The built-in guide works without credentials.',
  },
  {
    icon: Users,
    title: 'Run a workshop',
    description: 'Facilitators create a session code and watch participants’ progress and feedback live.',
  },
];

export default function Home() {
  const { t } = useI18n();
  return (
    <div>
      <section className="quantum-gradient border-b border-white/10">
        <div className="mx-auto max-w-7xl px-4 py-20 text-center sm:px-6">
          <p className="mx-auto mb-4 w-fit rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-widest text-cyan-300">
            {t('home.eyebrow')}
          </p>
          <h1 className="mx-auto max-w-4xl text-4xl font-black leading-tight sm:text-6xl">{t('home.title')}</h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-300">{t('home.body')}</p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link to="/learn" className="btn-primary">{t('home.start')}</Link>
            <Link to="/playground" className="btn-secondary">{t('home.playground')}</Link>
            <Link to="/builder" className="btn-secondary">{t('home.builder')}</Link>
          </div>
          <Link to="/progress" className="mt-6 inline-block text-sm text-cyan-200 underline">{t('home.join')}</Link>
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
