import { render, screen, within } from '@testing-library/react';
import { expect, it } from 'vitest';
import Markdown from '../components/Markdown';

it('renders gate tables as semantic tables with a keyboard-accessible scroll region', () => {
  render(<Markdown>{[
    '### Gate walkthrough', '',
    '| Step | Gate | Purpose |',
    '| --- | --- | --- |',
    '| 1 | H | Prepare a superposition. |',
    '| 2 | CX | Entangle the two qubits. |',
    '', 'The outcomes are correlated.',
  ].join('\n')}</Markdown>);
  const region = screen.getByRole('region', { name: 'Scrollable table' });
  expect(region).toHaveAttribute('tabindex', '0');
  const table = within(region).getByRole('table');
  expect(within(table).getAllByRole('columnheader')).toHaveLength(3);
  expect(within(table).getAllByRole('row')).toHaveLength(3);
  expect(within(table).getByRole('cell', { name: 'Entangle the two qubits.' })).toBeInTheDocument();
  expect(screen.getByText('The outcomes are correlated.')).toBeInTheDocument();
});

it('keeps short line-based explanations readable and longer steps in separate list items', () => {
  const { container } = render(<Markdown>{[
    'A short explanation.', 'A second line with an important detail.', '',
    '### Step-by-step', '',
    '1. **Prepare:** Start from the zero state.',
    '2. **Transform:** Apply a Hadamard gate.', '',
    '### Key points', '', '- Measurement gives a classical outcome.', '- Repeat the circuit for more shots.',
  ].join('\n')}</Markdown>);
  expect(container.querySelector('p br')).not.toBeNull();
  expect(screen.getByRole('heading', { name: 'Step-by-step' })).toBeInTheDocument();
  expect(screen.getAllByRole('listitem')).toHaveLength(4);
  expect(container.querySelector('ol strong')).toHaveTextContent('Prepare:');
});

it('preserves complete long replies with display equations and independently scrollable code', () => {
  const explanation = 'A detailed paragraph about interference and relative phases.\n\n'.repeat(60);
  const { container } = render(<Markdown>{explanation + [
    '\\[\\frac{|0\\rangle+|1\\rangle}{\\sqrt{2}}\\]', '',
    '```python', 'qc.h(0); '.repeat(60), '```', '', '**Final result:** Both outcomes have equal ideal probability.',
  ].join('\n')}</Markdown>);
  expect(container.querySelectorAll('p').length).toBeGreaterThan(60);
  expect(container.querySelector('.katex-display .katex')).not.toBeNull();
  const code = screen.getByLabelText('Code example');
  expect(code).toHaveAttribute('tabindex', '0');
  expect(code).toHaveTextContent('qc.h(0); '.repeat(60).trim());
  expect(screen.getByText('Final result:')).toBeInTheDocument();
});

it('preserves code delimiters while rendering equations and escaped pipes in table cells', () => {
  const { container } = render(<Markdown>{[
    '| Symbol | Meaning |', '| --- | --- |',
    '| $\\alpha$ | Amplitude of the first state |',
    '| `\\(x\\)` | A literal code example |',
    '| a \\| b | Two alternatives |',
  ].join('\n')}</Markdown>);
  expect(container.querySelector('td .katex')).not.toBeNull();
  expect(container.querySelector('td code')).toHaveTextContent('\\(x\\)');
  expect(screen.getByText('a | b', { selector: 'td' })).toBeInTheDocument();
});
