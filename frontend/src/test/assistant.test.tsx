import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import AIChatPanel from '../components/AIChatPanel';
import Markdown from '../components/Markdown';
import { AssistantProvider } from '../context/AssistantContext';
import { sendAssistantMessage } from '../services/api';

vi.mock('../services/api', () => ({ sendAssistantMessage: vi.fn() }));

beforeEach(() => vi.resetAllMocks());

function show() {
  return render(<AssistantProvider><AIChatPanel /></AssistantProvider>);
}

it('sends a question and distinguishes an AI answer from the guide', async () => {
  vi.mocked(sendAssistantMessage).mockResolvedValue({ reply: 'A qubit can be in superposition.', source: 'llm' });
  show();
  await userEvent.setup().click(screen.getByRole('button', { name: 'What is a qubit?' }));
  expect(await screen.findByText('AI answer')).toBeInTheDocument();
  expect(screen.getByText('A qubit can be in superposition.')).toBeInTheDocument();
  expect(sendAssistantMessage).toHaveBeenCalledTimes(1);
});

it('shows an explicit offline notice for a workshop guide reply', async () => {
  vi.mocked(sendAssistantMessage).mockResolvedValue({
    reply: 'H creates equal probabilities.', source: 'fallback', notice: 'Live AI is currently unavailable.',
  });
  show();
  await userEvent.setup().click(screen.getByRole('button', { name: 'What is a qubit?' }));
  expect(await screen.findByText('Workshop guide (offline)')).toBeInTheDocument();
  expect(screen.getByText('Live AI is currently unavailable.')).toBeInTheDocument();
});

it('retries without inserting the user question twice', async () => {
  vi.mocked(sendAssistantMessage).mockRejectedValueOnce(new Error('offline'))
    .mockResolvedValueOnce({ reply: 'A Hadamard gate creates superposition.', source: 'llm' });
  show();
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: 'What does the Hadamard gate do?' }));
  expect(await screen.findByRole('alert')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Retry message' }));
  expect(await screen.findByText('A Hadamard gate creates superposition.')).toBeInTheDocument();
  expect(screen.getByRole('log')).toHaveTextContent('What does the Hadamard gate do?');
  expect(sendAssistantMessage).toHaveBeenCalledTimes(2);
  expect(vi.mocked(sendAssistantMessage).mock.calls[1][0]).toHaveLength(1);
});

it('keeps one in-flight request when the chat panel remounts on another page', async () => {
  let finish!: (value: { reply: string; source: 'llm' }) => void;
  vi.mocked(sendAssistantMessage).mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  const { rerender } = show();
  await userEvent.setup().click(screen.getByRole('button', { name: 'What is a qubit?' }));
  rerender(<AssistantProvider><AIChatPanel key="another-page" /></AssistantProvider>);
  expect(screen.getByRole('status')).toHaveTextContent('Thinking');
  expect(screen.getByRole('button', { name: 'What is a qubit?' })).toBeDisabled();
  await act(async () => finish({ reply: 'A qubit is a quantum bit.', source: 'llm' }));
  expect(await screen.findByText('A qubit is a quantum bit.')).toBeInTheDocument();
  expect(sendAssistantMessage).toHaveBeenCalledTimes(1);
});

it('clearing a conversation aborts a request and ignores a late response', async () => {
  let finish!: (value: { reply: string; source: 'llm' }) => void;
  vi.mocked(sendAssistantMessage).mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  show();
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: 'What is a qubit?' }));
  const signal = vi.mocked(sendAssistantMessage).mock.calls[0][4];
  await user.click(screen.getByRole('button', { name: 'Cancel and clear chat' }));
  expect(signal?.aborted).toBe(true);
  await act(async () => finish({ reply: 'Old response', source: 'llm' }));
  await waitFor(() => expect(screen.queryByText('Old response')).not.toBeInTheDocument());
  expect(screen.queryByRole('status')).not.toBeInTheDocument();
});

it('renders LaTeX delimiters from AI answers without changing inline code', () => {
  const { container } = render(<Markdown>{'State: \\(\\frac{1}{2}\\). Code: `\\(x\\)`'}</Markdown>);
  expect(container.querySelector('.katex')).not.toBeNull();
  expect(container.querySelector('code')).toHaveTextContent('\\(x\\)');
});
