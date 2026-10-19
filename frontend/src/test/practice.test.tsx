import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import LessonPractice from '../components/LessonPractice';
import { checkPracticeAnswer } from '../services/api';
import type { PracticeFeedback, PracticeQuestion } from '../types/api';

vi.mock('../services/api', () => ({ checkPracticeAnswer: vi.fn() }));

const questions: PracticeQuestion[] = [
  { question_id: 'superposition-mcq-1', kind: 'multiple_choice', prompt: 'Which gate prepares equal superposition from zero?',
    options: [{ option_id: 'a', text: 'X gate' }, { option_id: 'b', text: 'H gate' }] },
  { question_id: 'superposition-mcq-2', kind: 'multiple_choice', prompt: 'What do two H gates do?',
    options: [{ option_id: 'a', text: 'Return the initial state' }, { option_id: 'b', text: 'Always produce one' }] },
  { question_id: 'superposition-written-1', kind: 'short_answer', prompt: 'Explain why H is not a random coin flip.', options: [] },
];
const correct: PracticeFeedback = { question_id: questions[0].question_id, kind: 'multiple_choice',
  correct: true, correct_option_id: 'b', explanation: 'Hadamard creates equal amplitude magnitudes.' };

beforeEach(() => vi.resetAllMocks());

function show() {
  return render(<LessonPractice key="superposition" lessonId="superposition" questions={questions} />);
}

function firstQuestion() {
  return within(screen.getByRole('form', { name: /Which gate prepares/ }));
}

it('requires a selection and keeps answers hidden until the learner checks', async () => {
  vi.mocked(checkPracticeAnswer).mockResolvedValue(correct);
  show();
  const user = userEvent.setup();
  const card = firstQuestion();
  const check = card.getByRole('button', { name: 'Check answer' });
  expect(check).toBeDisabled();
  expect(screen.queryByText('Correct option')).not.toBeInTheDocument();
  expect(screen.queryByText(correct.explanation)).not.toBeInTheDocument();
  await user.click(card.getByRole('radio', { name: 'H gate' }));
  expect(check).toBeEnabled();
  expect(checkPracticeAnswer).not.toHaveBeenCalled();
  await user.click(check);
  expect(await card.findByText('Correct!')).toBeInTheDocument();
  expect(card.getByText('Correct option')).toBeInTheDocument();
  expect(card.getByText(correct.explanation)).toBeInTheDocument();
  expect(checkPracticeAnswer).toHaveBeenCalledWith('superposition', {
    question_id: questions[0].question_id, option_id: 'b',
  }, expect.any(AbortSignal));
  expect(screen.getByText('1 of 2 correct · 1 checked')).toBeInTheDocument();
});

it('explains an incorrect choice and allows a fresh attempt', async () => {
  vi.mocked(checkPracticeAnswer).mockResolvedValueOnce({ ...correct, correct: false }).mockResolvedValueOnce(correct);
  show();
  const user = userEvent.setup();
  const card = firstQuestion();
  await user.click(card.getByRole('radio', { name: 'X gate' }));
  await user.click(card.getByRole('button', { name: 'Check answer' }));
  expect(await card.findByText(/Not quite/)).toBeInTheDocument();
  expect(card.getByText('Your selection')).toBeInTheDocument();
  expect(screen.getByText('0 of 2 correct · 1 checked')).toBeInTheDocument();
  await user.click(card.getByRole('button', { name: 'Try again' }));
  expect(card.queryByText('Correct option')).not.toBeInTheDocument();
  expect(card.getByRole('radio', { name: 'X gate' })).not.toBeChecked();
  expect(card.getByRole('button', { name: 'Check answer' })).toBeDisabled();
  await user.click(card.getByRole('radio', { name: 'H gate' }));
  await user.click(card.getByRole('button', { name: 'Check answer' }));
  expect(await card.findByText('Correct!')).toBeInTheDocument();
  expect(screen.getByText('1 of 2 correct · 1 checked')).toBeInTheDocument();
});

