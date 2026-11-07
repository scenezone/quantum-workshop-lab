import { Atom, Award, Bot, BookOpen, CircuitBoard, FlaskConical, Info, Menu, Microscope, Trophy, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useI18n } from '../i18n/context';
import type { MessageKey } from '../i18n/messages';

const links: { to: string; label: MessageKey; icon: typeof Atom }[] = [
  { to: '/learn', label: 'nav.learn', icon: BookOpen },
  { to: '/playground', label: 'nav.playground', icon: FlaskConical },
  { to: '/builder', label: 'nav.builder', icon: CircuitBoard },
  { to: '/labs', label: 'nav.labs', icon: Microscope },
  { to: '/challenges', label: 'nav.challenges', icon: Trophy },
  { to: '/assistant', label: 'nav.assistant', icon: Bot },
  { to: '/progress', label: 'nav.progress', icon: Award },
  { to: '/about', label: 'nav.guide', icon: Info },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  const { t, locale, setLocale, locales } = useI18n();

  useEffect(() => {
    if (!open) return;
    // Matches Tailwind's xl breakpoint, where the full link row is shown.
    const desktop = window.matchMedia('(min-width: 80rem)');
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
      <nav className="mx-auto max-w-7xl px-4 py-4 sm:px-6" aria-label={t('nav.main')}>
        <div className="flex items-center justify-between gap-3">
          <Link to="/" onClick={() => setOpen(false)} className="flex min-w-0 items-center gap-2 text-sm font-bold sm:text-base">
            <Atom className="h-6 w-6 shrink-0 text-cyan-400" /><span>{t('app.name')}</span>
          </Link>
          <button ref={toggle} type="button" className="btn-secondary h-11 w-11 shrink-0 p-2 xl:hidden" onClick={() => setOpen(!open)}
            aria-label={open ? t('nav.close') : t('nav.open')} aria-expanded={open} aria-controls="navigation-links">
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <div id="navigation-links" className={`${open ? 'flex' : 'hidden'} absolute left-0 right-0 top-full max-h-[calc(100dvh-5rem)] flex-col gap-1 overflow-y-auto border-b border-white/10 bg-navy-950 p-4 xl:static xl:flex xl:max-h-none xl:flex-row xl:items-center xl:overflow-visible xl:border-0 xl:bg-transparent xl:p-0`}>
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} onClick={() => setOpen(false)}
                className={({ isActive }) => `flex shrink-0 items-center gap-2 whitespace-nowrap rounded-lg px-3 py-3 text-sm xl:px-2.5 xl:py-2 ${isActive ? 'bg-white/10 text-cyan-300' : 'text-slate-300 hover:bg-white/5'}`}>
                <Icon className="h-4 w-4 shrink-0" />{t(label)}
              </NavLink>
            ))}
            {locales.length > 1 && <label className="flex items-center gap-2 px-3 py-2 text-sm text-slate-300">
              <span className="sr-only">{t('nav.language')}</span>
              <select className="input py-1" value={locale} onChange={(event) => setLocale(event.target.value)}>
                {locales.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
              </select>
            </label>}
          </div>
        </div>
      </nav>
    </header>
  );
}
