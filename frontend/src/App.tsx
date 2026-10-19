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
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<div className="p-10">Page not found. <Link to="/">Return home</Link></div>} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
