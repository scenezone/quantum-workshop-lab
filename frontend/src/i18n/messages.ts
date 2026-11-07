/**
 * Interface text for the app shell. To add a language, copy `en`, translate the values,
 * and register it in `LOCALES`. Missing keys fall back to English.
 */
export const en = {
  'app.name': 'Quantum Workshop Lab',
  'nav.main': 'Main navigation',
  'nav.open': 'Open navigation',
  'nav.close': 'Close navigation',
  'nav.learn': 'Learn Quantum',
  'nav.playground': 'Playground',
  'nav.builder': 'Build Circuit',
  'nav.labs': 'Labs',
  'nav.challenges': 'Challenges',
  'nav.assistant': 'AI Assistant',
  'nav.progress': 'Progress',
  'nav.guide': 'Workshop Guide',
  'nav.language': 'Language',
  'footer.tagline': 'Quantum Workshop Lab: learn by running real quantum circuits.',
  'footer.learn': 'Learn',
  'footer.playground': 'Playground',
  'footer.jobs': 'Hardware jobs',
  'footer.facilitator': 'Facilitators',
  'footer.guide': 'Guide',
  'offline.notice': 'You are offline. Lessons you have opened stay available; simulations need a connection.',
  'update.ready': 'A new version of the workshop is available.',
  'update.reload': 'Reload',
  'notFound.eyebrow': '404 · Page not found',
  'notFound.title': 'This page is outside the lab.',
  'notFound.body': 'The address may be out of date, or the page may have moved.',
  'notFound.home': 'Return to the workshop',
  'home.eyebrow': 'Quantum Workshop Lab',
  'home.title': 'Explore Quantum Computing',
  'home.body': 'Learn quantum computing through guided lessons, build and simulate circuits in your browser, and compare your results with ideal quantum behavior and realistic device noise. Optional IBM Quantum access is available when the workshop is configured for hardware.',
  'home.start': 'Start Learning',
  'home.playground': 'Launch Playground',
  'home.builder': 'Build a Circuit',
  'home.join': 'Join a workshop session',
} as const;

export type MessageKey = keyof typeof en;
export type Messages = Partial<Record<MessageKey, string>>;

export const LOCALES: Record<string, { label: string; messages: Messages; dir?: 'ltr' | 'rtl' }> = {
  en: { label: 'English', messages: en },
};
