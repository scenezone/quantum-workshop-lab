import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import Navbar from '../components/Navbar';

let desktop: MediaQueryList;

beforeEach(() => {
  const events = new EventTarget();
  desktop = Object.assign(events, { matches: false, media: '(min-width: 64rem)' }) as MediaQueryList;
  vi.stubGlobal('matchMedia', vi.fn(() => desktop));
});

afterEach(() => vi.unstubAllGlobals());

function show() {
  render(<MemoryRouter><Navbar /></MemoryRouter>);
}

it('opens mobile navigation and closes it after choosing a page', async () => {
  show();
  const user = userEvent.setup();
  const toggle = screen.getByRole('button', { name: 'Open navigation' });
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await user.click(toggle);
  expect(toggle).toHaveAttribute('aria-expanded', 'true');
  await user.click(screen.getByRole('link', { name: 'Learn Quantum' }));
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
});

it('closes with Escape and returns keyboard focus to the toggle', async () => {
  show();
  const user = userEvent.setup();
  const toggle = screen.getByRole('button', { name: 'Open navigation' });
  await user.click(toggle);
  screen.getByRole('link', { name: 'Playground' }).focus();
  await user.keyboard('{Escape}');
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
  expect(toggle).toHaveFocus();
});

it('resets an open mobile menu when the viewport becomes desktop size', async () => {
  show();
  const toggle = screen.getByRole('button', { name: 'Open navigation' });
  await userEvent.setup().click(toggle);
  act(() => {
    Object.assign(desktop, { matches: true });
    desktop.dispatchEvent(new Event('change'));
  });
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
});
