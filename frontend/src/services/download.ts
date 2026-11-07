import type { ExperimentResult } from '../types/api';

export function downloadText(filename: string, content: string, type: string) {
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([content], { type }));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

export function csv(rows: (string | number | boolean | null | undefined)[][]): string {
  return rows.map((row) => row.map((cell) => {
    let text = String(cell ?? '');
    // Prevent spreadsheet applications from evaluating cells as formulas.
    if (/^[=+\-@]/.test(text) && !/^-?\d/.test(text)) text = `'${text}`;
    return `"${text.replace(/"/g, '""')}"`;
  }).join(',')).join('\n');
}

export function downloadResultCsv(result: ExperimentResult, filename = `${result.experiment_id}-results.csv`) {
  const outcomes = [...new Set([...Object.keys(result.counts), ...Object.keys(result.ideal_probabilities)])].sort();
  downloadText(filename, csv([
    ['outcome', 'count', 'observed_probability', 'ideal_probability'],
    ...outcomes.map((outcome) => [outcome, result.counts[outcome] ?? 0,
      result.observed_probabilities[outcome] ?? 0, result.ideal_probabilities[outcome] ?? 0]),
  ]), 'text/csv;charset=utf-8');
}
