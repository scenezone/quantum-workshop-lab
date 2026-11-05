// frontend/src/components/Footer.tsx
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="border-t border-white/10 py-8">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 text-center text-sm text-slate-400 sm:flex-row sm:px-6 sm:text-left">
        <p>Quantum Workshop Lab — learn by running real quantum circuits.</p>
        <div className="flex shrink-0 flex-wrap justify-center gap-4">
          <Link to="/learn" className="hover:text-cyan-300">Learn</Link>
          <Link to="/playground" className="hover:text-cyan-300">Playground</Link>
          <Link to="/about" className="hover:text-cyan-300">Guide</Link>
        </div>
      </div>
    </footer>
  );
}
