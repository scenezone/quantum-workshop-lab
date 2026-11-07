import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

class ResizeObserverMock implements ResizeObserver {
  constructor() {}

  observe() {}

  unobserve() {}

  disconnect() {}
}

globalThis.ResizeObserver = ResizeObserverMock;

afterEach(() => {
  cleanup();
  // The assistant keeps its conversation in session storage between page loads.
  sessionStorage.clear();
});
