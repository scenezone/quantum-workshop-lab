import { Atom, Bot, BookOpen, FlaskConical, Info, Menu, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'Home', icon: Atom },
  { to: '/learn', label: 'Learn Quantum', icon: BookOpen },
  { to: '/playground', label: 'Playground', icon: FlaskConical },
  { to: '/assistant', label: 'AI Assistant', icon: Bot },
  { to: '/about', label: 'Workshop Guide', icon: Info },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const desktop = window.matchMedia('(min-width: 64rem)');
    function closeOnDesktop() {
      if (desktop.matches) setOpen(false);
    }
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpen(false);
        toggle.current?.focus();
      }
    }
    desktop.addEventListener('change', closeOnDesktop);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      desktop.removeEventListener('change', closeOnDesktop);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open]);

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-navy-950/80 backdrop-blur">
      <nav className="mx-auto max-w-7xl px-4 py-4 sm:px-6" aria-label="Main navigation">
        <div className="flex items-center justify-between gap-3">
          <Link to="/" onClick={() => setOpen(false)} className="flex min-w-0 items-center gap-2 text-sm font-bold sm:text-base">
            <Atom className="h-6 w-6 shrink-0 text-cyan-400" /><span>Quantum Workshop Lab</span>
          </Link>
          <button ref={toggle} type="button" className="btn-secondary h-11 w-11 shrink-0 p-2 lg:hidden" onClick={() => setOpen(!open)}
            aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} aria-controls="navigation-links">
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <div id="navigation-links" className={`${open ? 'flex' : 'hidden'} absolute left-0 right-0 top-full max-h-[calc(100dvh-5rem)] flex-col gap-1 overflow-y-auto border-b border-white/10 bg-navy-950 p-4 lg:static lg:flex lg:max-h-none lg:flex-row lg:overflow-visible lg:border-0 lg:bg-transparent lg:p-0`}>
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} onClick={() => setOpen(false)}
                className={({ isActive }) => `flex shrink-0 items-center gap-2 whitespace-nowrap rounded-lg px-3 py-3 text-sm lg:py-2 ${isActive ? 'bg-white/10 text-cyan-300' : 'text-slate-300 hover:bg-white/5'}`}>
                <Icon className="h-4 w-4 shrink-0" />{label}
              </NavLink>
            ))}
          </div>
        </div>
      </nav>
    </header>
  );
}
