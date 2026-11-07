import { Link } from 'react-router-dom';
import { useI18n } from '../i18n/context';

export default function Footer() {
  const { t } = useI18n();
  return (
    <footer className="border-t border-white/10 py-8">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 text-center text-sm text-slate-400 sm:flex-row sm:px-6 sm:text-left">
        <p>{t('footer.tagline')}</p>
        <div className="flex shrink-0 flex-wrap justify-center gap-4">
          <Link to="/learn" className="hover:text-cyan-300">{t('footer.learn')}</Link>
          <Link to="/playground" className="hover:text-cyan-300">{t('footer.playground')}</Link>
          <Link to="/jobs" className="hover:text-cyan-300">{t('footer.jobs')}</Link>
          <Link to="/facilitator" className="hover:text-cyan-300">{t('footer.facilitator')}</Link>
          <Link to="/about" className="hover:text-cyan-300">{t('footer.guide')}</Link>
        </div>
      </div>
    </footer>
  );
}
