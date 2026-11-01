import { lazy, Suspense } from 'react';
import { Route, Routes, Link } from 'react-router-dom';
import Footer from './components/Footer';
import Navbar from './components/Navbar';
import LoadingSkeleton from './components/LoadingSkeleton';
import Home from './pages/Home';

const About = lazy(() => import('./pages/About'));
const Assistant = lazy(() => import('./pages/Assistant'));
const Learn = lazy(() => import('./pages/Learn'));
const Playground = lazy(() => import('./pages/Playground'));
const CircuitBuilder = lazy(() => import('./pages/CircuitBuilder'));
const Challenges = lazy(() => import('./pages/Challenges'));

export default function App() {
  return (
    <div className="flex min-h-screen min-w-0 flex-col">
      <Navbar />
      <main className="min-w-0 flex-1">
        <Suspense fallback={<LoadingSkeleton className="m-6 h-64" />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/learn" element={<Learn />} />
            <Route path="/playground" element={<Playground />} />
            <Route path="/builder" element={<CircuitBuilder />} />
            <Route path="/challenges" element={<Challenges />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/about" element={<About />} />
            <Route
              path="*"
              element={
                <section className="mx-auto flex min-h-[55vh] max-w-3xl flex-col items-center justify-center px-6 py-16 text-center">
                  <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">404 · Page not found</p>
                  <h1 className="mt-4 text-3xl font-bold text-slate-100 sm:text-4xl">This page is outside the lab.</h1>
                  <p className="mt-3 max-w-xl text-slate-300">The address may be out of date, or the page may have moved.</p>
                  <Link to="/" className="btn-primary mt-7">Return to the workshop</Link>
                </section>
              }
            />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