it('clears previous feedback when a learner changes an already checked option', async () => {
  vi.mocked(checkPracticeAnswer).mockResolvedValue(correct);
  show();
  const user = userEvent.setup();
  const card = firstQuestion();
  await user.click(card.getByRole('radio', { name: 'H gate' }));
  await user.click(card.getByRole('button', { name: 'Check answer' }));
  await card.findByText('Correct!');
  await user.click(card.getByRole('radio', { name: /X gate/ }));
  expect(card.queryByText('Correct!')).not.toBeInTheDocument();
  expect(screen.getByText('0 of 2 correct · 0 checked')).toBeInTheDocument();
  expect(card.getByRole('button', { name: 'Check answer' })).toBeEnabled();
});

it('requires a written attempt before revealing a sample and self-review points', async () => {
  vi.mocked(checkPracticeAnswer).mockResolvedValue({ question_id: questions[2].question_id, kind: 'short_answer',
    sample_answer: 'H acts coherently on amplitudes and H squared is identity.',
    key_points: ['Coherent amplitudes', 'Interference', 'Reversible operation'],
  });
  show();
  const user = userEvent.setup();
  const card = within(screen.getByRole('form', { name: /Explain why H/ }));
  const compare = card.getByRole('button', { name: 'Compare with sample answer' });
  expect(compare).toBeDisabled();
  expect(card.queryByText('Sample answer')).not.toBeInTheDocument();
  await user.type(card.getByRole('textbox', { name: 'Your answer' }), '   ');
  expect(compare).toBeDisabled();
  await user.type(card.getByRole('textbox'), 'It transforms amplitudes reversibly.');
  await user.click(compare);
  expect(await card.findByText('Sample answer')).toBeInTheDocument();
  expect(card.getByText('Coherent amplitudes')).toBeInTheDocument();
  expect(card.getByText(/not automatically graded/)).toBeInTheDocument();
  expect(card.getByRole('textbox')).toHaveValue('   It transforms amplitudes reversibly.');
  expect(screen.getByText('0 of 2 correct · 0 checked')).toBeInTheDocument();
});

it('retains the selected option after a network error and can retry', async () => {
  vi.mocked(checkPracticeAnswer).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(correct);
  show();
  const user = userEvent.setup();
  const card = firstQuestion();
  await user.click(card.getByRole('radio', { name: 'H gate' }));
  await user.click(card.getByRole('button', { name: 'Check answer' }));
  expect(await card.findByRole('alert')).toHaveTextContent('could not be checked');
  expect(card.getByRole('radio', { name: 'H gate' })).toBeChecked();
  await user.click(card.getByRole('button', { name: 'Check answer' }));
  expect(await card.findByText('Correct!')).toBeInTheDocument();
  expect(checkPracticeAnswer).toHaveBeenCalledTimes(2);
});

it('prevents duplicate checks and aborts a pending request when leaving the lesson', async () => {
  let finish!: (result: PracticeFeedback) => void;
  vi.mocked(checkPracticeAnswer).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const { unmount } = show();
  const user = userEvent.setup();
  const card = firstQuestion();
  await user.click(card.getByRole('radio', { name: 'H gate' }));
  await user.dblClick(card.getByRole('button', { name: 'Check answer' }));
  expect(checkPracticeAnswer).toHaveBeenCalledTimes(1);
  expect(card.getByRole('radio', { name: 'H gate' })).toBeDisabled();
  const signal = vi.mocked(checkPracticeAnswer).mock.calls[0][2];
  unmount();
  expect(signal?.aborted).toBe(true);
  await act(async () => finish(correct));
});

it('resets attempts and scores when the selected lesson changes', async () => {
  vi.mocked(checkPracticeAnswer).mockResolvedValue(correct);
  const { rerender } = show();
  const user = userEvent.setup();
  const card = firstQuestion();
  await user.click(card.getByRole('radio', { name: 'H gate' }));
  await user.click(card.getByRole('button', { name: 'Check answer' }));
  await card.findByText('Correct!');
  rerender(<LessonPractice key="gates" lessonId="gates" questions={questions.map(question => ({ ...question, question_id: question.question_id.replace('superposition', 'gates') }))} />);
  await waitFor(() => expect(screen.getByText('0 of 2 correct · 0 checked')).toBeInTheDocument());
  expect(firstQuestion().getByRole('radio', { name: 'H gate' })).not.toBeChecked();
  expect(screen.queryByText('Correct!')).not.toBeInTheDocument();
});
