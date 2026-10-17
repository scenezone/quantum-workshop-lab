import { Atom, Bot, BookOpen, FlaskConical, Info } from 'lucide-react';
import { Link, NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'Home', icon: Atom },
  { to: '/learn', label: 'Learn Quantum', icon: BookOpen },
  { to: '/playground', label: 'Playground', icon: FlaskConical },
  { to: '/assistant', label: 'AI Assistant', icon: Bot },
  { to: '/about', label: 'Workshop Guide', icon: Info },
];

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-navy-950/80 backdrop-blur">
      <nav className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2 font-bold">
          <Atom className="h-6 w-6 text-cyan-400" />
          <span>Quantum Workshop Lab</span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition ${
                  isActive
                    ? 'bg-white/10 text-cyan-300'
                    : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </div>

        <Link to="/playground" className="btn-primary hidden sm:inline-flex">
          Launch Playground
        </Link>
      </nav>
    </header>
  );
}