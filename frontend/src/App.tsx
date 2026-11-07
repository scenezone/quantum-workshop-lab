import { lazy, Suspense, useEffect } from 'react';
import { Link, Route, Routes } from 'react-router-dom';
import AppStatusBanner from './components/AppStatusBanner';
import Footer from './components/Footer';
import LoadingSkeleton from './components/LoadingSkeleton';
import Navbar from './components/Navbar';
import { useI18n } from './i18n/context';
import Home from './pages/Home';
import { startSessionSync } from './services/session';

const About = lazy(() => import('./pages/About'));
const Assistant = lazy(() => import('./pages/Assistant'));
const Learn = lazy(() => import('./pages/Learn'));
const Playground = lazy(() => import('./pages/Playground'));
const CircuitBuilder = lazy(() => import('./pages/CircuitBuilder'));
const Challenges = lazy(() => import('./pages/Challenges'));
const Labs = lazy(() => import('./pages/Labs'));
const Progress = lazy(() => import('./pages/Progress'));
const Facilitator = lazy(() => import('./pages/Facilitator'));
const Jobs = lazy(() => import('./pages/Jobs'));

function NotFound() {
  const { t } = useI18n();
  return (
    <section className="mx-auto flex min-h-[55vh] max-w-3xl flex-col items-center justify-center px-6 py-16 text-center">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">{t('notFound.eyebrow')}</p>
      <h1 className="mt-4 text-3xl font-bold text-slate-100 sm:text-4xl">{t('notFound.title')}</h1>
      <p className="mt-3 max-w-xl text-slate-300">{t('notFound.body')}</p>
      <Link to="/" className="btn-primary mt-7">{t('notFound.home')}</Link>
    </section>
  );
}

export default function App() {
  // Shares progress with a joined workshop session whenever it changes.
  useEffect(() => startSessionSync(), []);
  return (
    <div className="flex min-h-screen min-w-0 flex-col">
      <Navbar />
      <AppStatusBanner />
      <main className="min-w-0 flex-1">
        <Suspense fallback={<LoadingSkeleton className="m-6 h-64" />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/learn" element={<Learn />} />
            <Route path="/playground" element={<Playground />} />
            <Route path="/builder" element={<CircuitBuilder />} />
            <Route path="/labs" element={<Labs />} />
            <Route path="/challenges" element={<Challenges />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/progress" element={<Progress />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/facilitator" element={<Facilitator />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
